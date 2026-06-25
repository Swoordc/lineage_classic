"""血条图色读取：基于空血参考色的百分比判断。

每个像素位置有一个对应的空血颜色，如果该位置颜色 ≠ 参考色，
说明此处有血量，即 HP ≥ 该百分比。
"""

# 空血条从左到右 96 像素的实际颜色
EMPTY_COLORS = [
    '5a1504', '571106', '222020', '211f1f', '211f1f', '222020', '232121', '232121',
    '211f1f', '211f1f', '201e1e', '201e1e', '211f1f', '232121', '242222', '232121',
    '232121', '242222', '232121', '211f1f', '201e1e', '1f1d1d', '1f1d1d', '1b1919',
    '1b1919', '252323', '282626', '201e1e', '222020', '232121', '222020', '272525',
    '222020', '272525', '292727', '232121', '211f1f', '262424', '252323', '252323',
    '252323', '242222', '252323', '282726', '252323', '211f1f', '211f1f', '211f1f',
    '252323', '262424', '232121', '242222', '252323', '232121', '222020', '242222',
    '242222', '242222', '242222', '252323', '262424', '262424', '242222', '232121',
    '211f1f', '222020', '211f1f', '201e1e', '222020', '242222', '252323', '242222',
    '242222', '242222', '222020', '211f1f', '211f1f', '222020', '232121', '232121',
    '211f1f', '211f1f', '201e1e', '201e1e', '211f1f', '232121', '242222', '232121',
    '232121', '242222', '232121', '211f1f', '201e1e', '1f1d1d', '1f1d1d', '1c1a1a',
]


# 名字区域扫描 — 判断队友是否远离
AWAY_X1, AWAY_Y1 = 0, -23         # 扫描区左上（相对血条起点）
AWAY_X2, AWAY_Y2 = 17, 17         # 扫描区右下
AWAY_LO = 0x74                     # 灰色下限
AWAY_HI = 0x78                     # 灰色上限
AWAY_MIN = 10                       # 灰色数量 ≥ 此值判定为远离


def _hex(img, x: int, y: int) -> str:
    pixel = img.getpixel((x, y))
    return f"{pixel[0]:02x}{pixel[1]:02x}{pixel[2]:02x}"


def _is_grayish(pixel: tuple) -> bool:
    """像素的三个通道是否都在 [0x10, 0x77] 之间（偏灰=远离）"""
    return all(AWAY_LO <= c <= AWAY_HI for c in pixel)


def is_away(img, bar_x: int, bar_y: int) -> bool:
    """队友是否远离（灰色像素 ≥ AWAY_MIN）"""
    gray, _ = count_grayish(img, bar_x, bar_y)
    return gray >= AWAY_MIN


def count_grayish(img, bar_x: int, bar_y: int) -> tuple[int, int]:
    """统计名字区域内偏灰像素数量，返回 (灰色数, 总数)"""
    x1 = bar_x + AWAY_X1
    y1 = bar_y + AWAY_Y1
    x2 = bar_x + AWAY_X2
    y2 = bar_y + AWAY_Y2
    gray = 0
    total = 0
    for py in range(y1, y2 + 1):
        for px in range(x1, x2 + 1):
            total += 1
            if _is_grayish(img.getpixel((px, py))):
                gray += 1
    return gray, total


def hp_above(img, bar_x: int, bar_y: int, pct: int) -> bool:
    """血条在 bar_x 处起算，当前百分比是否 ≥ pct。

    pct 范围 0-100，映射到 0-95 像素位置。
    返回值: True = HP ≥ pct，False = HP < pct。
    """
    idx = min(pct, 95)
    return _hex(img, bar_x + idx, bar_y) != EMPTY_COLORS[idx]
