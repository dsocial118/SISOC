from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from auditlog.models import LogEntry


class Command(BaseCommand):
    help = "Elimina entradas de auditoría (auditlog.LogEntry) más antiguas que N días."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=180,
            help="Cantidad de días de retención. Por defecto 180.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo muestra la cantidad de registros a eliminar sin borrarlos.",
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]
        cutoff = timezone.now() - timedelta(days=days)

        queryset = LogEntry.objects.filter(timestamp__lt=cutoff)
        total = queryset.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] {total} registros serían eliminados (anteriores a {cutoff})."
                )
            )
            return

        deleted, _ = queryset.delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"Eliminados {deleted} registros de auditoría anteriores a {cutoff}."
            )
        )
