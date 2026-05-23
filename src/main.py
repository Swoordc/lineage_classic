import keyboard
import time

running = False

def start_script():
    global running
    running = True
    print("脚本已启动")

def stop_script():
    global running
    running = False
    print("脚本已停止")

keyboard.add_hotkey('home', start_script)
keyboard.add_hotkey('end', stop_script)

print("就绪... 按 Home 启动，End 停止")

while True:
    if running:
        # 骑士端：读血量并发送
        # 或法师端：接收并加血
        pass
    time.sleep(0.05)  # 高响应频率