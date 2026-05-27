"""四级日志：ERROR / WARN / INFO / DEBUG，惰性初始化"""

import os
from datetime import datetime
from typing import Literal

LogLevel = Literal["DEBUG", "INFO", "WARN", "ERROR"]

LEVEL_RANK: dict[LogLevel, int] = {"DEBUG": 0, "INFO": 1, "WARN": 2, "ERROR": 3}

_logger_instance: "Logger | None" = None


def get_logger(log_dir: str = "logs") -> "Logger":
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger(log_dir)
    return _logger_instance


def set_log_level(level: LogLevel) -> None:
    get_logger().min_level = level


class Logger:
    def __init__(self, log_dir: str) -> None:
        self.min_level: LogLevel = "INFO"
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        today = datetime.now().strftime("%Y%m%d")
        self.log_file = os.path.join(log_dir, f"{today}.log")

    def _write(self, level: LogLevel, msg: str) -> None:
        if LEVEL_RANK[level] < LEVEL_RANK[self.min_level]:
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] [{level}] {msg}"
        print(line)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def debug(self, msg: str) -> None:
        self._write("DEBUG", msg)

    def info(self, msg: str) -> None:
        self._write("INFO", msg)

    def warn(self, msg: str) -> None:
        self._write("WARN", msg)

    def error(self, msg: str) -> None:
        self._write("ERROR", msg)
