import logging
from logging.handlers import TimedRotatingFileHandler
import os
from datetime import datetime
import colorlog

class _ETLLogger:
    """
    Central logger singleton.
    Do not instantiate multiple times, use Logger instance from logger.py
    """

    SUCCESS_LEVEL = 25
    TIMER_LEVEL = 27
    logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")
    logging.addLevelName(TIMER_LEVEL, "TIMER")

    LEVEL_COLORS = {
        "SUCCESS": "green",
        "INFO": "blue",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "magenta",
        "TIMER": "cyan"
    }

    def __init__(self, name="ETL", log_dir="logs"):
        self.log_dir = log_dir
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.hasHandlers():
            os.makedirs(log_dir, exist_ok=True)
            self.current_log_file = os.path.join(log_dir, f"etl_{datetime.now():%Y-%m-%d}.log")

            # Console handler
            console_handler = logging.StreamHandler()
            console_formatter = colorlog.ColoredFormatter(
                "%(log_color)s%(levelname)s:%(reset)s %(message)s",
                log_colors=self.LEVEL_COLORS,
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

            # File handler
            file_handler = TimedRotatingFileHandler(
                self.current_log_file, when="midnight", interval=1, backupCount=7, encoding="utf-8"
            )
            file_formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def success(self, message):
        self.logger.log(self.SUCCESS_LEVEL,message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)

    def timer(self, message):
        self.logger.log(self.TIMER_LEVEL, message)

    def get_log_file(self, date: str = None) -> str:
        """
        Return log file path
        """
        if date:
            return os.path.join(self.log_dir, f"etl_{date}.log")
        return self.current_log_file