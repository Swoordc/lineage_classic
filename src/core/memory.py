"""游戏内存读取模块"""

import pymem
import win32process
from src.config import BASE_OFFSET, GAME_PROCESS
from src.core.offsets import Offset
from src.utils.logger import log


class GameMemory:
    """游戏内存操作类"""
    
    def __init__(self, hwnd):
        """
        初始化
        
        参数:
            hwnd: 游戏窗口句柄
        """
        self.hwnd = hwnd
        self.pid = None
        self.pm = None
        self.module_base = None
        self.struct_base = None
    
    def connect(self):
        """连接游戏进程"""
        # 1. 通过窗口句柄获取进程ID
        _, self.pid = win32process.GetWindowThreadProcessId(self.hwnd)
        log.info(f"窗口句柄: {self.hwnd}, 进程ID: {self.pid}")
        
        # 2. 连接进程
        try:
            self.pm = pymem.Pymem(self.pid)
        except Exception as e:
            log.error(f"连接进程失败: {e}")
            return False
        
        # 3. 获取模块基址
        try:
            modules = list(self.pm.list_modules())
            for module in modules:
                if module.name == GAME_PROCESS:
                    self.module_base = module.lpBaseOfDll
                    break
            
            if not self.module_base:
                log.error(f"找不到模块: {GAME_PROCESS}")
                return False
        except Exception as e:
            log.error(f"获取模块基址失败: {e}")
            return False
        
        # 4. 计算结构体基址（坐标X的位置）
        # 将十六进制字符串转换为整数
        base_offset_int = int(BASE_OFFSET, 16)
        self.struct_base = self.module_base + base_offset_int
        
        return True
    
    def read_float(self, offset):
        """读取浮点数"""
        if not self.pm:
            return None
        try:
            addr = self.struct_base + offset
            return self.pm.read_float(addr)
        except Exception as e:
            log.error(f"读取浮点数失败: 偏移 0x{offset:X}, 错误: {e}")
            return None
    
    def read_int(self, offset):
        """读取整数"""
        if not self.pm:
            return None
        try:
            addr = self.struct_base + offset
            return self.pm.read_int(addr)
        except Exception as e:
            log.error(f"读取整数失败: 偏移 0x{offset:X}, 错误: {e}")
            return None
    
    def get_coordinates(self):
        """获取坐标"""
        x = self.read_int(Offset.X)
        y = self.read_int(Offset.Y)
        return x, y
    
    def get_hp(self):
        """获取血量"""
        return self.read_int(Offset.HP)
    
    def get_max_hp(self):
        """获取最大血量"""
        return self.read_int(Offset.MAX_HP)
    
    def get_mp(self):
        """获取魔量"""
        return self.read_int(Offset.MP)
    
    def get_max_mp(self):
        """获取最大魔量"""
        return self.read_int(Offset.MAX_MP)
    
    def get_level(self):
        """获取等级"""
        return self.read_int(Offset.LEVEL)
    
    def get_all_info(self):
        """获取所有角色信息"""
        return {
            "x": self.read_int(Offset.X),      # 改成 read_int
            "y": self.read_int(Offset.Y),      # 改成 read_int
            "hp": self.read_int(Offset.HP),
            "max_hp": self.read_int(Offset.MAX_HP),
            "mp": self.read_int(Offset.MP),
            "max_mp": self.read_int(Offset.MAX_MP),
            "level": self.read_int(Offset.LEVEL),
        }
    
    def close(self):
        """关闭连接"""
        pass