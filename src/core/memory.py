import ctypes
from ctypes import wintypes
import win32process
import pymem
from src.config import GAME_PROCESS, BASE_OFFSET
from src.core.offsets import Offset
from src.utils.window import find_game_window
from src.utils.logger import log

# ----- 底层内存读取 API -----
ntdll = ctypes.WinDLL('ntdll')
kernel32 = ctypes.WinDLL('kernel32')
PROCESS_VM_READ = 0x0010

def _read_int_via_nt(pid, address):
    """使用 NtReadVirtualMemory 读取整数（每次临时打开进程）"""
    hProcess = kernel32.OpenProcess(PROCESS_VM_READ, False, pid)
    if not hProcess:
        return None
    buffer = ctypes.c_int()
    bytes_read = ctypes.c_size_t()
    status = ntdll.NtReadVirtualMemory(
        hProcess,
        ctypes.c_void_p(address),
        ctypes.byref(buffer),
        ctypes.sizeof(buffer),
        ctypes.byref(bytes_read)
    )
    kernel32.CloseHandle(hProcess)
    if status == 0:
        return buffer.value
    return None


class GameMemory:
    def __init__(self, hwnd):
        self.hwnd = hwnd
        self.pid = None
        self.struct_base = None
        self._base_offset_int = int(BASE_OFFSET, 16) if isinstance(BASE_OFFSET, str) else BASE_OFFSET

    def connect(self):
        """连接游戏，获取 PID 和结构体基址"""
        _, self.pid = win32process.GetWindowThreadProcessId(self.hwnd)
        log.info(f"窗口句柄: {self.hwnd}, 进程ID: {self.pid}")

        # 临时使用 pymem 获取模块基址（仅此一次）
        try:
            pm = pymem.Pymem(self.pid)
            modules = list(pm.list_modules())
            module_base = None
            for mod in modules:
                if mod.name == GAME_PROCESS:
                    module_base = mod.lpBaseOfDll
                    break
            if not module_base:
                log.error(f"找不到模块: {GAME_PROCESS}")
                return False
            self.struct_base = module_base + self._base_offset_int
            log.info(f"结构体基址(坐标X): 0x{self.struct_base:X}")
            # 不再使用 pymem 对象，让 pm 被垃圾回收（句柄会关闭）
            return True
        except Exception as e:
            log.error(f"连接失败: {e}")
            return False

    def get_hp(self):
        """读取血量（稳定版）"""
        if self.struct_base is None or self.pid is None:
            return None
        addr = self.struct_base + Offset.HP
        return _read_int_via_nt(self.pid, addr)

    # 其他方法（get_mp, get_level, get_coordinates 等）类似实现，都调用 _read_int_via_nt
    def get_mp(self):
        if self.struct_base is None:
            return None
        addr = self.struct_base + Offset.MP
        return _read_int_via_nt(self.pid, addr)

    def get_level(self):
        if self.struct_base is None:
            return None
        addr = self.struct_base + Offset.LEVEL
        return _read_int_via_nt(self.pid, addr)

    def get_coordinates(self):
        if self.struct_base is None:
            return None, None
        x_addr = self.struct_base + Offset.X
        y_addr = self.struct_base + Offset.Y
        x = _read_int_via_nt(self.pid, x_addr)
        y = _read_int_via_nt(self.pid, y_addr)
        return x, y

    def get_all_info(self):
        if self.struct_base is None:
            return {}
        return {
            "x": _read_int_via_nt(self.pid, self.struct_base + Offset.X),
            "y": _read_int_via_nt(self.pid, self.struct_base + Offset.Y),
            "hp": _read_int_via_nt(self.pid, self.struct_base + Offset.HP),
            "max_hp": _read_int_via_nt(self.pid, self.struct_base + Offset.MAX_HP),
            "mp": _read_int_via_nt(self.pid, self.struct_base + Offset.MP),
            "max_mp": _read_int_via_nt(self.pid, self.struct_base + Offset.MAX_MP),
            "level": _read_int_via_nt(self.pid, self.struct_base + Offset.LEVEL),
        }

    def close(self):
        """清理（此处无需显式关闭句柄）"""
        pass