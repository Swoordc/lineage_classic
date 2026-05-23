"""配置文件"""

# ========== Arduino 配置 ==========
ARDUINO_PORT = "COM4"        # 改成你的 Arduino 端口
ARDUINO_BAUDRATE = 9600

# ========== 游戏配置 ==========
GAME_PROCESS = "LC.exe"
BASE_OFFSET = "149B350"
WINDOW_CLASS = "GLFW30"

# ========== 按键配置 ==========
HEAL_KEY = "f8"

# ========== 血量阈值 ==========
MAGE_HEAL_THRESHOLD = 150      # 单端法师：自己的血量
KNIGHT_HEAL_THRESHOLD = 250    # 双端法师：骑士的血量

# ========== 骑士端（发送端）配置 ==========
# 法师电脑的 IP 和端口
MAGE_IP = "192.168.1.7"      # 改成法师电脑的实际 IP
MAGE_PORT = 18888             # 通信端口

# 发送频率（秒）
SEND_INTERVAL = 0.3          # 每秒约发送 3 次