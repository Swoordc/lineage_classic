"""站桩奶妈：扫描队伍槽位颜色 → 治愈 / 喝红 / 回家 / 加BUFF"""

# ============================================================
# 配置
# ============================================================
THRESHOLD = 70                          # 治愈触发阈值百分比
HOME_THRESHOLD = 0                      # 回家阈值百分比（0=禁用，如 30 则 HP<30% 回家）
SKILL_CD = 1.0                          # 技能全局冷却（秒）

# BUFF: 空列表 = 禁用，否则按顺序给每个队友逐个释放
BUFF_KEYS = ["f9"]
BUFF_CYCLE = 1140                       # BUFF 周期（秒），默认 19 分钟

# 队伍槽位网格（游戏客户区坐标）
FIRST_ROW_X = 12
FIRST_ROW_Y = 797
COLUMN_SPACING = 103
ROW_SPACING = 45
COLS = 2
ROWS = 4

# 槽位检测
CHAR_COLOR = "5a1504"                   # 有角色
# ============================================================

import time

import win32gui
import pyautogui
from PIL import ImageGrab

from src.roles.base import BaseRole
from src.utils.hp_bar import hp_above, is_away, _hex


class StationaryHealerRole(BaseRole):
    _needs_memory: bool = False
    _needs_window_move: bool = True

    def __init__(self) -> None:
        super().__init__()
        self._client_left: int = 0
        self._client_top: int = 0
        self._skill_cd_end: float = 0

        # BUFF 状态机
        self._buff_col: int = 1       # 当前队友列（跳过 [0,0] 自己）
        self._buff_row: int = 0
        self._buff_skill: int = 0     # BUFF_KEYS 索引
        self._buff_active: bool = False
        self._next_buff_time: float = 0

    # ========== 生命周期 ==========

    def _setup_extra(self) -> bool:
        self._client_left, self._client_top = win32gui.ClientToScreen(self._hwnd, (0, 0))  # type: ignore[arg-type]

        self.keyboard.click("f8")  # type: ignore[union-attr]
        time.sleep(0.5)

        self._log.info(
            f"站桩奶妈启动 | 治愈阈值:{THRESHOLD}% | 回家阈值:{HOME_THRESHOLD}%"
            f" | BUFF:{BUFF_KEYS if BUFF_KEYS else '关'} | 周期:{BUFF_CYCLE // 60}分钟"
        )
        return True

    def _cleanup_extra(self) -> None:
        pass

    # ========== 主循环 ==========

    def _tick(self) -> None:
        now = time.time()
        img = ImageGrab.grab(bbox=(
            self._client_left,
            self._client_top,
            self._client_left + 1280,
            self._client_top + 960,
        ))

        # ---- 回家检测 ----
        if HOME_THRESHOLD > 0:
            if not hp_above(img, FIRST_ROW_X, FIRST_ROW_Y, HOME_THRESHOLD):
                self._log.warn(f"触发回家 (HP<{HOME_THRESHOLD}%)")
                self.keyboard.click("f12")  # type: ignore[union-attr]
                time.sleep(0.1)
                self.running = False
                img.close()
                return

        # ---- 喝红检测 ----
        if _hex(img, FIRST_ROW_X + 73, FIRST_ROW_Y) == "242222":
            self.keyboard.click("f11")  # type: ignore[union-attr]

        # ---- CD 中只检测回家/喝红 ----
        if now < self._skill_cd_end:
            img.close()
            return

        # ---- 治愈扫描（生命优先） ----
        done = self._heal_scan(img)
        if done:
            img.close()
            return

        # ---- BUFF 状态机 ----
        if not BUFF_KEYS:
            img.close()
            return

        if not self._buff_active and now < self._next_buff_time:
            img.close()
            return

        if not self._buff_active:
            self._buff_active = True

        self._buff_step(img)
        img.close()

    # ========== 治愈扫描 ==========

    def _heal_scan(self, img) -> bool:
        """遍历槽位治愈。空槽停扫，远离跳过，低血治愈一个后停止。
        返回 True 表示已执行了操作。"""
        stop = False
        for row in range(ROWS):
            if stop:
                break
            for col in range(COLS):
                x = FIRST_ROW_X + col * COLUMN_SPACING
                y = FIRST_ROW_Y + row * ROW_SPACING

                if _hex(img, x, y) != CHAR_COLOR:
                    stop = True
                    break

                if is_away(img, x, y):
                    continue

                if not hp_above(img, x, y, THRESHOLD):
                    self._heal(x + THRESHOLD, y)
                    return True

        return False

    # ========== BUFF 状态机 ==========

    def _buff_step(self, img) -> None:
        """一步：给当前队友放当前技能，推进状态"""
        x = FIRST_ROW_X + self._buff_col * COLUMN_SPACING
        y = FIRST_ROW_Y + self._buff_row * ROW_SPACING

        if _hex(img, x, y) != CHAR_COLOR:
            self._buff_skill = 0
            self._advance_teammate()
            return

        if is_away(img, x, y):
            self._buff_skill = 0
            self._advance_teammate()
            return

        skill = BUFF_KEYS[self._buff_skill]
        self.keyboard.click(skill)  # type: ignore[union-attr]
        time.sleep(0.05)
        pyautogui.moveTo(self._client_left + x + 20, self._client_top + y)
        time.sleep(0.05)
        self.keyboard.click_mouse()  # type: ignore[union-attr]
        self._skill_cd_end = time.time() + SKILL_CD

        self._buff_skill += 1
        if self._buff_skill >= len(BUFF_KEYS):
            self._buff_skill = 0
            self._advance_teammate()

    def _advance_teammate(self) -> None:
        self._buff_col += 1
        if self._buff_col >= COLS:
            self._buff_col = 0
            self._buff_row += 1

        if self._buff_row >= ROWS:
            self._buff_col, self._buff_row = 1, 0
            self._buff_active = False
            self._next_buff_time = time.time() + BUFF_CYCLE
            self._log.info(f"BUFF 轮完成 | 下一轮 {BUFF_CYCLE // 60}分钟后")

    # ========== 辅助 ==========

    def _heal(self, client_x: int, client_y: int) -> None:
        self.keyboard.click("f8")  # type: ignore[union-attr]
        time.sleep(0.05)
        pyautogui.moveTo(self._client_left + client_x, self._client_top + client_y)
        time.sleep(0.05)
        self.keyboard.click_mouse()  # type: ignore[union-attr]
        self._skill_cd_end = time.time() + SKILL_CD
