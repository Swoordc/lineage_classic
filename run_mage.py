"""双端法师脚本：
- 接收骑士血量（UDP）
- 读取自身血量
- 鼠标锁定跟随（启动时锁定，停止时解锁）
- 优先级：回家(F12) > 喝红水(F11) > 自保治愈(按住F8) > 骑士加血(点按F8)
- 自保治愈：按住F8直到血量超过阈值，期间不响应骑士加血，共用冷却
- 骑士加血：点按F8，共用冷却，仅在未按住F8时执行
"""

import sys
import os
import time
import socket
import threading
import pyautogui
import keyboard
import ctypes
import ctypes.wintypes

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.arduino_keyboard import ArduinoKeyboard
from src.utils.window import find_game_window
from src.core.memory import GameMemory
from src.config import (
    MAGE_BIND_PORT,
    KNIGHT_HEAL_THRESHOLD,
    MAGE_HEAL_THRESHOLD,       # 自保治愈阈值
    MAGE_HOME_THRESHOLD,       # 回家阈值（需要你添加）
    MAGE_POTION_THRESHOLD,     # 喝红水阈值（需要你添加）
    HEAL_COOLDOWN,             # 治愈冷却时间（秒）
    POTION_COOLDOWN,           # 红水冷却时间（秒，可选）
    HEAL_KEY,                  # "f8"
    HOME_KEY,                  # "f12"
    POTION_KEY,                # "f11"
    KNIGHT_HEAL_DURATION,      # 骑士加血按F8的时长（秒）
)

# ---------- 鼠标锁定 (ClipCursor) ----------
user32 = ctypes.windll.user32

def lock_mouse(x, y):
    rect = ctypes.wintypes.RECT()
    rect.left = x
    rect.right = x + 1
    rect.top = y
    rect.bottom = y + 1
    user32.ClipCursor(ctypes.byref(rect))
    pyautogui.moveTo(x, y)

def unlock_mouse():
    user32.ClipCursor(None)


class MageClient:
    def __init__(self):
        self.running = False          # 主循环运行标志（热键控制启动/停止）
        self.alive = True             # 脚本是否存活（用于退出）
        self.f8_pressed = False       # 是否正按住F8（自保中）
        self.heal_cooldown_end = 0    # 治愈冷却结束时间（时间戳）
        self.potion_cooldown_end = 0  # 红水冷却结束时间
        self.knight_hp = 1000         # 骑士血量（UDP更新）
        self.click_x = 0
        self.click_y = 0
        self.sock = None
        self.keyboard = None
        self.game = None
        self.udp_running = False
        self.udp_thread = None
        self.hp_lock = threading.Lock()

    # ---------- 初始化 ----------
    def setup(self):
        print("=" * 50)
        print("双端法师脚本（跟随+加血+自保+回家）")
        print(f"UDP端口: {MAGE_BIND_PORT}")
        print(f"回家阈值: {MAGE_HOME_THRESHOLD}  (按住{HOME_KEY.upper()}2秒)")
        print(f"喝红水阈值: {MAGE_POTION_THRESHOLD} (按{POTION_KEY.upper()})")
        print(f"自保治愈阈值: {MAGE_HEAL_THRESHOLD} (按住{HEAL_KEY.upper()}直到达标)")
        print(f"骑士加血阈值: {KNIGHT_HEAL_THRESHOLD} (点按{HEAL_KEY.upper()}{KNIGHT_HEAL_DURATION}秒)")
        print(f"治愈冷却: {HEAL_COOLDOWN}秒")
        print("=" * 50)

        # 1. 创建UDP套接字
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', MAGE_BIND_PORT))
        self.sock.settimeout(0.5)
        print(f"✓ UDP接收端口已绑定: {MAGE_BIND_PORT}")

        # 2. 连接Arduino
        self.keyboard = ArduinoKeyboard()
        if not self.keyboard.connect():
            print("❌ Arduino连接失败")
            return False

        # 3. 连接游戏内存
        hwnd = find_game_window()
        if not hwnd:
            print("❌ 未找到游戏窗口")
            return False
        self.game = GameMemory(hwnd)
        if not self.game.connect():
            print("❌ 内存连接失败")
            return False

        # 4. 启动UDP接收线程
        self.udp_running = True
        self.udp_thread = threading.Thread(target=self._udp_receiver, daemon=True)
        self.udp_thread.start()
        print("✓ UDP接收线程已启动")

        print("✓ 初始化完成")
        return True

    # ---------- 热键控制 ----------
    def start(self):
        if self.running:
            return
        self.running = True
        # 获取当前鼠标位置（骑士身上）并锁定
        self.click_x, self.click_y = pyautogui.position()
        print(f"🚀 脚本启动，记录鼠标位置 ({self.click_x}, {self.click_y})，锁定跟随")
        lock_mouse(self.click_x, self.click_y)

    def stop(self):
        if not self.running:
            return
        self.running = False
        # 如果正按住F8，先释放
        if self.f8_pressed:
            self.keyboard.release(HEAL_KEY)
            self.f8_pressed = False
        unlock_mouse()
        print("⏹️ 脚本已停止，鼠标解锁")

    # ---------- UDP接收线程 ----------
    def _udp_receiver(self):
        while self.udp_running:
            try:
                data, addr = self.sock.recvfrom(1024)
                hp = int(data.decode('utf-8'))
                with self.hp_lock:
                    self.knight_hp = hp
                print(f"📥 骑士血量: {hp}")
            except socket.timeout:
                continue
            except Exception as e:
                print(f"⚠️ UDP接收错误: {e}")

    # ---------- 主循环逻辑 ----------
    def run(self):
        if not self.setup():
            return

        keyboard.add_hotkey('home', self.start)
        keyboard.add_hotkey('end', self.stop)

        print("\n就绪... 按 Home 启动，End 停止")

        try:
            while self.alive:
                # 只有 running 为 True 时执行核心逻辑
                if self.running:
                    now = time.time()
                    hp = self.game.get_hp()
                    if hp is None:
                        time.sleep(0.05)
                        continue

                    # ----- 1. 回家（最高优先级）-----
                    if hp < MAGE_HOME_THRESHOLD:
                        # 先释放可能按住的F8
                        if self.f8_pressed:
                            self.keyboard.release(HEAL_KEY)
                            self.f8_pressed = False
                        print(f"⚠️ 血量过低({hp})，回家！按住{HOME_KEY.upper()} 2秒")
                        self.keyboard.hold(HOME_KEY, 2.0)
                        print("脚本已停止（回家）")
                        self.running = False
                        self.alive = False   # 退出整个脚本
                        break

                    # ----- 2. 喝红水 -----
                    if hp < MAGE_POTION_THRESHOLD and now >= self.potion_cooldown_end:
                        self.keyboard.click(POTION_KEY)
                        self.potion_cooldown_end = now + POTION_COOLDOWN
                        print(f"🍷 喝红水 (hp={hp})")
                        # 喝完后短暂等待，让药水生效
                        time.sleep(0.2)
                        continue  # 跳过后续治愈判断，下一轮再读血量

                    # ----- 3. 自保治愈（按住F8直到血量达标）-----
                    if hp < MAGE_HEAL_THRESHOLD and now >= self.heal_cooldown_end:
                        if not self.f8_pressed:
                            print(f"💚 自保治愈开始，按住{HEAL_KEY.upper()} (hp={hp})")
                            self.keyboard.press(HEAL_KEY)
                            self.f8_pressed = True
                            # 记录冷却（按下即开始冷却）
                            self.heal_cooldown_end = now + HEAL_COOLDOWN
                    else:
                        # 血量达标 或 冷却未过，释放F8
                        if self.f8_pressed:
                            print(f"✅ 自保治愈结束，释放{HEAL_KEY.upper()}")
                            self.keyboard.release(HEAL_KEY)
                            self.f8_pressed = False

                    # ----- 4. 骑士加血（仅在未按住F8且冷却未过时）-----
                    if (not self.f8_pressed) and now >= self.heal_cooldown_end:
                        with self.hp_lock:
                            knight_hp = self.knight_hp
                        if knight_hp < KNIGHT_HEAL_THRESHOLD:
                            print(f"💙 骑士加血，点按{HEAL_KEY.upper()} {KNIGHT_HEAL_DURATION}秒")
                            self.keyboard.click(HEAL_KEY, duration=KNIGHT_HEAL_DURATION)
                            self.heal_cooldown_end = now + HEAL_COOLDOWN

                time.sleep(0.05)   # 20Hz 循环

        except KeyboardInterrupt:
            print("\n用户中断")
        finally:
            self.cleanup()

    def cleanup(self):
        self.udp_running = False
        if self.sock:
            self.sock.close()
        if self.udp_thread:
            self.udp_thread.join(timeout=1)
        if self.f8_pressed:
            self.keyboard.release(HEAL_KEY)
        unlock_mouse()
        if self.keyboard:
            self.keyboard.close()
        if self.game:
            self.game.close()
        print("脚本已退出")


def main():
    mage = MageClient()
    mage.run()


if __name__ == "__main__":
    main()