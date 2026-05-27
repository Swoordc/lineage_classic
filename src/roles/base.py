"""角色基类：统一生命周期、热键、cleanup、进程存活检测"""

import time
from abc import ABC, abstractmethod

import keyboard

from src.game.memory import GameMemory
from src.hardware.arduino import ArduinoKeyboard
from src.utils.logger import get_logger


class BaseRole(ABC):
    game: GameMemory | None
    keyboard: ArduinoKeyboard | None
    running: bool

    def __init__(self) -> None:
        self.game = None
        self.keyboard = None
        self.running = False
        self._log = get_logger()

    # ========== 子类可覆盖 ==========

    _needs_keyboard: bool = True  # 是否需要 Arduino 键盘

    @abstractmethod
    def _setup_extra(self) -> bool:
        """子类额外初始化（UDP、线程等），返回 True 表示成功"""
        ...

    @abstractmethod
    def _tick(self) -> None:
        """主循环每次迭代的逻辑"""
        ...

    def _cleanup_extra(self) -> None:
        """子类额外清理"""
        pass

    def _on_start(self) -> None:
        """热键 Home：启动时回调"""
        pass

    def _on_stop(self) -> None:
        """热键 End：停止时回调"""
        pass

    # ========== 公共生命周期 ==========

    def setup(self) -> bool:
        """初始化：窗口 → 内存 → Arduino → 热键 → 子类扩展"""
        from src.utils.window import find_game_window

        hwnd = find_game_window()
        if not hwnd:
            self._log.error("未找到游戏窗口")
            return False
        self._log.info(f"窗口句柄: {hwnd}")

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

        keyboard.add_hotkey('home', self._do_start)
        keyboard.add_hotkey('end', self._do_stop)
        self._log.info("初始化完成")
        return True

    def _do_start(self) -> None:
        if self.running:
            return
        self.running = True
        self._on_start()
        self._log.warn("脚本已启动")

    def _do_stop(self) -> None:
        if not self.running:
            return
        self.running = False
        self._on_stop()
        self._log.warn("脚本已停止")

    def run(self) -> None:
        if not self.setup():
            return
        self._log.info("就绪... 按 Home 启动，End 停止")

        try:
            while True:
                if self.running:
                    self._tick()

                    # 进程存活检测
                    if self.game and not self.game.alive():
                        self._log.error("游戏可能已关闭，脚本退出")
                        self.running = False
                        break

                time.sleep(0.05)

        except KeyboardInterrupt:
            self._log.warn("用户中断")
        finally:
            self.cleanup()

    def cleanup(self) -> None:
        """统一释放顺序：子类扩展 → Arduino → 内存"""
        self._cleanup_extra()
        if self.keyboard:
            self.keyboard.close()
        if self.game:
            self.game.close()
        self._log.info("脚本已退出")
