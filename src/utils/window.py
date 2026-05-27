"""窗口工具"""

import win32con
import win32gui


def find_game_window(class_name: str = "GLFW30") -> int | None:
    hwnd = win32gui.FindWindow(class_name, None)
    return hwnd if hwnd else None


def set_window_size_and_position(
    hwnd: int, width: int, height: int, x: int, y: int
) -> bool:
    try:
        win32gui.SetWindowPos(
            hwnd, win32con.HWND_TOP,
            x, y, width, height,
            win32con.SWP_SHOWWINDOW,
        )
        return True
    except Exception as e:
        print(f"设置窗口失败: {e}")
        return False
