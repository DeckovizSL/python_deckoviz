from ._celery import celery_app
from . import _tasks

__all__ = ('celery_app',)
