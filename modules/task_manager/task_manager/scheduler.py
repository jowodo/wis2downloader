from celery import Celery
import os

from shared.logging import setup_logging
from shared.redis_client import (REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB)

# Set up logging
setup_logging()  # Configure root logger
LOGGER = setup_logging(__name__)

if not REDIS_PASSWORD:
    raise ValueError("REDIS_PASSWORD must be set")

HOUSEKEEP_BACKEND_DB = int(os.getenv("HOUSEKEEP_BACKEND_DB", "2"))
HOUSEKEEP_RESULT_DB = int(os.getenv("HOUSEKEEP_RESULT_DB", "3"))

HOUSEKEEP_BROKER_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{HOUSEKEEP_BACKEND_DB}"
HOUSEKEEP_RESULT_BACKEND = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{HOUSEKEEP_RESULT_DB}"

# --- Celery App Setup ---
app = Celery('tasks',
             broker=HOUSEKEEP_BROKER_URL,
             result_backend=HOUSEKEEP_RESULT_BACKEND)
app.conf.worker_log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
app.conf.CELERYBEAT_LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()
app.conf.result_expires = 86400  # 1 day, or do we want 1 hour? (TBD)
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json'
)

# Import your tasks
app.autodiscover_tasks(['task_manager.tasks','task_manager.tasks.scheduled_tasks'])
