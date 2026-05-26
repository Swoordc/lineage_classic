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
    MAGE_HEAL_THRESHOLD,
    MAGE_HOME_THRESHOLD,
    MAGE_POTION_THRESHOLD,
    HEAL_COOLDOWN,
    POTION_COOLDOWN,
    HEAL_KEY,
    HOME_KEY,
    POTION_KEY,
    KNIGHT_HEAL_DURATION,
    # 加Buff配置
    BUFF_ENABLED,
    BUFF_KEYS,
    BUFF_HOLD_DURATION,
    BUFF_KEY_INTERVAL,
    BUFF_CYCLE_INTERVAL,
)

# ---------- 周期性加Buff功能 ----------
def periodic_keys(keyboard, keys, hold_duration, key_interval, cycle_interval):
    """
    周期性依次按下指定的按键列表
    """
    while True:
        time.sleep(cycle_interval)
        for key in keys:
            keyboard.hold(key, hold_duration)
            time.sleep(key_interval)

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
        self.running = False
        self.alive = True
        self.f8_pressed = False
        self.heal_cooldown_end = 0
        self.potion_cooldown_end = 0
        self.knight_hp = 1000
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
        if BUFF_ENABLED:
            print(f"自动加Buff: 每{BUFF_CYCLE_INTERVAL//60}分钟依次 {BUFF_KEYS} (按住{BUFF_HOLD_DURATION}秒, 间隔{BUFF_KEY_INTERVAL}秒)")
        else:
            print("自动加Buff: 禁用")
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

        # 5. 如果配置启用，启动周期性加Buff线程
        if BUFF_ENABLED:
            self.key_thread = threading.Thread(
                target=periodic_keys,
                args=(self.keyboard, BUFF_KEYS, BUFF_HOLD_DURATION, BUFF_KEY_INTERVAL, BUFF_CYCLE_INTERVAL),
                daemon=True
            )
            self.key_thread.start()
            print(f"✓ 自动加Buff线程已启动")

        print("✓ 初始化完成")
        return True

    # ---------- 热键控制 ----------
    def start(self):
        if self.running:
            return
        self.running = True
        self.click_x, self.click_y = pyautogui.position()
        print(f"🚀 脚本启动，记录鼠标位置 ({self.click_x}, {self.click_y})，锁定跟随")
        lock_mouse(self.click_x, self.click_y)

    def stop(self):
        if not self.running:
            return
        self.running = False
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
                if self.running:
                    now = time.time()
                    hp = self.game.get_hp()
                    if hp is None:
                        time.sleep(0.05)
                        continue

                    # ----- 1. 回家（最高优先级）-----
                    if hp < MAGE_HOME_THRESHOLD:
                        if self.f8_pressed:
                            self.keyboard.release(HEAL_KEY)
                            self.f8_pressed = False
                        print(f"⚠️ 血量过低({hp})，回家！按住{HOME_KEY.upper()} 2秒")
                        self.keyboard.hold(HOME_KEY, 2.0)
                        print("脚本已停止（回家）")
                        self.running = False
                        self.alive = False
                        break

                    # ----- 2. 喝红水 -----
                    if hp < MAGE_POTION_THRESHOLD and now >= self.potion_cooldown_end:
                        self.keyboard.click(POTION_KEY)
                        self.potion_cooldown_end = now + POTION_COOLDOWN
                        print(f"🍷 喝红水 (hp={hp})")
                        continue

                    # ----- 3. 自保治愈（按住F8直到血量达标）-----
                    if hp < MAGE_HEAL_THRESHOLD and now >= self.heal_cooldown_end:
                        if not self.f8_pressed:
                            print(f"💚 自保治愈开始，按住{HEAL_KEY.upper()} (hp={hp})")
                            self.keyboard.press(HEAL_KEY)
                            self.f8_pressed = True
                            self.heal_cooldown_end = now + HEAL_COOLDOWN
                    elif self.f8_pressed and hp >= MAGE_HEAL_THRESHOLD:
                        print(f"✅ 自保治愈结束，释放{HEAL_KEY.upper()}")
                        self.keyboard.release(HEAL_KEY)
                        self.f8_pressed = False

                    # ----- 4. 骑士加血（仅在未按住F8且冷却未过时）-----
                    if (not self.f8_pressed) and now >= self.heal_cooldown_end:
                        with self.hp_lock:
                            knight_hp = self.knight_hp
                        if knight_hp < KNIGHT_HEAL_THRESHOLD:
                            print(f"💙 骑士加血，点按{HEAL_KEY.upper()} {KNIGHT_HEAL_DURATION}秒")
                            self.keyboard.hold(HEAL_KEY, KNIGHT_HEAL_DURATION)
                            self.heal_cooldown_end = now + HEAL_COOLDOWN

                time.sleep(0.05)

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