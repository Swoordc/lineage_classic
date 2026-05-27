"""游戏内存读取：句柄复用 + 启动检测 + 进程存活检测"""

import ctypes
from ctypes import wintypes

import pymem
import win32process

from src.config import BASE_OFFSET, GAME_PROCESS
from src.game.offsets import Offset
from src.utils.logger import get_logger

log = get_logger()

ntdll = ctypes.WinDLL('ntdll')
kernel32 = ctypes.WinDLL('kernel32')
PROCESS_VM_READ = 0x0010
MAX_READ_ERRORS = 30  # 连续错误次数上限


class GameMemory:
    def __init__(self, hwnd: int) -> None:
        self.hwnd: int = hwnd
        self.pid: int | None = None
        self.struct_base: int | None = None
        self._process_handle: int | None = None
        self._error_count: int = 0
        base_offset_int = int(BASE_OFFSET, 16) if isinstance(BASE_OFFSET, str) else BASE_OFFSET
        self._base_offset_int: int = base_offset_int

    def connect(self) -> bool:
        """连接游戏：获取 PID → 模块基址 → 打开句柄 → 试读验证"""
        _, self.pid = win32process.GetWindowThreadProcessId(self.hwnd)
        log.info(f"进程ID: {self.pid}")

        # 获取模块基址（仅此一次用 pymem）
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
            log.info(f"结构体基址: 0x{self.struct_base:X}")
        except Exception as e:
            log.error(f"获取模块基址失败: {e}")
            return False

        # 打开进程句柄（复用）
        self._process_handle = kernel32.OpenProcess(PROCESS_VM_READ, False, self.pid)
        if not self._process_handle:
            log.error("打开进程句柄失败")
            return False

        # 启动试读
        test_hp = self.get_hp()
        if test_hp is None:
            log.error("启动试读失败，内存连接不可靠")
            self.close()
            return False
        log.info(f"启动试读成功: HP={test_hp}")
        return True

    def _read_int(self, address: int) -> int | None:
        if self._process_handle is None:
            return None
        buffer = ctypes.c_int()
        bytes_read = ctypes.c_size_t()
        status = ntdll.NtReadVirtualMemory(
            self._process_handle,
            ctypes.c_void_p(address),
            ctypes.byref(buffer),
            ctypes.sizeof(buffer),
            ctypes.byref(bytes_read),
        )
        if status == 0:
            self._error_count = 0
            return buffer.value
        self._error_count += 1
        return None

    def alive(self) -> bool:
        """进程是否存活（连续错误过多认为已关闭）"""
        return self._error_count < MAX_READ_ERRORS

    # ---- 便捷读取 ----

    def get_hp(self) -> int | None:
        if self.struct_base is None:
            return None
        return self._read_int(self.struct_base + Offset.HP)

    def get_mp(self) -> int | None:
        if self.struct_base is None:
            return None
        return self._read_int(self.struct_base + Offset.MP)

    def get_level(self) -> int | None:
        if self.struct_base is None:
            return None
        return self._read_int(self.struct_base + Offset.LEVEL)

    def get_coordinates(self) -> tuple[int | None, int | None]:
        if self.struct_base is None:
            return None, None
        x = self._read_int(self.struct_base + Offset.X)
        y = self._read_int(self.struct_base + Offset.Y)
        return x, y

    def get_all_info(self) -> dict[str, int | None]:
        if self.struct_base is None:
            return {}
        base = self.struct_base
        return {
            "x": self._read_int(base + Offset.X),
            "y": self._read_int(base + Offset.Y),
            "hp": self._read_int(base + Offset.HP),
            "max_hp": self._read_int(base + Offset.MAX_HP),
            "mp": self._read_int(base + Offset.MP),
            "max_mp": self._read_int(base + Offset.MAX_MP),
            "level": self._read_int(base + Offset.LEVEL),
        }

    def close(self) -> None:
        if self._process_handle:
            kernel32.CloseHandle(self._process_handle)
            self._process_handle = None
            log.info("内存句柄已释放")
