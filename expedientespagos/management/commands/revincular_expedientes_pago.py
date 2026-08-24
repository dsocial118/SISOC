"""Reintenta vincular expedientes de pago que quedaron sin admisión asignada.

Uso típico:

    python manage.py revincular_expedientes_pago --dry-run
    python manage.py revincular_expedientes_pago
    python manage.py revincular_expedientes_pago --comedor 1529
"""

from django.core.management.base import BaseCommand

from expedientespagos.models import ExpedientePago
from expedientespagos.vinculacion import revincular_expedientes_sueltos


class Command(BaseCommand):
    help = "Revincula expedientes de pago sin admisión con la admisión que corresponda."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Informa cuántos se vincularían, sin escribir nada.",
        )
        parser.add_argument(
            "--comedor",
            type=int,
            default=None,
            help="Limita el reintento a un comedor.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        comedor_id = options["comedor"]

        pendientes_antes = ExpedientePago.objects.filter(admision__isnull=True)
        if comedor_id:
            pendientes_antes = pendientes_antes.filter(comedor_id=comedor_id)
        total_pendientes = pendientes_antes.count()

        resultado = revincular_expedientes_sueltos(
            comedor=comedor_id,
            guardar=not dry_run,
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("Simulación: no se escribió ningún cambio.")
            )

        self.stdout.write(f"Sin admisión al inicio: {total_pendientes}")
        self.stdout.write(f"Revisados: {resultado['revisados']}")
        self.stdout.write(self.style.SUCCESS(f"Vinculados: {resultado['vinculados']}"))

        sin_resolver = resultado["revisados"] - resultado["vinculados"]
        if sin_resolver:
            self.stdout.write(
                f"Quedan sin admisión: {sin_resolver} "
                "(sin coincidencia, o con más de una)"
            )
