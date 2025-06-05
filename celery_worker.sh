#!/bin/bash

 
celery -A core.celery.celery_app worker --pool=solo --loglevel=info -Q elinity_ai
