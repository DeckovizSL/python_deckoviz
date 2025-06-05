from celery import Celery
from dotenv import load_dotenv
import os

load_dotenv()

# Create a Celery app with a unique namespace
# Using a unique namespace ensures tasks won't conflict
APP_NAME = 'python_deckovizai'

# Create Celery instance with explicit namespace
celery_app = Celery(
    APP_NAME,
    broker_url=os.getenv("CELERY_BROKER_URL"),
    result_backend=os.getenv("CELERY_RESULT_BACKEND"),
    timezone="UTC",
    enable_utc=True,
)

# Configure Celery
celery_app.conf.update(
    # Use a default queue with our namespace
    task_default_queue=APP_NAME,
    # Ignore unknown tasks - this prevents conflicts with other applications
    accept_content=['json'],
    # Allow creating queues as needed
    task_create_missing_queues=True,
    
    # Beat schedule configuration
    beat_schedule={
        'run-create-embeddings-every-minute': {
            'task': 'core.celery._tasks.create_embedding',
            'schedule': 60,  # Execute every 60 seconds
        },
        'run-create-metadata-every-minute': {
            'task': 'core.celery._tasks.create_metadata',
            'schedule': 60,  # Execute every 60 seconds
        }
    },
    timezone='UTC',
)

# Optional: Auto-discover tasks in your packages
celery_app.autodiscover_tasks(['core.celery._tasks'])
