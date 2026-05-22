from django.core.management.base import BaseCommand

from ciudadanos.services_importacion_masiva_jobs import (
    run_ciudadanos_import_jobs_worker,
)


class Command(BaseCommand):
    help = "Procesa lotes pendientes de importacion masiva de ciudadanos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Procesa un ciclo y termina.",
        )

    def handle(self, *args, **options):
        run_ciudadanos_import_jobs_worker(once=options["once"])
