"""测试 Arduino 连接和按键"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.arduino_keyboard import ArduinoKeyboard


def main():
    print("=" * 50)
    print("Arduino 连接测试")
    print("=" * 50)
    
    # 1. 连接 Arduino
    kb = ArduinoKeyboard()
    if not kb.connect():
        print("❌ Arduino 连接失败，请检查：")
        print("   1. Arduino 是否已连接电脑")
        print("   2. config.py 中的 ARDUINO_PORT 是否正确")
        print("   3. Arduino 是否已烧录固件")
        return
    
    print("\n测试按键...")
    
    # 4. 测试长按
    print("\n测试 F8 长按 1 秒")
    input("按 Enter 键开始...")
    # 切换到游戏窗口
    time.sleep(3)
    kb.hold("f8", 1.5)
    
    time.sleep(3)
    kb.press_mouse()
    time.sleep(0.1)
    kb.release_mouse()

    kb.close()
    print("\n测试完成！")


if __name__ == "__main__":
    main()