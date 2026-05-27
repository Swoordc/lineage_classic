"""测试 Arduino 连接和按键"""
import time
from src.hardware.arduino import ArduinoKeyboard


def main():
    print("=" * 50)
    print("Arduino 连接测试")
    print("=" * 50)
    kb = ArduinoKeyboard()
    if not kb.connect():
        print("Arduino 连接失败")
        return
    print("\n测试 F8 长按 1.5 秒")
    input("按 Enter 开始...")
    time.sleep(3)
    kb.hold("f8", 1.5)
    time.sleep(3)
    kb.click_mouse()
    kb.close()
    print("\n测试完成！")


if __name__ == "__main__":
    main()
