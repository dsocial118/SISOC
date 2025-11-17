from django.core.management.base import BaseCommand
from comedores.services.validacion_service import ValidacionService


class Command(BaseCommand):
    help = "Resetea el estado de validación de todos los comedores a Pendiente"

    def handle(self, *args, **options):
        comedores_actualizados = ValidacionService.resetear_validaciones()

        self.stdout.write(
            self.style.SUCCESS(
                f"Se resetearon {comedores_actualizados} comedores a estado Pendiente"
            )
        )
