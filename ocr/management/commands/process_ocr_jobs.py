from django.core.management.base import BaseCommand

from ocr.services_ocr_jobs import run_ocr_jobs_worker


class Command(BaseCommand):
    help = "Procesa lotes OCR pendientes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Procesa un ciclo y termina (útil para tests y CI).",
        )

    def handle(self, *args, **options):
        run_ocr_jobs_worker(once=bool(options["once"]))
