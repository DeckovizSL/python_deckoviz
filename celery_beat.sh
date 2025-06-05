#!/bin/bash

# Start Celery Beat scheduler
# This ensures your tasks run automatically at scheduled intervals

# Activate virtual environment if needed
# source .venv/bin/activate

# Start Celery Beat scheduler
celery -A core.celery.celery_app beat --loglevel=info
