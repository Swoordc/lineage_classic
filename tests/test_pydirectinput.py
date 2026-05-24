import pydirectinput
import time
import keyboard

def main():
    print("=" * 50)
    print("PyDirectInput 鼠标点击测试")
    print("=" * 50)
    print("请将鼠标移动到骑士身上")
    print("按 Home 开始每0.5秒点击一次（跟随测试）")
    print("按 End 停止")
    print("按 Ctrl+C 退出脚本")

    running = False
    click_x, click_y = 0, 0

    def start():
        nonlocal running, click_x, click_y
        if running:
            return
        click_x, click_y = pydirectinput.position()
        print(f"\n[启动] 记录鼠标位置: ({click_x}, {click_y})")
        print("[启动] 开始每0.5秒点击一次...")
        running = True
        # 先点击一次激活跟随
        pydirectinput.click(x=click_x, y=click_y)
        time.sleep(0.1)

    def stop():
        nonlocal running
        if not running:
            return
        running = False
        print("\n[停止] 已停止点击")

    keyboard.add_hotkey('home', start)
    keyboard.add_hotkey('end', stop)

    print("就绪...")

    try:
        while True:
            if running:
                pydirectinput.click(x=click_x, y=click_y)
                time.sleep(0.5)
            else:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n退出测试")

if __name__ == "__main__":
    main()