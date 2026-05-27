"""测试游戏内存读取"""
import time
from src.game.memory import GameMemory
from src.utils.window import find_game_window


def main():
    hwnd = find_game_window()
    if not hwnd:
        print("未找到游戏窗口")
        return
    game = GameMemory(hwnd)
    if not game.connect():
        print("连接失败")
        return
    print("开始循环读取血量，每 0.05 秒一次，共 100 次...")
    for i in range(100):
        hp = game.get_hp()
        if hp is not None:
            print(f"{i}: HP = {hp}")
        else:
            print(f"{i}: 读取失败")
            break
        time.sleep(0.05)
    game.close()


if __name__ == "__main__":
    main()
