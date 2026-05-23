"""Arduino 键盘控制模块"""

import serial
import time
from src.config import ARDUINO_PORT, ARDUINO_BAUDRATE


class ArduinoKeyboard:
    """通过 Arduino 模拟键盘按键"""
    
    # F1-F12 键码
    KEY_CODES = {
        "f1": 0xC2,
        "f2": 0xC3,
        "f3": 0xC4,
        "f4": 0xC5,
        "f5": 0xC6,
        "f6": 0xC7,
        "f7": 0xC8,
        "f8": 0xC9,
        "f9": 0xCA,
        "f10": 0xCB,
        "f11": 0xCC,
        "f12": 0xCD,
    }
    
    def __init__(self):
        self.ser = None
    
    def connect(self):
        """连接 Arduino"""
        try:
            self.ser = serial.Serial(ARDUINO_PORT, ARDUINO_BAUDRATE, timeout=1)
            time.sleep(2)  # 等待 Arduino 复位
            print(f"✓ Arduino 已连接 ({ARDUINO_PORT})")
            return True
        except Exception as e:
            print(f"✗ Arduino 连接失败: {e}")
            return False
    
    def click(self, key):
        """点击按键"""
        key_lower = key.lower()
        if key_lower not in self.KEY_CODES:
            print(f"不支持的按键: {key}")
            return False
        
        key_code = self.KEY_CODES[key_lower]
        self.ser.write(bytes([ord('c'), key_code]))  # 改这里
        self.ser.flush()
        print(f"✓ 已按 {key.upper()}")
        return True

    def press(self, key):
        """只按下"""
        key_lower = key.lower()
        if key_lower not in self.KEY_CODES:
            return False
        
        key_code = self.KEY_CODES[key_lower]
        self.ser.write(bytes([ord('p'), key_code]))  # 改这里
        self.ser.flush()
        return True

    def release(self, key):
        """只释放"""
        key_lower = key.lower()
        if key_lower not in self.KEY_CODES:
            return False
        
        key_code = self.KEY_CODES[key_lower]
        self.ser.write(bytes([ord('r'), key_code]))  # 改这里
        self.ser.flush()
        return True
    
    def hold(self, key, duration):
        """按住一段时间"""
        self.press(key)
        time.sleep(duration)
        self.release(key)
        print(f"✓ 按住 {key.upper()} {duration} 秒")
    
    def close(self):
        """关闭串口"""
        if self.ser:
            self.ser.close()
            print("✓ Arduino 已断开")