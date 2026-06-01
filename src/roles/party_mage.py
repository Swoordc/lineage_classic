"""站桩奶妈：扫描队伍槽位颜色 → 低于阈值治愈 → 自己低血回家
对标 VBScript 大漠逻辑，用 PIL 截图 + Arduino 键鼠

用法: python main.py stationary-healer
"""

# ============================================================
# 配置（改这里就行）
# ============================================================
THRESHOLD = 65              # 血量阈值：65 / 70 / 75 / 80
SCAN_INTERVAL = 0.1         # 扫描间隔（秒）

# 队伍槽位网格（游戏客户区坐标，跟大漠一致）
FIRST_ROW_X = 12
FIRST_ROW_Y = 797
COLUMN_SPACING = 103
ROW_SPACING = 45
COLS = 2
ROWS = 4

# 颜色常量（PIL getpixel 返回 RGB，hex 直接比对）
CHAR_COLOR = "5a1504"       # 有角色时的 c1 颜色
GO_HOME_COLOR = "591302"    # [0,0] 名字处正常颜色，不是这个就回家
# 不同阈值对应的 HP 条目标颜色
HEAL_COLORS = {
    80: "530d02",
    75: "4f0e06",
    70: "5b1306",
    65: "551004",
}
# ============================================================

import time
import ctypes
from ctypes import wintypes

import win32gui, win32con
import pyautogui
from PIL import ImageGrab

from src.roles.base import BaseRole

user32 = ctypes.windll.user32


class StationaryHealerRole(BaseRole):
    """站桩奶妈 — 不移动，定时扫描队伍血条"""

    _needs_keyboard = True

    def __init__(self) -> None:
        super().__init__()
        self._hwnd: int | None = None
        self._client_left: int = 0
        self._client_top: int = 0
        self._heal_color: str = HEAL_COLORS[THRESHOLD]
        self._heal_count: int = 0
        self._home_used: bool = False

    # ========== 生命周期 ==========

    def _setup_extra(self) -> bool:
        from src.utils.window import find_game_window
        self._hwnd = find_game_window()
        if not self._hwnd:
            self._log.error("未找到游戏窗口")
            return False
        return True

    def _on_start(self) -> None:
        hwnd = self._hwnd
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.3)

        self._client_left, self._client_top = win32gui.ClientToScreen(hwnd, (0, 0))

        # 锁定鼠标范围到游戏窗口
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        rect = wintypes.RECT()
        rect.left, rect.top = left, top
        rect.right, rect.bottom = right, bottom
        user32.ClipCursor(ctypes.byref(rect))

        # 初始选中治愈术
        self.keyboard.click("f8")
        time.sleep(0.5)

        self._heal_count = 0
        self._home_used = False
        self._log.info(f"站桩奶妈启动 | 阈值:{THRESHOLD}% | 治愈色:{self._heal_color}")

    def _on_stop(self) -> None:
        user32.ClipCursor(None)
        self._log.info(f"已停止 | 治愈:{self._heal_count}次 | 回家:{self._home_used}")

    # ========== 主循环 ==========

    def _tick(self) -> None:
        # 截客户区
        img = ImageGrab.grab(bbox=(
            self._client_left,
            self._client_top,
            self._client_left + 1280,
            self._client_top + 960,
        ))

        for row in range(ROWS):
            for col in range(COLS):
                x = FIRST_ROW_X + col * COLUMN_SPACING
                y = FIRST_ROW_Y + row * ROW_SPACING

                # --- [0,0]：检查是否回家 ---
                if col == 0 and row == 0:
                    test_color = self._get_hex(img, x + 50, y)
                    if test_color != GO_HOME_COLOR:
                        self._log.warn("触发回家")
                        self.keyboard.click("f12")
                        time.sleep(0.1)
                        self._home_used = True
                        self.running = False
                        img.close()
                        return

                # --- 检测是否有角色 ---
                c1 = self._get_hex(img, x, y)
                if c1 != CHAR_COLOR:
                    img.close()
                    return  # 空槽位 → 退出，下一轮从 [0,0] 重来

                # --- 检查 HP 条颜色 ---
                cx = x + THRESHOLD
                c2 = self._get_hex(img, cx, y)

                if c2 != self._heal_color:
                    self._log.debug(f"[{col},{row}] HP低 c2={c2} → 治愈")
                    self._heal(cx, y)

        img.close()

    # ========== 辅助 ==========

    @staticmethod
    def _get_hex(img, client_x: int, client_y: int) -> str:
        pixel = img.getpixel((client_x, client_y))
        return f"{pixel[0]:02x}{pixel[1]:02x}{pixel[2]:02x}"

    def _heal(self, client_x: int, client_y: int) -> None:
        self.keyboard.click("f8")
        time.sleep(0.05)
        pyautogui.moveTo(self._client_left + client_x, self._client_top + client_y)
        time.sleep(0.05)
        self.keyboard.click_mouse()
        self._heal_count += 1

    def _cleanup_extra(self) -> None:
        try:
            user32.ClipCursor(None)
        except Exception:
            pass