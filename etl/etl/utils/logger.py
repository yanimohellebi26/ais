# logger.py
from ._ETLLogger import _ETLLogger
import os
from dotenv import load_dotenv

load_dotenv()
log_dir = os.getenv("LOG_DIR", "logs")
os.makedirs(log_dir, exist_ok=True)

Logger = _ETLLogger(name="ETL", log_dir=log_dir)
