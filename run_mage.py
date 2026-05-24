"""脚本三：法师端 - 接收骑士血量，读取自己血量，跟随并加血"""

import sys
import os
import time
import socket
import threading
import pyautogui
import keyboard

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.arduino_keyboard import ArduinoKeyboard
from src.utils.window import find_game_window
from src.core.memory import GameMemory
from src.config import (
    MAGE_BIND_PORT,
    KNIGHT_HEAL_THRESHOLD,
    KNIGHT_HEAL_DURATION,
    MAGE_HEAL_THRESHOLD,
    MAGE_SELF_HEAL_DURATION,
    FOLLOW_CLICK_INTERVAL
)


class MageClient:
    """法师端：接收血量、自保、跟随、加血"""
    
    def __init__(self):
        self.running = False
        self.following = False
        self.knight_hp = 1000              # 骑士血量（初始高值）
        self.click_x = 0
        self.click_y = 0
        self.follow_thread = None
        self.sock = None
        self.keyboard = None
        self.game = None                   # 游戏内存（读自己血量）
        
    def setup(self):
        """初始化"""
        print("=" * 50)
        print("法师端脚本")
        print(f"UDP 接收端口: {MAGE_BIND_PORT}")
        print(f"骑士加血阈值: {KNIGHT_HEAL_THRESHOLD} (按住 {KNIGHT_HEAL_DURATION} 秒)")
        print(f"法师自保阈值: {MAGE_HEAL_THRESHOLD} (按住 {MAGE_SELF_HEAL_DURATION} 秒)")
        print(f"跟随点击间隔: {FOLLOW_CLICK_INTERVAL} 秒")
        print("=" * 50)
        
        # 1. 创建 UDP 套接字
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', MAGE_BIND_PORT))
        self.sock.settimeout(0.5)
        print(f"✓ UDP 接收端口已绑定: {MAGE_BIND_PORT}")
        
        # 2. 连接 Arduino
        self.keyboard = ArduinoKeyboard()
        if not self.keyboard.connect():
            print("❌ Arduino 连接失败")
            return False
        
        # 3. 连接游戏内存（读取法师自己血量）
        hwnd = find_game_window()
        if not hwnd:
            print("❌ 未找到游戏窗口")
            return False
        
        self.game = GameMemory(hwnd)
        if not self.game.connect():
            print("❌ 连接游戏内存失败")
            return False
        
        print("✓ 初始化完成")
        return True
    
    def start(self):
        """启动脚本"""
        if self.running:
            return
        
        self.running = True
        self.following = True
        
        # 获取当前鼠标位置（骑士身上）
        self.click_x, self.click_y = pyautogui.position()
        print(f"\n🚀 脚本启动")
        print(f"📌 获取鼠标位置: ({self.click_x}, {self.click_y})")
        
        # 启动跟随线程
        self.follow_thread = threading.Thread(target=self._follow_loop, daemon=True)
        self.follow_thread.start()
        print("🖱️ 跟随线程已启动")
    
    def stop(self):
        """停止脚本"""
        if not self.running:
            return
        
        self.running = False
        self.following = False
        print("\n⏹️ 脚本已停止")
    
    def _follow_loop(self):
        """跟随线程：持续点击固定位置"""
        while self.running:
            if self.following:
                pyautogui.click(x=self.click_x, y=self.click_y)
            time.sleep(FOLLOW_CLICK_INTERVAL)
    
    def _receive_knight_hp(self):
        """接收骑士血量（非阻塞）"""
        try:
            data, addr = self.sock.recvfrom(1024)
            hp_str = data.decode('utf-8')
            self.knight_hp = int(hp_str)
            print(f"📥 骑士血量: {self.knight_hp}")
        except socket.timeout:
            pass
        except Exception as e:
            print(f"⚠️ 接收错误: {e}")
    
    def _get_self_hp(self):
        """读取法师自己血量"""
        if self.game:
            return self.game.get_hp()
        return None
    
    def _heal(self, target, duration):
        """执行加血"""
        print(f"💚 {target} 触发治愈术，按住 F8 {duration} 秒")
        self.keyboard.hold("f8", duration)
        time.sleep(0.5)  # 加血后短暂等待
    
    def _check_and_heal(self):
        """检查是否需要加血（优先级：自己 > 骑士）"""
        # 1. 先检查法师自己血量（自保优先级最高）
        self_hp = self._get_self_hp()
        if self_hp is not None and self_hp < MAGE_HEAL_THRESHOLD:
            print(f"⚠️ 法师血量过低: {self_hp}")
            self._heal("法师自保", MAGE_SELF_HEAL_DURATION)
            return  # 自己加血后跳过骑士加血，避免同时触发
        
        # 2. 再检查骑士血量
        if self.knight_hp < KNIGHT_HEAL_THRESHOLD:
            print(f"⚠️ 骑士血量过低: {self.knight_hp}")
            self._heal("骑士", KNIGHT_HEAL_DURATION)
    
    def run(self):
        """主循环"""
        if not self.setup():
            return
        
        # 注册热键
        keyboard.add_hotkey('home', self.start)
        keyboard.add_hotkey('end', self.stop)
        
        print("\n就绪... 按 Home 启动，End 停止")
        
        try:
            while True:
                # 接收骑士血量
                self._receive_knight_hp()
                
                # 如果脚本运行中，检查是否需要加血
                if self.running:
                    self._check_and_heal()
                
                time.sleep(0.05)
                
        except KeyboardInterrupt:
            print("\n用户中断")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        self.running = False
        if self.sock:
            self.sock.close()
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