import os
from celery import Celery
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'deckoviz.settings')

app = Celery('deckoviz')

# Load task modules from all registered Django app configs.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Set the worker and beat log file paths
app.conf.worker_logfile = '/app/logs/celery/celery-worker.log'  # Full path inside Docker container
app.conf.beat_logfile = '/app/logs/celery/celery-beat.log'

# Set the CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP configuration
app.conf.broker_connection_retry_on_startup = True

app.conf.worker_concurrency = 4  # Replace 4 with the desired number of concurrent workers

# Add Celery Beat scheduler
app.conf.beat_schedule = {
    'run_process_audio_task': {
        'task': 'common.apps.gallery.tasks.process_audio',
        'schedule': timedelta(seconds=10),  # Run every 10 seconds
    },  
    'run_populate_unsplash_images_task': {
        'task': 'common.apps.gallery.tasks.populate_unsplash_images',
        'schedule': timedelta(seconds=10),  # Run every 10 seconds
    },
        'run_generate_metadata_task': {
        'task': 'common.apps.gallery.tasks.generate_metadata',
        'schedule': timedelta(minutes=2),  # Run every 10 seconds
    },
}

app.autodiscover_tasks()
