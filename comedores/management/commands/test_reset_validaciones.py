from django.core.management.base import BaseCommand
from comedores.services.validacion_service import ValidacionService
from comedores.models import Comedor


class Command(BaseCommand):
    help = "Prueba el reset de validaciones - simula el paso de 1 mes"

    def handle(self, *args, **options):
        # Mostrar estado actual
        validados = Comedor.objects.filter(estado_validacion="Validado").count()
        no_validados = Comedor.objects.filter(estado_validacion="No Validado").count()
        pendientes = Comedor.objects.filter(estado_validacion="Pendiente").count()

        self.stdout.write(f"Estado ANTES del reset:")
        self.stdout.write(f"  - Validados: {validados}")
        self.stdout.write(f"  - No Validados: {no_validados}")
        self.stdout.write(f"  - Pendientes: {pendientes}")

        # Ejecutar reset
        comedores_actualizados = ValidacionService.resetear_validaciones()

        # Mostrar estado después
        pendientes_despues = Comedor.objects.filter(
            estado_validacion="Pendiente"
        ).count()

        self.stdout.write(f"\nEstado DESPUÉS del reset:")
        self.stdout.write(f"  - Pendientes: {pendientes_despues}")
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Se resetearon {comedores_actualizados} comedores a estado Pendiente"
            )
        )
