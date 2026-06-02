"""角色基类：统一生命周期、进程存活检测。
启动即运行，Ctrl+C 停止。不再使用 Home/End 热键。
"""

import time
from abc import ABC, abstractmethod

import win32con
import win32gui

from src.game.memory import GameMemory
from src.hardware.arduino import ArduinoKeyboard
from src.utils.logger import get_logger


class BaseRole(ABC):
    game: GameMemory | None
    keyboard: ArduinoKeyboard | None
    running: bool

    _needs_keyboard: bool = True
    _needs_memory: bool = True

    def __init__(self) -> None:
        self.game = None
        self.keyboard = None
        self.running = False
        self._hwnd: int | None = None
        self._log = get_logger()

    # ========== 子类实现 ==========

    @abstractmethod
    def _setup_extra(self) -> bool:
        """子类额外初始化，返回 True 表示成功"""
        ...

    @abstractmethod
    def _tick(self) -> None:
        """主循环每次迭代"""
        ...

    def _cleanup_extra(self) -> None:
        pass

    # ========== 公共生命周期 ==========

    def setup(self) -> bool:
        from src.utils.window import find_game_window

        hwnd = find_game_window()
        if not hwnd:
            self._log.error("未找到游戏窗口")
            return False
        self._hwnd = hwnd
        self._log.info(f"窗口句柄: {hwnd}")

        # 激活游戏窗口
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.3)

        if self._needs_memory:
            self.game = GameMemory(hwnd)
            if not self.game.connect():
                self._log.error("内存连接失败")
                return False

        if self._needs_keyboard:
            self.keyboard = ArduinoKeyboard()
            if not self.keyboard.connect():
                self._log.error("Arduino 连接失败")
                return False

        if not self._setup_extra():
            return False

        self.running = True
        self._log.info("初始化完成")
        return True

    def run(self) -> None:
        if not self.setup():
            return
        self._log.info("脚本已启动")

        try:
            while self.running:
                self._tick()

                if self.game is not None and not self.game.alive():
                    self._log.error("游戏可能已关闭，脚本退出")
                    break

                time.sleep(0.05)

        except KeyboardInterrupt:
            self._log.warn("用户中断")
        finally:
            self.cleanup()
        self._log.info("脚本已停止")

    def cleanup(self) -> None:
        self._cleanup_extra()
        if self.keyboard:
            self.keyboard.close()
        if self.game:
            self.game.close()
