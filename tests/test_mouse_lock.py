import ctypes
import ctypes.wintypes
import keyboard
import pyautogui

# Windows API 函数定义
user32 = ctypes.windll.user32

def lock_mouse(x, y):
    """将鼠标锁定在屏幕的 (x, y) 点（实际是锁定在一个1x1的矩形区域）"""
    rect = ctypes.wintypes.RECT()
    rect.left = x
    rect.right = x + 1
    rect.top = y
    rect.bottom = y + 1
    user32.ClipCursor(ctypes.byref(rect))
    # 将光标强制移动到锁定点
    pyautogui.moveTo(x, y)

def unlock_mouse():
    """解除鼠标锁定"""
    user32.ClipCursor(None)

def main():
    print("=== 鼠标锁定测试 (ClipCursor方案) ===")
    print("按 Home 锁定鼠标到当前位置")
    print("按 End 解锁鼠标")
    print("按 Ctrl+C 退出")

    def on_home():
        x, y = pyautogui.position()
        lock_mouse(x, y)
        print(f"[锁定] 鼠标锁定在 ({x}, {y})")

    def on_end():
        unlock_mouse()
        print("[解锁] 鼠标已解锁")

    keyboard.add_hotkey('home', on_home)
    keyboard.add_hotkey('end', on_end)

    try:
        keyboard.wait()
    except KeyboardInterrupt:
        print("\n退出")
    finally:
        unlock_mouse()

if __name__ == "__main__":
    main()