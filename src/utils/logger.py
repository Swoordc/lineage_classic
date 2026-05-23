"""日志记录工具"""

import sys
import os
from datetime import datetime

class Logger:
    """简单的日志记录器"""
    
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # 创建今日日志文件
        today = datetime.now().strftime("%Y%m%d")
        self.log_file = os.path.join(log_dir, f"{today}.log")
    
    def _write(self, level, msg):
        """写入日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] [{level}] {msg}"
        
        # 控制台输出
        print(line)
        
        # 文件输出
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    
    def info(self, msg):
        self._write("INFO", msg)
    
    def error(self, msg):
        self._write("ERROR", msg)
    
    def warn(self, msg):
        self._write("WARN", msg)

# 全局日志实例
log = Logger()