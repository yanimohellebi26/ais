from worker.store import TaskStore

class TaskPublisher:
    def __init__(self, task_id: str = None, dummy: bool = False):
        self.dummy = dummy or task_id is None
        self.task_id = task_id

    def log(self, message: str, level="info"):
        if self.dummy:
            print(f"[{level}] {message}")
            return
        TaskStore.append_log(self.task_id, message, level=level)
