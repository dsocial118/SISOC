import logging

from django.core.management.base import BaseCommand
from comunicados.services_mailing_jobs import run_mailing_jobs_worker

logger = logging.getLogger("django")


class Command(BaseCommand):
    help = "Procesa lotes de mailing masivo en background."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Ejecuta un ciclo y termina (para testing o cron).",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Iniciando worker de mailing masivo..."))
        try:
            run_mailing_jobs_worker(once=bool(options["once"]))
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Worker interrumpido por el usuario."))
        except Exception as exc:
            logger.exception("Fallo fatal en el worker de mailing masivo.")
            self.stdout.write(self.style.ERROR(f"Error: {exc}"))
