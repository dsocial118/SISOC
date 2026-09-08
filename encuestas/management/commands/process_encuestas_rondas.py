from django.core.management.base import BaseCommand

from encuestas.services import run_encuestas_scheduler


class Command(BaseCommand):
    help = "Abre y cierra rondas de encuestas automáticamente según sus fechas."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Procesa un ciclo y termina (útil para tests y CI).",
        )

    def handle(self, *args, **options):
        run_encuestas_scheduler(once=bool(options["once"]))
