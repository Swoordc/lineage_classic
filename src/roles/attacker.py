"""打手发送端：读取自身血量，通过 UDP 发送给法师"""

import socket
import time

from src.config import ATTACKER_IP, UDP_PORT, SEND_INTERVAL
from src.roles.base import BaseRole


class AttackerRole(BaseRole):
    _needs_keyboard: bool = False

    def __init__(self) -> None:
        super().__init__()
        self._sock: socket.socket | None = None
        self._send_count: int = 0
        self._last_summary: float = 0
        self._last_send: float = 0

    def _setup_extra(self) -> bool:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._log.info(f"UDP 发送目标: {ATTACKER_IP}:{UDP_PORT}")
        return True

    def _tick(self) -> None:
        now = time.time()
        if now - self._last_send < SEND_INTERVAL:
            return

        hp = self.game.get_hp()  # type: ignore[union-attr]
        if hp is None:
            self._log.warn(f"读取血量失败 (连续{self.game.error_count}次)")
            return
        if hp <= 0:
            return

        data = str(hp).encode('utf-8')
        self._sock.sendto(data, (ATTACKER_IP, UDP_PORT))  # type: ignore[union-attr]
        self._send_count += 1
        self._last_send = now

        # 心跳摘要（每 30 秒）
        now = time.time()
        if now - self._last_summary >= 30:
            self._log.info(
                f"打手汇总 | 发送次数: {self._send_count} | 当前血量: {hp}"
            )
            self._last_summary = now

        self._log.debug(f"发送血量: {hp}")

    def _cleanup_extra(self) -> None:
        if self._sock:
            self._sock.close()
