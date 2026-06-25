"""测试 hp_bar — 血量百分比 + 远离检测（灰度区间）"""

import win32gui
from PIL import ImageGrab
from src.utils.hp_bar import hp_above, is_away, _hex, AWAY_X1, AWAY_Y1, AWAY_X2, AWAY_Y2, AWAY_LO, AWAY_HI


FIRST_ROW_X = 12
FIRST_ROW_Y = 797
COL = 103
ROW_H = 45
COLS = 2
ROWS = 4

CHAR_COLOR = "5a1504"
PCT = 50


def find_grayish(img, x1, y1, x2, y2) -> list:
    """返回区域内所有偏灰像素的 (x, y, 颜色串)"""
    found = []
    for py in range(y1, y2 + 1):
        for px in range(x1, x2 + 1):
            pixel = img.getpixel((px, py))
            if all(AWAY_LO <= c <= AWAY_HI for c in pixel):
                found.append((px, py, f"{pixel[0]:02x}{pixel[1]:02x}{pixel[2]:02x}"))
    return found


def main():
    hwnd = win32gui.FindWindow("GLFW30", None)
    if not hwnd:
        print("未找到游戏窗口")
        return

    left, top = win32gui.ClientToScreen(hwnd, (0, 0))
    img = ImageGrab.grab(bbox=(left, top, left + 1280, top + 960))

    print(f"血量阈值 {PCT}% | 灰色区间 {AWAY_LO:02x}~{AWAY_HI:02x}\n")

    stop = False
    for row in range(ROWS):
        if stop:
            break
        for col in range(COLS):
            x = FIRST_ROW_X + col * COL
            y = FIRST_ROW_Y + row * ROW_H

            c1 = _hex(img, x, y)
            if c1 != CHAR_COLOR:
                stop = True
                break

            ok = hp_above(img, x, y, PCT)
            actual = _hex(img, x + PCT, y)
            hp_str = f"HP{'≥' if ok else '<'}{PCT}%"

            far = is_away(img, x, y)
            away_str = "远离" if far else "在身旁"

            gray_pixels = find_grayish(img,
                                       x + AWAY_X1, y + AWAY_Y1,
                                       x + AWAY_X2, y + AWAY_Y2)

            print(f"[{col},{row}] {hp_str} | {away_str} | 像素[{x+PCT},{y}]={actual}")
            if gray_pixels:
                for gx, gy, gc in gray_pixels[:3]:
                    print(f"      灰色: ({gx},{gy})={gc}")
                if len(gray_pixels) > 3:
                    print(f"      ... 共 {len(gray_pixels)} 个灰色像素")

    img.close()


if __name__ == "__main__":
    main()
