"""测试 hp_bar & 队友距离 — 血量百分比 + 名字区域是否灰色（远离）"""

import win32gui
from PIL import ImageGrab
from src.utils.hp_bar import hp_above, _hex


FIRST_ROW_X = 12
FIRST_ROW_Y = 797
COL = 103
ROW_H = 45
COLS = 2
ROWS = 4

CHAR_COLOR = "5a1504"
AWAY_COLOR = "777777"         # 名字灰色 = 远离
AWAY_X1, AWAY_Y1 = 0, -23    # 名字扫描区偏移（相对血条起点）
AWAY_X2, AWAY_Y2 = 18, 18
PCT = 50


def has_color(img, x1, y1, x2, y2, target: str) -> bool:
    """在矩形区域内逐像素查找目标颜色，找到即返回 True"""
    for py in range(y1, y2 + 1):
        for px in range(x1, x2 + 1):
            if _hex(img, px, py) == target:
                return True
    return False


def main():
    hwnd = win32gui.FindWindow("GLFW30", None)
    if not hwnd:
        print("未找到游戏窗口")
        return

    left, top = win32gui.ClientToScreen(hwnd, (0, 0))
    img = ImageGrab.grab(bbox=(left, top, left + 1280, top + 960))

    print(f"血量阈值 {PCT}% | 远离颜色 {AWAY_COLOR}\n")

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

            # 血量
            ok = hp_above(img, x, y, PCT)
            actual = _hex(img, x + PCT, y)
            hp_str = f"HP{'≥' if ok else '<'}{PCT}%"

            # 距离
            far = has_color(img,
                            x + AWAY_X1, y + AWAY_Y1,
                            x + AWAY_X2, y + AWAY_Y2,
                            AWAY_COLOR)
            away_str = "远离" if far else "在身旁"

            print(f"[{col},{row}] {hp_str} | {away_str} | 像素[{x+PCT},{y}]={actual}")

    img.close()


if __name__ == "__main__":
    main()
