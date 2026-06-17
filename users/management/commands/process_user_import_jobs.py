from django.core.management.base import BaseCommand

from users.services_user_import_jobs import run_user_import_jobs_worker


class Command(BaseCommand):
    help = "Procesa lotes pendientes de importacion masiva de usuarios."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Procesa como maximo un lote pendiente y finaliza.",
        )

    def handle(self, *args, **options):
        run_user_import_jobs_worker(once=bool(options["once"]))
