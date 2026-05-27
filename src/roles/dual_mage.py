"""双端法师：接收打手血量 + 自保 + 救打手 + 跟随 + Buff"""

import ctypes
import ctypes.wintypes
import socket
import threading
import time

import pyautogui

from src.config import (
    ATTACKER_HEAL_THRESHOLD,
    BUFF_ENABLED,
    BUFF_HOLD_DURATION,
    BUFF_KEY_INTERVAL,
    BUFF_KEYS,
    DUAL_MAGE_ACTIONS,
    HOME,
    DRINK,
    SELF_HEAL,
    HEAL_OTHER,
    MAGE_BIND_PORT,
)
from src.roles.base import BaseRole

user32 = ctypes.windll.user32


class DualMageRole(BaseRole):
    def __init__(self) -> None:
        super().__init__()
        self._sock: socket.socket | None = None
        self._udp_thread: threading.Thread | None = None
        self._buff_thread: threading.Thread | None = None
        self._udp_running: bool = False
        self._attacker_hp: int = 1000
        self._hp_lock = threading.Lock()
        self._click_x: int = 0
        self._click_y: int = 0
        self._f8_pressed: bool = False
        self._heal_cooldown_end: float = 0
        self._potion_cooldown_end: float = 0
        self._last_summary: float = 0
        self._heal_count: int = 0
        self._potion_count: int = 0

    # ========== 鼠标锁定 ==========

    @staticmethod
    def _lock_mouse(x: int, y: int) -> None:
        rect = ctypes.wintypes.RECT()
        rect.left, rect.right = x, x + 1
        rect.top, rect.bottom = y, y + 1
        user32.ClipCursor(ctypes.byref(rect))
        pyautogui.moveTo(x, y)

    @staticmethod
    def _unlock_mouse() -> None:
        user32.ClipCursor(None)

    # ========== UDP 接收线程 ==========

    def _udp_receiver(self) -> None:
        while self._udp_running:
            try:
                data, _ = self._sock.recvfrom(1024)  # type: ignore[union-attr]
                hp = int(data.decode('utf-8'))
                with self._hp_lock:
                    self._attacker_hp = hp
            except socket.timeout:
                continue
            except Exception:
                continue

    # ========== Buff 线程 ==========

    def _buff_loop(self, cycle_interval: int = 1200) -> None:
        while self._udp_running:
            time.sleep(cycle_interval)
            for key in BUFF_KEYS:
                self.keyboard.hold(key, BUFF_HOLD_DURATION)  # type: ignore[union-attr]
                time.sleep(BUFF_KEY_INTERVAL)

    # ========== 生命周期 ==========

    def _setup_extra(self) -> bool:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind(('0.0.0.0', MAGE_BIND_PORT))
        self._sock.settimeout(0.5)
        self._log.info(f"UDP 端口已绑定: {MAGE_BIND_PORT}")

        self._udp_running = True
        self._udp_thread = threading.Thread(target=self._udp_receiver, daemon=True)
        self._udp_thread.start()

        if BUFF_ENABLED:
            self._buff_thread = threading.Thread(target=self._buff_loop, daemon=True)
            self._buff_thread.start()
            self._log.info("Buff 线程已启动")

        self._log.info("双端法师初始化完成")
        return True

    def _on_start(self) -> None:
        self._click_x, self._click_y = pyautogui.position()
        self._lock_mouse(self._click_x, self._click_y)
        self._last_summary = time.time()
        self._heal_count = 0
        self._potion_count = 0

    def _on_stop(self) -> None:
        if self._f8_pressed:
            self.keyboard.release("f8")  # type: ignore[union-attr]
            self._f8_pressed = False
        self._unlock_mouse()

    # ========== 主循环 ==========

    def _tick(self) -> None:
        now = time.time()
        hp = self.game.get_hp()  # type: ignore[union-attr]
        if hp is None:
            return

        self._log.debug(f"HP={hp}, 打手HP={self._attacker_hp}")

        # 自保治愈中：检查是否血量已恢复
        if self._f8_pressed and hp >= SELF_HEAL.threshold:
            self.keyboard.release("f8")  # type: ignore[union-attr]
            self._f8_pressed = False
            self._log.warn(f"自保治愈结束 (HP={hp})")

        # 按优先级遍历 Action：回家 > 红水 > 自保 > 救打手
        for action in DUAL_MAGE_ACTIONS:
            if not self._should_trigger(action, hp, now):
                continue

            self._execute(action, hp, now)

            # 回家后停止
            if action is HOME:
                self.running = False
            return  # 每轮只触发一个

        # 心跳摘要（每 30 秒）
        if now - self._last_summary >= 30:
            self._log.info(
                f"双法汇总 | HP:{hp} 打手HP:{self._attacker_hp} | "
                f"加血:{self._heal_count}次 红水:{self._potion_count}次"
            )
            self._last_summary = now

    def _should_trigger(self, action, hp: int, now: float) -> bool:
        """判断 Action 是否应触发"""
        if action is HEAL_OTHER:
            # 自保治愈中不救打手
            if self._f8_pressed:
                return False
            with self._hp_lock:
                current = self._attacker_hp
            threshold = ATTACKER_HEAL_THRESHOLD
        else:
            current = hp
            threshold = action.threshold

        if current >= threshold:
            return False

        # 冷却检查
        if action is DRINK:
            if now < self._potion_cooldown_end:
                return False
        elif action.cooldown > 0:
            if now < self._heal_cooldown_end:
                return False

        return True

    def _execute(self, action, hp: int, now: float) -> None:
        """执行一个 Action"""
        if action is HOME:
            if self._f8_pressed:
                self.keyboard.release("f8")  # type: ignore[union-attr]
                self._f8_pressed = False
            self._log.warn(f"血量过低 ({hp})，使用回家卷")
            self.keyboard.hold(action.key, action.hold)  # type: ignore[union-attr]

        elif action is DRINK:
            self.keyboard.click(action.key)  # type: ignore[union-attr]
            self._potion_cooldown_end = now + action.cooldown
            self._potion_count += 1
            self._log.warn(f"喝红水 (HP={hp})")

        elif action is SELF_HEAL:
            self.keyboard.press(action.key)  # type: ignore[union-attr]
            self._f8_pressed = True
            self._heal_cooldown_end = now + action.cooldown
            self._heal_count += 1
            self._log.warn(f"自保治愈开始 (HP={hp})")

        elif action is HEAL_OTHER:
            self.keyboard.hold(action.key, action.hold)  # type: ignore[union-attr]
            self._heal_cooldown_end = now + action.cooldown
            self._heal_count += 1
            self._log.warn(f"救打手 (打手HP={self._attacker_hp})")

    def _cleanup_extra(self) -> None:
        self._udp_running = False
        if self._f8_pressed:
            self.keyboard.release("f8")  # type: ignore[union-attr]
        self._unlock_mouse()
        if self._sock:
            self._sock.close()
        if self._udp_thread:
            self._udp_thread.join(timeout=1)
