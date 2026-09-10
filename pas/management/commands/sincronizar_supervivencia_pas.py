"""Entrada operativa que solicita trabajo persistente sin llamadas externas."""

from datetime import date
from django.core.management.base import BaseCommand, CommandError
from pas.models import PasSupervivenciaRun
from pas.services.supervivencia_jobs import request_run


class Command(BaseCommand):
    help = "Solicita el control mensual o reanuda una corrida pausada."

    def add_arguments(self, parser):
        parser.add_argument("--fecha", type=date.fromisoformat)
        parser.add_argument("--reanudar", type=int)

    def handle(self, *args, **options):
        if options["reanudar"]:
            updated = PasSupervivenciaRun.objects.filter(
                pk=options["reanudar"], status="paused"
            ).update(status="running")
            if not updated:
                raise CommandError("La corrida no existe o no esta pausada.")
            self.stdout.write("Corrida reanudada desde el punto de control.")
        else:
            run = request_run(cutoff=options["fecha"])
            self.stdout.write(f"Corrida mensual #{run.pk}: {run.status}")
