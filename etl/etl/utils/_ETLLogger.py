# logger.py
import logging
from logging.handlers import RotatingFileHandler

class _ETLLogger:
    """
    Central logger singleton .
    Do no instantiate, use 'logger' "from ._ETLLogger import logger"
    """

    LEVEL_COLORS = {
        "SUCCESS": "\033[92m",
        "INFO": "\033[94m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
        "CRITICAL": "\033[95m",
        "RESET": "\033[0m"
    }

    def __init__(self, name="ETL", log_file="etl.log"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)  # Catch all

        if not self.logger.hasHandlers():  # Avoid double
            # Handler console
            console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

            # Handler rotating files
            file_handler = RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=5)
            file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    # Simple use case
    def success(self, message):
        colored = f"{self.LEVEL_COLORS['SUCCESS']}SUCCESS: {message}{self.LEVEL_COLORS['RESET']}"
        self.logger.info(colored)

    def info(self, message):
        colored = f"{self.LEVEL_COLORS['INFO']}INFO: {message}{self.LEVEL_COLORS['RESET']}"
        self.logger.info(colored)

    def warning(self, message):
        colored = f"{self.LEVEL_COLORS['WARNING']}WARNING: {message}{self.LEVEL_COLORS['RESET']}"
        self.logger.warning(colored)

    def error(self, message):
        colored = f"{self.LEVEL_COLORS['ERROR']}ERROR: {message}{self.LEVEL_COLORS['RESET']}"
        self.logger.error(colored)

    def critical(self, message):
        colored = f"{self.LEVEL_COLORS['CRITICAL']}CRITICAL: {message}{self.LEVEL_COLORS['RESET']}"
        self.logger.critical(colored)