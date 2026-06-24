"""采集空血血条 96 像素颜色 — 从 (12,797) 到 (107,797)"""

import win32gui
from PIL import ImageGrab


def main():
    hwnd = win32gui.FindWindow("GLFW30", None)
    if not hwnd:
        print("未找到游戏窗口")
        return

    left, top = win32gui.ClientToScreen(hwnd, (0, 0))
    img = ImageGrab.grab(bbox=(left, top, left + 1280, top + 960))

    colors = []
    for i in range(96):
        pixel = img.getpixel((12 + i, 797))
        colors.append(f"{pixel[0]:02x}{pixel[1]:02x}{pixel[2]:02x}")

    print(f"# 共 {len(colors)} 个像素")
    print(f"EMPTY_COLORS = [")
    for i in range(0, 96, 8):
        chunk = ", ".join(f"'{c}'" for c in colors[i:i + 8])
        print(f"    {chunk},")
    print("]")

    img.close()


if __name__ == "__main__":
    main()
