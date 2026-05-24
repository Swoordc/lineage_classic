"""配置文件"""

# ========== Arduino 配置 ==========
ARDUINO_PORT = "COM3"        # 改成你的 Arduino 端口
ARDUINO_BAUDRATE = 9600

# ========== 游戏配置 ==========
GAME_PROCESS = "LC.exe"
BASE_OFFSET = "149B350"
WINDOW_CLASS = "GLFW30"

# ========== 按键配置 ==========
HEAL_KEY = "f8"

# ========== 血量阈值 ==========
MAGE_HEAL_THRESHOLD = 130       # 法师治愈触发阈值（单端/双端共用）
KNIGHT_HEAL_THRESHOLD = 150    # 骑士治愈触发阈值（双端）

# ========== 治愈时长 ==========
MAGE_HEAL_DURATION = 1         # 单端法师治愈按住秒数
MAGE_SELF_HEAL_DURATION = 1.5  # 双端法师自保按住秒数
KNIGHT_HEAL_DURATION = 1       # 双端骑士治愈按住秒数

# ========== 骑士端（发送端）配置 ==========
# 法师电脑的 IP 和端口
MAGE_IP = "192.168.1.7"      # 改成法师电脑的实际 IP
MAGE_PORT = 18888             # 通信端口
SEND_INTERVAL = 0.3            # 每秒发送次数

# ========== 法师端（接收端）配置 ==========
MAGE_BIND_PORT = 18888        # UDP 接收端口

# ========== 跟随点击配置 ==========
FOLLOW_CLICK_INTERVAL = 0.5       # 点击间隔（秒）
CLICK_HOLD_DURATION = 0.6         # 每次点击的按住时长（秒）