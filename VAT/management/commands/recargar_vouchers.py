"""
Management command para renovación mensual de vouchers según parametrías.

Uso:
    python manage.py recargar_vouchers --check    # muestra qué se procesaría
    python manage.py recargar_vouchers --execute  # ejecuta la renovación

Cron (día 1 de cada mes a las 00:30):
    30 0 1 * * cd /sisoc && python manage.py recargar_vouchers --execute
"""

import logging
from datetime import date
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from VAT.models import VoucherParametria, Voucher
from VAT.services.voucher_service.impl import VoucherService

logger = logging.getLogger("django")


class Command(BaseCommand):
    help = "Renovación mensual de vouchers según las parametrías configuradas."

    def add_arguments(self, parser):
        parser.add_argument(
            "--check",
            action="store_true",
            help="Muestra qué se procesaría sin hacer cambios.",
        )
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Ejecuta la renovación.",
        )
        parser.add_argument(
            "--parametria",
            type=int,
            help="Limitar a una parametría específica (ID).",
        )

    def handle(self, *args, **options):
        check = options["check"]
        execute = options["execute"]

        if not check and not execute:
            self.stdout.write(self.style.WARNING("Usá --check o --execute."))
            return

        hoy = date.today()
        sistema = self._get_system_user()

        # Parametrías activas con renovación mensual habilitada
        qs = VoucherParametria.objects.filter(renovacion_mensual=True, activa=True).select_related("programa")
        if options["parametria"]:
            qs = qs.filter(pk=options["parametria"])

        if not qs.exists():
            self.stdout.write(self.style.WARNING("No hay parametrías con renovación mensual activa."))
            return

        self._separador()
        self.stdout.write(f"Renovación mensual de vouchers — {hoy}")
        self.stdout.write(f"Modo: {'VERIFICACIÓN' if check else 'EJECUCIÓN'}")
        self._separador()

        total_ok = 0
        total_err = 0
        total_venc = 0  # expirados marcados

        for parametria in qs:
            cantidad = parametria.cantidad_renovacion or parametria.cantidad_inicial
            reiniciar = parametria.renovacion_tipo == "reinicia"
            accion_label = "Reiniciar" if reiniciar else "Sumar"

            self.stdout.write(
                f"\n[{parametria.nombre}] programa={parametria.programa} "
                f"| {accion_label} {cantidad} créditos"
                f"| vence {parametria.fecha_vencimiento}"
            )

            # Vouchers vinculados a esta parametría que están activos o agotados
            vouchers = Voucher.objects.filter(
                parametria=parametria,
                estado__in=["activo", "agotado"],
            ).select_related("ciudadano")

            # También marcar como vencidos los que correspondan
            por_vencer = Voucher.objects.filter(
                parametria=parametria,
                estado__in=["activo", "agotado"],
                fecha_vencimiento__lt=hoy,
            )

            if check:
                self.stdout.write(f"  → {vouchers.count()} vouchers para renovar")
                self.stdout.write(f"  → {por_vencer.count()} vouchers a marcar como vencidos")
                continue

            # Marcar vencidos primero
            for v in por_vencer:
                v.estado = "vencido"
                v.save(update_fields=["estado", "fecha_modificacion"])
                VoucherService.validar_vencimiento(v)
                total_venc += 1
                self.stdout.write(
                    self.style.WARNING(f"  ⚠ Vencido: {v.ciudadano.nombre_completo}")
                )

            # Renovar los vigentes
            vigentes = Voucher.objects.filter(
                parametria=parametria,
                estado__in=["activo", "agotado"],
                fecha_vencimiento__gte=hoy,
            ).select_related("ciudadano")

            for voucher in vigentes:
                try:
                    ok, msg = VoucherService.recargar_voucher(
                        voucher=voucher,
                        cantidad=cantidad,
                        motivo="automatica",
                        usuario=sistema,
                        reiniciar=reiniciar,
                    )
                    if ok:
                        total_ok += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"  ✓ {voucher.ciudadano.nombre_completo}: {msg}")
                        )
                    else:
                        total_err += 1
                        self.stdout.write(
                            self.style.ERROR(f"  ✗ {voucher.ciudadano.nombre_completo}: {msg}")
                        )
                except Exception as e:
                    total_err += 1
                    logger.exception(f"Error renovando voucher {voucher.id}")
                    self.stdout.write(
                        self.style.ERROR(f"  ✗ {voucher.ciudadano.nombre_completo}: ERROR — {e}")
                    )

        self._separador()
        if not check:
            self.stdout.write(f"Renovados: {total_ok}  |  Vencidos marcados: {total_venc}  |  Errores: {total_err}")
            logger.info(
                f"recargar_vouchers: ok={total_ok} vencidos={total_venc} errores={total_err}"
            )
            if total_err:
                raise CommandError(f"Renovación completada con {total_err} errores.")

    def _separador(self):
        self.stdout.write("=" * 60)

    @staticmethod
    def _get_system_user():
        try:
            return User.objects.get(username="sistema")
        except User.DoesNotExist:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                raise CommandError("No se encontró usuario sistema o superusuario.")
            return user
