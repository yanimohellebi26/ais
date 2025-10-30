from datetime import datetime
from worker import store

class TaskContext:
    """Publy message in Celery"""

    def __init__(self, task_id: str):
        self.task_id = task_id

    def publish(self, message: str):
        """Publie un message dans les logs de la tâche."""
        timestamp = datetime.utcnow().isoformat()
        log_entry = {"timestamp": timestamp, "message": message}
        store.append_task_log(self.task_id, log_entry)
