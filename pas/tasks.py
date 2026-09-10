"""Adaptadores mínimos entre Celery y los servicios de PAS."""

from celery import shared_task

from pas.services.supervivencia_jobs import (
    process_batch,
    reconcile_jobs,
    schedule_monthly,
)


@shared_task
def schedule_month():
    schedule_monthly()


@shared_task
def reconcile():
    reconcile_jobs()


@shared_task(acks_late=True, reject_on_worker_lost=True)
def run_batch(batch_id):
    process_batch(batch_id)
