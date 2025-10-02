import time
from functools import wraps
from etl.utils.logger import Logger

def timer(func):
    """
    Decorator to measure execution time of a function and log it.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)  # exécution de la fonction
        end_time = time.time()
        elapsed = end_time - start_time
        Logger.timer(f"Function '{func.__name__}' executed in {round(elapsed, 3)} seconds")
        return result
    return wrapper
