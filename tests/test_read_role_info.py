"""测试读取角色信息"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.window import find_game_window
from src.core.memory import GameMemory


def main():
    # 1. 找窗口
    hwnd = find_game_window()
    if not hwnd:
        print("未找到游戏窗口")
        return
    
    print(f"找到窗口句柄: {hwnd}")
    
    # 2. 连接游戏内存
    game = GameMemory(hwnd)
    if not game.connect():
        print("连接游戏失败")
        return
    
    # 3. 读取所有信息
    info = game.get_all_info()
    
    # 4. 打印结果
    print("\n" + "=" * 50)
    print("角色信息")
    print("=" * 50)
    print(f"坐标X: {info['x']:.2f}")
    print(f"坐标Y: {info['y']:.2f}")
    print(f"血量: {info['hp']} / {info['max_hp']}")
    print(f"魔量: {info['mp']} / {info['max_mp']}")
    print(f"等级: {info['level']}")
    print("=" * 50)
    while True:
        info = game.get_hp()
        print(f"血量：{info}")
    
    game.close()


if __name__ == "__main__":
    main()