"""Aplicación Celery; la programación funcional pertenece a PAS."""

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
app = Celery("sisoc")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(["pas"])
app.conf.beat_schedule = {
    "pas-month-end": {
        "task": "pas.tasks.schedule_month",
        "schedule": crontab(minute=0, hour=2, day_of_month="28-31"),
        "options": {"expires": 3600},
    },
    "pas-reconcile": {
        "task": "pas.tasks.reconcile",
        "schedule": 60.0,
        "options": {"expires": 60},
    },
}
