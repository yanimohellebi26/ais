from worker.store import TaskStore

class TaskPublisher:
    def __init__(self, task_id: str):
        self.task_id = task_id

    def log(self, message: str, level="info"):
        TaskStore.append_log(self.task_id, message, level=level)
