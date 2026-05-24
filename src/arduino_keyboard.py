"""Arduino 键鼠控制模块（键盘 + 鼠标）"""

import serial
import time
from src.config import ARDUINO_PORT, ARDUINO_BAUDRATE


class ArduinoKeyboard:
    """通过 Arduino 模拟键盘按键和鼠标点击"""
    
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
    
    # ========== 键盘方法 ==========
    def click(self, key):
        """点击按键（按下并释放）"""
        key_lower = key.lower()
        if key_lower not in self.KEY_CODES:
            print(f"不支持的按键: {key}")
            return False
        
        key_code = self.KEY_CODES[key_lower]
        self.ser.write(bytes([ord('c'), key_code]))
        self.ser.flush()
        print(f"✓ 已按 {key.upper()}")
        return True

    def press(self, key):
        """只按下按键（按住不放）"""
        key_lower = key.lower()
        if key_lower not in self.KEY_CODES:
            return False
        
        key_code = self.KEY_CODES[key_lower]
        self.ser.write(bytes([ord('p'), key_code]))
        self.ser.flush()
        return True

    def release(self, key):
        """只释放按键"""
        key_lower = key.lower()
        if key_lower not in self.KEY_CODES:
            return False
        
        key_code = self.KEY_CODES[key_lower]
        self.ser.write(bytes([ord('r'), key_code]))
        self.ser.flush()
        return True
    
    def hold(self, key, duration):
        """按住按键一段时间"""
        self.press(key)
        time.sleep(duration)
        self.release(key)
        print(f"✓ 按住 {key.upper()} {duration} 秒")
    
    # ========== 鼠标方法 ==========
    def click_mouse(self, duration=0.1):
        #"""鼠标左键点击（按下并释放）"""
        # if self.ser:
        #     self.ser.write(b'm')   # 对应 Arduino 固件中的 'm' 命令
        #     self.ser.flush()
            # print("✓ 鼠标左键点击")  # 可选，避免刷屏
        """鼠标左键点击（按下、保持、释放），默认保持 0.1 秒"""
        if self.ser:
            self.press_mouse()          # 发送按下命令 'd'
            time.sleep(duration)        # 保持指定时间（毫秒级转秒）
            self.release_mouse()        # 发送释放命令 'u'
            # print("✓ 鼠标左键点击")   # 可选
        
    def press_mouse(self):
        """鼠标左键按下（按住不放）"""
        if self.ser:
            self.ser.write(b'd')   # 对应 Arduino 固件中的 'd' 命令（mouse down）
            self.ser.flush()
    
    def release_mouse(self):
        """鼠标左键释放"""
        if self.ser:
            self.ser.write(b'u')   # 对应 Arduino 固件中的 'u' 命令（mouse up）
            self.ser.flush()
    
    def close(self):
        """关闭串口"""
        if self.ser:
            self.ser.close()
            print("✓ Arduino 已断开")