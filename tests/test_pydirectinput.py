import pydirectinput
import time

# 等待3秒，给你时间将鼠标移动到骑士身上
print("请在3秒内将鼠标移动到骑士身上...")
time.sleep(3)

# 获取当前位置
x, y = pydirectinput.position()
print(f"当前位置: ({x}, {y})")

# 模拟长按左键（按下0.2秒再释放）
print("开始长按0.2秒...")
pydirectinput.mouseDown(button='left')
time.sleep(1)      # 按住0.2秒
pydirectinput.mouseUp(button='left')
print("点击完成，观察骑士是否跟随")