"""站桩奶妈：扫描队伍槽位颜色 → 低于阈值治愈 → 低血回家 → 团队加速"""

# ============================================================
# 配置
# ============================================================
THRESHOLD = 65              # 血量阈值：65 / 70 / 75 / 80
ENABLE_HOME = True          # 是否启用低血回家
ENABLE_BUFF = True          # 是否启用 19 分钟团队加速
SCAN_INTERVAL = 0.1         # 扫描间隔（秒）

# 队伍槽位网格（游戏客户区坐标）
FIRST_ROW_X = 12
FIRST_ROW_Y = 797
COLUMN_SPACING = 103
ROW_SPACING = 45
COLS = 2
ROWS = 4

# 颜色常量
CHAR_COLOR = "5a1504"       # 有角色
GO_HOME_COLOR = "591302"    # 名字处正常颜色，不是就回家
HEAL_COLORS = {
    80: "530d02",
    75: "4f0e06",
    70: "5b1306",
    65: "551004",
}
# ============================================================

import time

import win32gui
import pyautogui
from PIL import ImageGrab

from src.roles.base import BaseRole


class StationaryHealerRole(BaseRole):
    _needs_memory: bool = False

    def __init__(self) -> None:
        super().__init__()
        self._client_left: int = 0
        self._client_top: int = 0
        self._heal_color: str = HEAL_COLORS[THRESHOLD]
        self._heal_count: int = 0
        self._home_used: bool = False
        self._next_buff_time: float = 0

    # ========== 生命周期 ==========

    def _setup_extra(self) -> bool:
        self._client_left, self._client_top = win32gui.ClientToScreen(self._hwnd, (0, 0))  # type: ignore[arg-type]

        self.keyboard.click("f8")  # type: ignore[union-attr]
        time.sleep(0.5)

        self._heal_count = 0
        self._home_used = False
        self._log.info(f"站桩奶妈启动 | 阈值:{THRESHOLD}% | 回家:{'开' if ENABLE_HOME else '关'} | 加速:{'开' if ENABLE_BUFF else '关'}")
        return True

    def _cleanup_extra(self) -> None:
        self._log.info(f"已停止 | 治愈:{self._heal_count}次 | 回家:{self._home_used}")

    # ========== 主循环 ==========

    def _tick(self) -> None:
        now = time.time()
        img = ImageGrab.grab(bbox=(
            self._client_left,
            self._client_top,
            self._client_left + 1280,
            self._client_top + 960,
        ))

        # 回家检测
        if ENABLE_HOME:
            test_color = self._get_hex(img, FIRST_ROW_X + 50, FIRST_ROW_Y)
            if test_color != GO_HOME_COLOR:
                self._log.warn(f"触发回家 (颜色:{test_color})")
                self.keyboard.click("f12")  # type: ignore[union-attr]
                time.sleep(0.1)
                self._home_used = True
                self.running = False
                img.close()
                return

        # 团队加速
        if ENABLE_BUFF and now >= self._next_buff_time:
            self._buff_round(img)
            self._next_buff_time = time.time() + 1140
            img.close()
            return

        # 治愈扫描
        for row in range(ROWS):
            for col in range(COLS):
                x = FIRST_ROW_X + col * COLUMN_SPACING
                y = FIRST_ROW_Y + row * ROW_SPACING

                c1 = self._get_hex(img, x, y)
                if c1 != CHAR_COLOR:
                    img.close()
                    return

                cx = x + THRESHOLD
                c2 = self._get_hex(img, cx, y)

                if c2 != self._heal_color:
                    self._log.debug(f"[{col},{row}] HP低 c2={c2} → 治愈")
                    self._heal(cx, y)

        img.close()

    # ========== 团队加速 ==========

    def _buff_round(self, img) -> None:
        """F9 选技能 → 点队友，从第二个槽位开始"""
        count = 0
        for row in range(ROWS):
            for col in range(COLS):
                if row == 0 and col == 0:
                    continue
                x = FIRST_ROW_X + col * COLUMN_SPACING
                y = FIRST_ROW_Y + row * ROW_SPACING
                c1 = self._get_hex(img, x, y)
                if c1 != CHAR_COLOR:
                    return
                self.keyboard.click("f9")  # type: ignore[union-attr]
                time.sleep(0.05)
                pyautogui.moveTo(self._client_left + x + 20, self._client_top + y)
                time.sleep(0.05)
                self.keyboard.click_mouse()  # type: ignore[union-attr]
                count += 1
        self._log.info(f"团队加速完成 | {count}人 | 下一轮 19分钟后")

    # ========== 辅助 ==========

    @staticmethod
    def _get_hex(img, client_x: int, client_y: int) -> str:
        pixel = img.getpixel((client_x, client_y))
        return f"{pixel[0]:02x}{pixel[1]:02x}{pixel[2]:02x}"

    def _heal(self, client_x: int, client_y: int) -> None:
        self.keyboard.click("f8")  # type: ignore[union-attr]
        time.sleep(0.05)
        pyautogui.moveTo(self._client_left + client_x, self._client_top + client_y)
        time.sleep(0.05)
        self.keyboard.click_mouse()  # type: ignore[union-attr]
        self._heal_count += 1
