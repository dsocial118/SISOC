import logging
from datetime import date, timedelta
from django.db import transaction
from django.contrib.auth.models import User
from VAT.models import Voucher, VoucherRecarga, VoucherUso, VoucherLog, InscripcionOferta

logger = logging.getLogger("django")


class VoucherService:
    """Service layer for Voucher business logic."""

    @staticmethod
    def crear_voucher(
        ciudadano_id: int,
        programa_id: int,
        cantidad: int,
        fecha_vencimiento: date,
        usuario: User,
        parametria=None,
    ) -> Voucher:
        """Create a new voucher for a citizen."""
        with transaction.atomic():
            voucher = Voucher.objects.create(
                ciudadano_id=ciudadano_id,
                programa_id=programa_id,
                cantidad_inicial=cantidad,
                cantidad_usada=0,
                cantidad_disponible=cantidad,
                fecha_vencimiento=fecha_vencimiento,
                estado="activo",
                parametria=parametria,
                asignado_por=usuario,
            )

            VoucherLog.objects.create(
                voucher=voucher,
                tipo_evento="asignacion",
                cantidad_afectada=cantidad,
                usuario=usuario,
                detalles={"razon": "Creación inicial de voucher"},
            )

        logger.info(f"Voucher {voucher.id} creado para {voucher.ciudadano}")
        return voucher

    @staticmethod
    def recargar_voucher(
        voucher: Voucher,
        cantidad: int,
        motivo: str,
        usuario: User,
        reiniciar: bool = False,
    ) -> tuple[bool, str]:
        """
        Reload credits to a voucher.
        reiniciar=True: sets cantidad_disponible to `cantidad` and cantidad_usada to 0.
        reiniciar=False (default): adds `cantidad` to existing balance.
        """
        if voucher.estado == "cancelado":
            return False, "No se puede recargar un voucher cancelado."

        with transaction.atomic():
            if reiniciar:
                voucher.cantidad_disponible = cantidad
                voucher.cantidad_usada = 0
                update_fields = ["cantidad_disponible", "cantidad_usada", "estado", "fecha_modificacion"]
            else:
                voucher.cantidad_disponible += cantidad
                update_fields = ["cantidad_disponible", "estado", "fecha_modificacion"]

            # Reactivar si estaba agotado o vencido
            if voucher.estado in ("agotado", "vencido"):
                voucher.estado = "activo"

            voucher.save(update_fields=update_fields)

            VoucherRecarga.objects.create(
                voucher=voucher,
                cantidad=cantidad,
                motivo=motivo,
                autorizado_por=usuario,
            )

            VoucherLog.objects.create(
                voucher=voucher,
                tipo_evento="recarga",
                cantidad_afectada=cantidad,
                usuario=usuario,
                detalles={"motivo": motivo, "reiniciado": reiniciar},
            )

        logger.info(
            f"Voucher {voucher.id} {'reiniciado' if reiniciar else 'recargado'} con {cantidad} créditos ({motivo})"
        )
        return True, f"Voucher {'reiniciado' if reiniciar else 'recargado'} con {cantidad} créditos."

    @staticmethod
    def usar_voucher(
        voucher: Voucher,
        inscripcion_oferta: InscripcionOferta,
        cantidad: int,
    ) -> tuple[bool, str]:
        """Use voucher credits for an offering enrollment."""
        # Actualizar estado de vencimiento antes de validar (evita usar vouchers expirados con estado stale)
        VoucherService.validar_vencimiento(voucher)

        if voucher.estado == "cancelado":
            return False, "El voucher ha sido cancelado."

        if voucher.estado == "vencido":
            return False, "El voucher ha vencido."

        if voucher.cantidad_disponible < cantidad:
            return (
                False,
                f"Créditos insuficientes. Disponible: {voucher.cantidad_disponible}",
            )

        # Use voucher
        with transaction.atomic():
            voucher.cantidad_usada += cantidad
            voucher.cantidad_disponible -= cantidad

            # Update estado if exhausted
            if voucher.cantidad_disponible == 0:
                voucher.estado = "agotado"

            voucher.save(
                update_fields=[
                    "cantidad_usada",
                    "cantidad_disponible",
                    "estado",
                    "fecha_modificacion",
                ]
            )

            VoucherUso.objects.create(
                voucher=voucher,
                inscripcion_oferta=inscripcion_oferta,
                cantidad_usada=cantidad,
            )

            VoucherLog.objects.create(
                voucher=voucher,
                tipo_evento="uso",
                cantidad_afectada=-cantidad,
                usuario=inscripcion_oferta.inscrito_por,
                detalles={
                    "inscripcion_oferta_id": inscripcion_oferta.id,
                    "oferta": str(inscripcion_oferta.oferta),
                },
            )

        logger.info(
            f"Voucher {voucher.id} utilizado: {cantidad} créditos "
            f"en {inscripcion_oferta.oferta}"
        )
        return True, f"Créditos utilizados exitosamente. Disponible: {voucher.cantidad_disponible}"

    @staticmethod
    def cancelar_voucher(voucher: Voucher, usuario: User) -> bool:
        """Cancel a voucher."""
        if voucher.estado == "cancelado":
            return False

        with transaction.atomic():
            voucher.estado = "cancelado"
            voucher.save(update_fields=["estado", "fecha_modificacion"])

            VoucherLog.objects.create(
                voucher=voucher,
                tipo_evento="cancelacion",
                cantidad_afectada=0,
                usuario=usuario,
                detalles={"razon": "Cancelación manual"},
            )

        logger.info(f"Voucher {voucher.id} cancelado")
        return True

    @staticmethod
    def validar_vencimiento(voucher: Voucher) -> tuple[bool, str]:
        """Validate and update voucher expiration status."""
        if voucher.estado == "cancelado":
            return True, "Voucher cancelado"

        if date.today() > voucher.fecha_vencimiento:
            with transaction.atomic():
                # Re-fetch con lock para evitar race condition entre procesos concurrentes
                locked = Voucher.objects.select_for_update().get(pk=voucher.pk)
                if locked.estado != "vencido":
                    locked.estado = "vencido"
                    locked.save(update_fields=["estado", "fecha_modificacion"])
                    # Sincronizar el objeto recibido para que el caller vea el estado actualizado
                    voucher.estado = "vencido"

                    try:
                        admin_user = User.objects.filter(is_staff=True).first()
                        if admin_user:
                            VoucherLog.objects.create(
                                voucher=locked,
                                tipo_evento="vencimiento",
                                cantidad_afectada=0,
                                usuario=admin_user,
                                detalles={"fecha_vencimiento": str(locked.fecha_vencimiento)},
                            )
                    except Exception as e:
                        logger.warning(f"Error logging voucher expiration: {e}")

                    logger.info(f"Voucher {locked.id} expirado")

            return False, "Voucher vencido"

        return True, "Voucher vigente"

    @staticmethod
    def obtener_estado_actual(voucher: Voucher) -> dict:
        """Get current state of a voucher."""
        valid, mensaje = VoucherService.validar_vencimiento(voucher)

        dias_para_vencer = (voucher.fecha_vencimiento - date.today()).days

        return {
            "voucher_id": voucher.id,
            "ciudadano": str(voucher.ciudadano),
            "programa": str(voucher.programa),
            "cantidad_inicial": voucher.cantidad_inicial,
            "cantidad_usada": voucher.cantidad_usada,
            "cantidad_disponible": voucher.cantidad_disponible,
            "porcentaje_uso": (
                (voucher.cantidad_usada / voucher.cantidad_inicial * 100)
                if voucher.cantidad_inicial > 0
                else 0
            ),
            "estado": voucher.estado,
            "fecha_vencimiento": str(voucher.fecha_vencimiento),
            "dias_para_vencer": dias_para_vencer,
            "vigente": valid,
        }

    @staticmethod
    def buscar_vouchers(ciudadano_id: int = None, estado: str = None):
        """Search vouchers by criteria."""
        queryset = Voucher.objects.select_related(
            "ciudadano", "programa"
        ).order_by("-fecha_asignacion")

        if ciudadano_id:
            queryset = queryset.filter(ciudadano_id=ciudadano_id)
        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset

    @staticmethod
    def obtener_vouchers_por_vencer(dias: int = 7):
        """Get vouchers expiring in the next N days."""
        desde = date.today()
        hasta = desde + timedelta(days=dias)

        return Voucher.objects.filter(
            fecha_vencimiento__range=[desde, hasta],
            estado__in=["activo", "agotado"],
        ).select_related("ciudadano", "programa")

    @staticmethod
    def procesar_recarga_automatica(programa_id: int = None, cantidad: int = 50) -> dict:
        """
        Process automatic reload of vouchers.
        Used by management command and cron jobs.
        """
        # Get system user for logging
        sistema_user = User.objects.filter(username="sistema").first()
        if not sistema_user:
            sistema_user = User.objects.filter(is_superuser=True).first()
        if not sistema_user:
            logger.error("No system user found for automatic reload")
            return {"success": False, "reloaded": 0, "error": "No system user"}

        # Get vouchers to reload
        query = Voucher.objects.filter(
            estado__in=["activo", "agotado"],
            fecha_vencimiento__gte=date.today(),
        )

        if programa_id:
            query = query.filter(programa_id=programa_id)

        reloaded = 0
        errors = []

        with transaction.atomic():
            for voucher in query.select_for_update():
                try:
                    VoucherService.recargar_voucher(
                        voucher=voucher,
                        cantidad=cantidad,
                        motivo="automatica",
                        usuario=sistema_user,
                    )
                    reloaded += 1
                except Exception as e:
                    logger.exception(f"Error reloading voucher {voucher.id}: {e}")
                    errors.append(str(e))

        return {
            "success": len(errors) == 0,
            "reloaded": reloaded,
            "errors": errors,
        }
