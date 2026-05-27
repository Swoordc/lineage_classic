# 以坐标X为基准（offset = 0）
class Offset:
    X = 0x00      # 基准点
    Y = 0x04      # 坐标Y
    # 0x08 位置未知，可能是坐标Z或其他
    HP = 0x0C
    MAX_HP = 0x10
    MP = 0x14
    MAX_MP = 0x18
    LEVEL = 0x1C