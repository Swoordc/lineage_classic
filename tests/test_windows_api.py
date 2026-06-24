import ctypes
from ctypes import wintypes
import time
import sys, os


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
class CURSORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hCursor", ctypes.c_void_p),
        ("ptScreenPos", wintypes.POINT)
    ]

user32 = ctypes.windll.user32

def get_cursor_handle():
    cursor_info = CURSORINFO()
    cursor_info.cbSize = ctypes.sizeof(CURSORINFO)
    if user32.GetCursorInfo(ctypes.byref(cursor_info)):
        return cursor_info.hCursor
    return None

print("测试不同鼠标位置的特征码：")
print("请在5秒内依次将鼠标移到：")
print("1. 普通地面（3秒后）")
print("2. 攻击目标（6秒后）")
print("3. 其他UI元素（9秒后）")
print()

for i in range(15):
    handle = get_cursor_handle()
    print(f"第{i+1}秒: 光标句柄 = {handle}")
    time.sleep(1)