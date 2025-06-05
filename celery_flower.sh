#!/bin/bash

# Set environment variable to enable API without authentication 
# (only use this in development environments)
export FLOWER_UNAUTHENTICATED_API=true

# Activate virtual environment if needed
# source .venv/bin/activate

# Start Flower monitoring tool for Celery
celery -A core.celery.celery_app flower --port=5555
