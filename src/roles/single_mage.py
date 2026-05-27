"""单端法师：监控自身血量，低于阈值时加血"""

import time

from src.config import SINGLE_MAGE_ACTIONS
from src.roles.base import BaseRole
from src.utils.window import set_window_size_and_position


class SingleMageRole(BaseRole):
    def __init__(self) -> None:
        super().__init__()
        self._last_heal_time: float = 0

    def _setup_extra(self) -> bool:
        # 调整窗口
        hwnd = self.game.hwnd  # type: ignore[union-attr]
        set_window_size_and_position(hwnd, 1280, 960, 0, 0)
        self._log.info("单端法师初始化完成")
        return True

    def _tick(self) -> None:
        action = SINGLE_MAGE_ACTIONS[0]  # 只有一个 Action
        now = time.time()

        if now - self._last_heal_time < action.cooldown:
            return

        hp = self.game.get_hp()  # type: ignore[union-attr]
        if hp is None:
            return

        self._log.debug(f"当前血量: {hp}")

        if hp < action.threshold and hp > 0:
            self._log.warn(f"触发自保治愈 (HP={hp})")
            self.keyboard.hold(action.key, action.hold)  # type: ignore[union-attr]
            self._last_heal_time = now
            time.sleep(1)

    def _cleanup_extra(self) -> None:
        pass
