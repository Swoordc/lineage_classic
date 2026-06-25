"""站桩奶妈：扫描队伍槽位颜色 → 治愈 / 喝红 / 回家 / 加BUFF"""

# ============================================================
# 配置
# ============================================================
THRESHOLD = 70                          # 治愈触发阈值百分比
HOME_THRESHOLD = 0                      # 回家阈值百分比（0=禁用）
DRINK_THRESHOLD = 0                     # 喝红阈值百分比（0=禁用）
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
from src.utils.hp_bar import hp_above, is_away, count_grayish, _hex, AWAY_MIN


class StationaryHealerRole(BaseRole):
    _needs_memory: bool = False
    _needs_window_move: bool = True

    def __init__(self) -> None:
        super().__init__()
        self._client_left: int = 0
        self._client_top: int = 0
        self._skill_cd_end: float = 0

        # 治愈状态机
        self._heal_col: int = 0        # 扫描起点（含自己 [0,0]）
        self._heal_row: int = 0

        # BUFF 状态机
        self._buff_col: int = 1        # 当前队友列
        self._buff_row: int = 0
        self._buff_skill: int = 0      # BUFF_KEYS 索引
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

        # 扫描并打印队伍信息
        img = ImageGrab.grab(bbox=(
            self._client_left, self._client_top,
            self._client_left + 1280, self._client_top + 960,
        ))
        self._print_party_summary(img)
        img.close()
        return True

    def _print_party_summary(self, img) -> None:
        """启动时打印队伍各槽位信息"""
        count = 0
        for row in range(ROWS):
            for col in range(COLS):
                x = FIRST_ROW_X + col * COLUMN_SPACING
                y = FIRST_ROW_Y + row * ROW_SPACING

                c1 = _hex(img, x, y)
                has_char = c1 == CHAR_COLOR
                if has_char:
                    count += 1
                    gray, total = count_grayish(img, x, y)
                    away = f"远离 (灰色{gray}/{total})" if gray >= AWAY_MIN else "在身旁"
                    hp_ok = hp_above(img, x, y, THRESHOLD)
                    hp_str = f"HP{'≥' if hp_ok else '<'}{THRESHOLD}%"
                    self._log.info(f"  [{col},{row}] c1={c1} {away} {hp_str}")
                else:
                    self._log.info(f"  [{col},{row}] c1={c1} ≠ {CHAR_COLOR} 无角色")

        self._log.info(f"共 {count} 个角色")

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
        if DRINK_THRESHOLD > 0:
            if not hp_above(img, FIRST_ROW_X, FIRST_ROW_Y, DRINK_THRESHOLD):
                self.keyboard.click("f11")  # type: ignore[union-attr]

        # ---- CD 中只检测回家/喝红 ----
        if now < self._skill_cd_end:
            img.close()
            return

        # ---- 治愈扫描（生命优先） ----
        done = self._heal_tick(img)
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

    # ========== 治愈状态机 ==========

    def _heal_tick(self, img) -> bool:
        """从 (_heal_col, _heal_row) 开始找第一个需要治愈的。
        空槽归零，远离跳过，低血治愈后推进指针。
        返回 True 表示执行了治愈。"""
        col, row = self._heal_col, self._heal_row
        scanned = 0
        while scanned < 8:
            x = FIRST_ROW_X + col * COLUMN_SPACING
            y = FIRST_ROW_Y + row * ROW_SPACING

            if _hex(img, x, y) != CHAR_COLOR:
                self._heal_col, self._heal_row = 0, 0
                return False

            if not is_away(img, x, y) and not hp_above(img, x, y, THRESHOLD):
                self._heal(x + THRESHOLD, y)
                self._advance_heal_pointer(col, row)
                return True

            self._advance_heal_pointer(col, row)
            col, row = self._heal_col, self._heal_row
            scanned += 1

        return False

    def _advance_heal_pointer(self, col: int, row: int) -> None:
        col += 1
        if col >= COLS:
            col = 0
            row += 1
        if row >= ROWS:
            col, row = 0, 0
        self._heal_col, self._heal_row = col, row

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
