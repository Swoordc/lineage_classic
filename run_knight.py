"""脚本二：骑士端 - 读取血量并通过 UDP 发送给法师"""

import sys
import os
import time
import socket

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.window import find_game_window
from src.core.memory import GameMemory
from src.config import MAGE_IP, MAGE_PORT, SEND_INTERVAL


def main():
    print("=" * 50)
    print("骑士端脚本")
    print("发送目标: {}:{}".format(MAGE_IP, MAGE_PORT))
    print("发送间隔: {} 秒".format(SEND_INTERVAL))
    print("=" * 50)
    
    # 1. 创建 UDP 套接字
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # 2. 查找游戏窗口
    hwnd = find_game_window()
    if not hwnd:
        print("❌ 未找到游戏窗口")
        return
    
    print("✓ 找到窗口句柄: {}".format(hwnd))
    
    # 3. 连接游戏内存
    game = GameMemory(hwnd)
    if not game.connect():
        print("❌ 连接游戏失败")
        return
    
    print("\n✓ 初始化完成，开始发送血量...")
    print("按 Ctrl+C 停止\n")
    
    try:
        while True:
            # 读取血量
            hp = game.get_hp()
            
            if hp is not None and hp > 0:
                # 发送血量
                data = str(hp).encode('utf-8')
                sock.sendto(data, (MAGE_IP, MAGE_PORT))
                print("📤 发送血量: {}".format(hp))
            else:
                print("⚠️ 读取血量失败")
            
            # 等待发送间隔
            time.sleep(SEND_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n用户中断，脚本停止")
    finally:
        sock.close()
        game.close()
        print("脚本已退出")


if __name__ == "__main__":
    main()