"""脚本一：单端法师自动治愈"""

import sys
import os
import time

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.window import find_game_window
from src.core.memory import GameMemory
from src.config import MAGE_HEAL_THRESHOLD, MAGE_HEAL_DURATION, HEAL_KEY
from src.arduino_keyboard import ArduinoKeyboard


def main():
    print("=" * 50)
    print("单端法师自动治愈脚本")
    print(f"触发条件: 血量 < {MAGE_HEAL_THRESHOLD}")
    print(f"触发按键: {HEAL_KEY.upper()} (按住 {MAGE_HEAL_DURATION} 秒)")
    print("=" * 50)
    
    # 1. 查找游戏窗口
    hwnd = find_game_window()
    if not hwnd:
        print("❌ 未找到游戏窗口")
        return
    
    print(f"✓ 找到窗口句柄: {hwnd}")
    
    # 2. 连接游戏内存
    game = GameMemory(hwnd)
    if not game.connect():
        print("❌ 连接游戏失败")
        return
    
    # 3. 连接 Arduino
    keyboard = ArduinoKeyboard()
    if not keyboard.connect():
        print("❌ 连接 Arduino 失败")
        return
    
    print("\n✓ 初始化完成，开始监控血量...")
    print("按 Ctrl+C 停止\n")
    
    # 冷却时间相关
    last_heal_time = 0
    heal_cooldown = 3  # 加血后等待3秒，避免重复触发
    
    try:
        while True:
            # 读取血量
            hp = game.get_hp()
            
            if hp is not None:
                
                # 判断是否需要加血
                if hp < MAGE_HEAL_THRESHOLD and hp > 0:
                    current_time = time.time()
                    
                    # 检查冷却
                    if current_time - last_heal_time >= heal_cooldown:
                        print(f"⚠️ 血量过低 ({hp})，触发治愈术")
                        
                        keyboard.hold(HEAL_KEY, MAGE_HEAL_DURATION)
                        
                        last_heal_time = current_time

    except KeyboardInterrupt:
        print("\n\n用户中断，脚本停止")
    finally:
        game.close()
        keyboard.close()
        print("脚本已退出")


if __name__ == "__main__":
    main()