from celery import Celery
import os
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "etl_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.autodiscover_tasks(["worker"])

redis_client = redis.Redis.from_url(REDIS_URL, db=1, decode_responses=True)

import worker.task_command
import worker.task_pipeline