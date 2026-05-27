"""Arduino HID 设备：键盘按键 + 鼠标点击"""

import time
from typing import ClassVar

import serial

from src.config import ARDUINO_PORT, ARDUINO_BAUDRATE
from src.utils.logger import get_logger

log = get_logger()


class ArduinoKeyboard:
    """通过 Arduino 模拟键盘按键和鼠标点击"""

    KEY_CODES: ClassVar[dict[str, int]] = {
        "f1": 0xC2, "f2": 0xC3, "f3": 0xC4, "f4": 0xC5,
        "f5": 0xC6, "f6": 0xC7, "f7": 0xC8, "f8": 0xC9,
        "f9": 0xCA, "f10": 0xCB, "f11": 0xCC, "f12": 0xCD,
    }

    def __init__(self) -> None:
        self.ser: serial.Serial | None = None

    def connect(self) -> bool:
        try:
            self.ser = serial.Serial(ARDUINO_PORT, ARDUINO_BAUDRATE, timeout=1)
            time.sleep(2)
            log.info(f"Arduino 已连接 ({ARDUINO_PORT})")
            return True
        except Exception as e:
            log.error(f"Arduino 连接失败: {e}")
            return False

    # ========== 键盘 ==========

    def click(self, key: str) -> bool:
        key_lower = key.lower()
        if key_lower not in self.KEY_CODES:
            log.error(f"不支持的按键: {key}")
            return False
        key_code = self.KEY_CODES[key_lower]
        self.ser.write(bytes([ord('c'), key_code]))  # type: ignore[union-attr]
        self.ser.flush()  # type: ignore[union-attr]
        return True

    def press(self, key: str) -> bool:
        key_lower = key.lower()
        if key_lower not in self.KEY_CODES:
            return False
        key_code = self.KEY_CODES[key_lower]
        self.ser.write(bytes([ord('p'), key_code]))  # type: ignore[union-attr]
        self.ser.flush()  # type: ignore[union-attr]
        return True

    def release(self, key: str) -> bool:
        key_lower = key.lower()
        if key_lower not in self.KEY_CODES:
            return False
        key_code = self.KEY_CODES[key_lower]
        self.ser.write(bytes([ord('r'), key_code]))  # type: ignore[union-attr]
        self.ser.flush()  # type: ignore[union-attr]
        return True

    def hold(self, key: str, duration: float) -> None:
        self.press(key)
        time.sleep(duration)
        self.release(key)

    # ========== 鼠标 ==========

    def click_mouse(self, duration: float = 0.1) -> None:
        if self.ser:
            self.press_mouse()
            time.sleep(duration)
            self.release_mouse()

    def press_mouse(self) -> None:
        if self.ser:
            self.ser.write(b'd')
            self.ser.flush()

    def release_mouse(self) -> None:
        if self.ser:
            self.ser.write(b'u')
            self.ser.flush()

    def close(self) -> None:
        if self.ser:
            self.ser.close()
            log.info("Arduino 已断开")
