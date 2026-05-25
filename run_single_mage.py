"""单端法师脚本：运行即监控自身血量，低于阈值时按 F8 加血，并自动设置窗口分辨率与位置"""

import sys
import os
import time
import win32gui
import win32con

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.window import find_game_window
from src.core.memory import GameMemory
from src.arduino_keyboard import ArduinoKeyboard
from src.config import (
    MAGE_HEAL_THRESHOLD,
    MAGE_HEAL_DURATION,
    HEAL_KEY
)


def set_window_size_and_position(hwnd, width, height, x, y):
    """设置窗口大小和位置"""
    try:
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOP,
            x, y, width, height,
            win32con.SWP_SHOWWINDOW
        )
        print(f"✓ 窗口已设置为 {width}x{height}，位置 ({x}, {y})")
        return True
    except Exception as e:
        print(f"❌ 设置窗口失败: {e}")
        return False


class SingleMage:
    def __init__(self):
        self.game = None
        self.keyboard = None
        self.last_heal_time = 0
        self.heal_cooldown = 1.0   # 加血后冷却2秒

    def setup(self):
        print("=" * 50)
        print("单端法师自动加血脚本（运行即开始）")
        print(f"触发条件: 血量 < {MAGE_HEAL_THRESHOLD}")
        print(f"加血按键: {HEAL_KEY.upper()} 长按 {MAGE_HEAL_DURATION} 秒")
        print("=" * 50)

        # 1. 查找窗口
        hwnd = find_game_window()
        if not hwnd:
            print("❌ 未找到游戏窗口")
            return False
        print(f"✓ 找到窗口句柄: {hwnd}")

        # 2. 调整窗口分辨率和位置（1280x960 移动到 0,0）
        set_window_size_and_position(hwnd, 1280, 960, 0, 0)

        # 3. 连接内存
        self.game = GameMemory(hwnd)
        if not self.game.connect():
            print("❌ 内存连接失败")
            return False
        print("✓ 内存连接成功")

        # 4. 连接 Arduino
        self.keyboard = ArduinoKeyboard()
        if not self.keyboard.connect():
            print("❌ Arduino 连接失败")
            return False
        print("✓ Arduino 连接成功")

        return True

    def run(self):
        if not self.setup():
            return

        print("\n🚀 开始监控血量...\n")

        try:
            while True:
                now = time.time()
                if now - self.last_heal_time >= self.heal_cooldown:
                    hp = self.game.get_hp()
                    if hp is not None:
                        print(f"当前血量: {hp}")
                        if hp < MAGE_HEAL_THRESHOLD and hp > 0:
                            print(f"⚠️ 血量过低 ({hp})，触发加血")
                            self.keyboard.hold(HEAL_KEY, MAGE_HEAL_DURATION)
                            self.last_heal_time = now
                            # 加血后短暂等待技能生效
                            time.sleep(1)
                    else:
                        print("⚠️ 读取血量失败")
                time.sleep(0.5)   # 每0.5秒检测一次
        except KeyboardInterrupt:
            print("\n用户中断")
        finally:
            if self.game:
                self.game.close()
            if self.keyboard:
                self.keyboard.close()

if __name__ == "__main__":
    mage = SingleMage()
    mage.run()