import time
from functools import wraps
from etl.utils.logger import Logger

def timer(func):
    """
    Decorator to measure execution time of a function and log it in HH:MM:SS.mmm format.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed = end_time - start_time

        # Convert in HH:MM:SS
        hours, rem = divmod(elapsed, 3600)
        minutes, seconds = divmod(rem, 60)
        Logger.timer(
            f"Function '{func.__name__}' executed in "
            f"{int(hours):02d}:{int(minutes):02d}:{seconds:06.3f}"
        )
        return result

    return wrapper
