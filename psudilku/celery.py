import os

from celery import Celery

# from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "psudilku.settings")

app = Celery("psudilku")
app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.task_default_queue = "default"
app.conf.task_default_priority = 3
app.conf.result_expires = 1200

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.beat_schedule = {}

app.conf.broker_url = settings.CELERY_BROKER_URL
