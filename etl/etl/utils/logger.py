# logger.py
from ._ETLLogger import _ETLLogger
import os
from dotenv import load_dotenv

load_dotenv()
log_dir = "data/logs"
os.makedirs(log_dir, exist_ok=True)

Logger = _ETLLogger(name="ETL", log_dir=log_dir)
