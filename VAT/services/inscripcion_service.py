from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction

from VAT.models import Inscripcion, Voucher
from VAT.services.voucher_service.impl import VoucherService

User = get_user_model()

# Estados de inscripción que se consideran "activos" y bloquean una nueva inscripción
# cuando inscripcion_unica_activa está habilitado en la parametría del voucher.
ESTADOS_INSCRIPCION_ACTIVA = ("pre_inscripta", "inscripta", "validada_presencial")


class InscripcionService:
    """Orquesta altas de inscripción con validaciones de voucher."""

    @staticmethod
    def _resolver_usuario_auditoria(usuario):
        if getattr(usuario, "is_authenticated", False):
            return usuario
        return User.objects.filter(is_staff=True).first() or User.objects.filter(
            is_superuser=True
        ).first()

    @staticmethod
    def validar_inscripcion_unica(ciudadano, programa) -> tuple[bool, str]:
        """
        Verifica si el ciudadano puede inscribirse según la regla de inscripción
        única activa configurada en la parametría del voucher.

        Retorna (True, "") si puede inscribirse, o (False, mensaje) si no.
        """
        voucher = (
            Voucher.objects.select_related("parametria")
            .filter(
                ciudadano=ciudadano,
                programa=programa,
                estado="activo",
                parametria__isnull=False,
            )
            .order_by("fecha_vencimiento")
            .first()
        )

        if not voucher or not voucher.parametria:
            return True, ""

        if not voucher.parametria.inscripcion_unica_activa:
            return True, ""

        inscripcion_activa = (
            Inscripcion.objects.select_related("comision")
            .filter(
                ciudadano=ciudadano,
                programa=programa,
                estado__in=ESTADOS_INSCRIPCION_ACTIVA,
            )
            .first()
        )

        if inscripcion_activa:
            return False, (
                f"Ya tenés una inscripción activa en "
                f'"{inscripcion_activa.comision.nombre}" '
                f"(estado: {inscripcion_activa.get_estado_display()}). "
                f"Debés completarla o abandonarla antes de inscribirte en otro curso."
            )

        return True, ""

    @staticmethod
    def crear_inscripcion(
        *,
        ciudadano,
        comision,
        programa=None,
        estado="inscripta",
        origen_canal="api",
        observaciones="",
        usuario=None,
    ) -> Inscripcion:
        oferta = comision.oferta
        programa = programa or oferta.programa

        if programa.id != oferta.programa_id:
            raise ValueError(
                "La inscripción debe usar el mismo programa de la oferta institucional."
            )

        # Validar inscripción única activa (solo si usa voucher)
        if oferta.usa_voucher:
            puede, motivo = InscripcionService.validar_inscripcion_unica(
                ciudadano, programa
            )
            if not puede:
                raise ValueError(motivo)

        with transaction.atomic():
            inscripcion = Inscripcion.objects.create(
                ciudadano=ciudadano,
                comision=comision,
                programa=programa,
                estado=estado,
                origen_canal=origen_canal,
                observaciones=observaciones or "",
            )

            if oferta.usa_voucher:
                voucher = (
                    Voucher.objects.filter(
                        ciudadano=ciudadano,
                        programa=oferta.programa,
                        estado="activo",
                    )
                    .order_by("fecha_vencimiento")
                    .first()
                )
                if not voucher:
                    raise ValueError(
                        f"{ciudadano} no tiene voucher activo para el programa {oferta.programa}."
                    )

                cantidad_debito = int(Decimal(oferta.costo or 0))
                usuario_auditoria = InscripcionService._resolver_usuario_auditoria(
                    usuario
                )
                if usuario_auditoria is None:
                    raise ValueError(
                        "No hay usuario disponible para registrar la auditoría del voucher."
                    )
                ok, msg = VoucherService.debitar_voucher(
                    voucher=voucher,
                    cantidad=cantidad_debito,
                    usuario=usuario_auditoria,
                    detalles={
                        "inscripcion_id": inscripcion.id,
                        "comision_id": inscripcion.comision_id,
                        "comision": str(inscripcion.comision),
                        "origen": "inscripcion_comision",
                    },
                )
                if not ok:
                    raise ValueError(msg)

                inscripcion._voucher_debito = cantidad_debito
                inscripcion._voucher_saldo = voucher.cantidad_disponible

        return inscripcion
