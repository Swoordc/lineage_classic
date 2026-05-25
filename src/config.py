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
KNIGHT_HEAL_THRESHOLD = 235    # 骑士治愈触发阈值（双端）

# ========== 治愈时长 ==========
MAGE_HEAL_DURATION = 0.5       # 单端法师治愈按住秒数
MAGE_SELF_HEAL_DURATION = 1.5  # 双端法师自保按住秒数
KNIGHT_HEAL_DURATION = 0.5     # 双端骑士治愈按住秒数
HEAL_KEY = "f8"                # 加血快捷键

# ========== 骑士端（发送端）配置 ==========
# 法师电脑的 IP 和端口
MAGE_IP = "192.168.1.7"      # 改成法师电脑的实际 IP
MAGE_PORT = 18888             # 通信端口
SEND_INTERVAL = 0.5            # 发送间隔时间(秒)

# ========== 法师端（接收端）配置 ==========
MAGE_BIND_PORT = 18888        # UDP 接收端口

# ========== 跟随点击配置 ==========
FOLLOW_CLICK_INTERVAL = 0.3       # 点击间隔（秒）
CLICK_HOLD_DURATION = 0.2         # 每次点击的按住时长（秒）

# ========== 双端法师（自保与回家）配置 ==========
MAGE_HOME_THRESHOLD = 50          # 低于此值按F12回家
MAGE_POTION_THRESHOLD = 100       # 低于此值喝红水（F11）
HEAL_COOLDOWN = 2.0               # 治愈冷却时间（秒），自保和骑士共用
POTION_COOLDOWN = 0.5             # 红水冷却（秒），避免连续狂按，设为0则无冷却
HOME_KEY = "f12"                  # 回家快捷键
POTION_KEY = "f11"                # 喝水快捷键
# HEAL_KEY 你已经定义为 "f8"
# KNIGHT_HEAL_DURATION 你已有（之前是0.5）