"""游戏辅助工具配置：Action 定义、硬件参数、网络设置、日志级别"""

from dataclasses import dataclass
from typing import Literal


# ========== Action 定义 ==========
@dataclass(frozen=True)
class Action:
    """技能/道具动作。同一个热键可以有多个 Action（如 F8 自保 vs F8 救打手）"""
    key: str          # 热键名 "f1"~"f12"
    hold: float       # 按住秒数
    cooldown: float   # 冷却时间（秒）
    threshold: int    # 触发阈值（血量低于此值触发）
    priority: int     # 越小越优先（0=回家, 1=红水, 2=自保, 3=救打手）


# --- 单端法师动作 ---
SINGLE_MAGE_ACTIONS = [
    Action("f8", hold=0.5, cooldown=1.0, threshold=130, priority=0),
]

# --- 双端法师动作 ---
HOME   = Action("f12", hold=1.0, cooldown=0,   threshold=70,  priority=0)
DRINK  = Action("f11", hold=0.1, cooldown=0.5, threshold=120, priority=1)
SELF_HEAL  = Action("f8", hold=1.5, cooldown=0.7, threshold=160, priority=2)
HEAL_OTHER = Action("f8", hold=0.5, cooldown=0.7, threshold=250, priority=3)

DUAL_MAGE_ACTIONS = [HOME, DRINK, SELF_HEAL, HEAL_OTHER]

# --- Buff 动作（双端法师周期性执行） ---
BUFF_ENABLED = False
BUFF_KEYS = ["f5", "f6", "f7", "f9", "f10"]
BUFF_HOLD_DURATION = 0.6
BUFF_KEY_INTERVAL = 2.0

# ========== Arduino 配置 ==========
ARDUINO_PORT = "COM6"
ARDUINO_BAUDRATE = 9600

# ========== 游戏配置 ==========
GAME_PROCESS = "LC.exe"
BASE_OFFSET = "14CC880"
WINDOW_CLASS = "GLFW30"

# ========== UDP 通信配置 ==========
UDP_PORT = 18888               # 发送端和接收端共用
ATTACKER_IP = "192.168.1.7"    # 法师电脑的 IP（打手发送目标）
SEND_INTERVAL = 0.2             # 打手发送间隔（秒）

# ========== 日志 ==========
LogLevel = Literal["DEBUG", "INFO", "WARN", "ERROR"]
LOG_LEVEL: LogLevel = "INFO"


def validate_config() -> None:
    """启动时校验配置合法性"""
    errors: list[str] = []

    # 检查阈值范围
    for name, action in [("SELF_HEAL", SELF_HEAL), ("HEAL_OTHER", HEAL_OTHER)]:
        if not (50 <= action.threshold <= 500):
            errors.append(f"{name}.threshold={action.threshold} 超出合理范围 50-500")

    if not (1024 <= UDP_PORT <= 65535):
        errors.append(f"UDP_PORT={UDP_PORT} 无效")

    if errors:
        raise ValueError("配置校验失败:\n  " + "\n  ".join(errors))