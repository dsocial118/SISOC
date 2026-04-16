from django.core.management.base import BaseCommand

from users.services_bulk_credentials_jobs import run_bulk_credentials_jobs_worker


class Command(BaseCommand):
    help = "Procesa lotes pendientes de credenciales masivas."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Procesa como maximo un lote pendiente y finaliza.",
        )

    def handle(self, *args, **options):
        run_bulk_credentials_jobs_worker(once=bool(options["once"]))
