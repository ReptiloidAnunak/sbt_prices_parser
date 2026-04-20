import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api_server.settings")

app = Celery("api_server")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()