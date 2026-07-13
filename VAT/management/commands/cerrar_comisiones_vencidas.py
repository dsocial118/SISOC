"""
Management command para cerrar comisiones cuya fecha de fin ya pasó.

Cierra comisiones operativas (`ComisionCurso`) y de oferta institucional
(`Comision`) en estado planificada/activa cuando `fecha_fin < hoy`.
Las suspendidas no se tocan (decisión manual).

Uso:
    python manage.py cerrar_comisiones_vencidas --check    # muestra qué se cerraría
    python manage.py cerrar_comisiones_vencidas --execute  # cierra las comisiones

Cron (todos los días a la 01:00):
    0 1 * * * cd /sisoc && python manage.py cerrar_comisiones_vencidas --execute
"""

import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from VAT.services.comision_cierre_service import CierreComisionService

logger = logging.getLogger("django")


class Command(BaseCommand):
    help = (
        "Cierra comisiones (operativas y de oferta institucional) "
        "con fecha de fin vencida."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--check",
            action="store_true",
            help="Muestra qué se procesaría sin hacer cambios.",
        )
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Ejecuta el cierre.",
        )

    def handle(self, *args, **options):
        check = options["check"]
        execute = options["execute"]

        if not check and not execute:
            self.stdout.write(self.style.WARNING("Usá --check o --execute."))
            return

        hoy = timezone.localdate()

        self._separador()
        self.stdout.write(f"Cierre de comisiones vencidas — {hoy}")
        self.stdout.write(f"Modo: {'VERIFICACIÓN' if check else 'EJECUCIÓN'}")
        self._separador()

        if check:
            por_cerrar_curso = CierreComisionService.comisiones_curso_vencidas(hoy)
            por_cerrar_oferta = CierreComisionService.comisiones_oferta_vencidas(hoy)
            self.stdout.write(
                f"→ {por_cerrar_curso.count()} comisiones de curso a cerrar"
            )
            self.stdout.write(
                f"→ {por_cerrar_oferta.count()} comisiones de oferta a cerrar"
            )
            return

        resultado = CierreComisionService.cerrar_comisiones_vencidas(hoy)

        self._separador()
        self.stdout.write(
            self.style.SUCCESS(
                f"Comisiones de curso cerradas: {resultado['comisiones_curso']}  |  "
                f"Comisiones de oferta cerradas: {resultado['comisiones_oferta']}"
            )
        )
        logger.info(
            "cerrar_comisiones_vencidas: curso=%s oferta=%s",
            resultado["comisiones_curso"],
            resultado["comisiones_oferta"],
        )

    def _separador(self):
        self.stdout.write("=" * 60)
