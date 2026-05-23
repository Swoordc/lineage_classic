"""窗口查找工具"""

import win32gui


def find_game_window(class_name="GLFW30"):
    """
    查找游戏窗口
    
    参数:
        class_name: 窗口类名
    
    返回:
        窗口句柄，找不到返回 None
    """
    return win32gui.FindWindow(class_name, None)