from decimal import Decimal
from contextlib import nullcontext

from django.contrib.auth import get_user_model
from django.db import transaction

from VAT.models import Inscripcion, InscripcionOferta, Voucher, VoucherUso
from VAT.services.voucher_service import VoucherService

User = get_user_model()

# Estados de inscripción que se consideran "activos" y bloquean una nueva inscripción
# cuando inscripcion_unica_activa está habilitado en la parametría del voucher.
ESTADOS_INSCRIPCION_ACTIVA = ("pre_inscripta", "inscripta", "validada_presencial")


class InscripcionService:
    """Orquesta altas de inscripción con validaciones de voucher."""

    @staticmethod
    def _normalizar_motivos(*motivos) -> list[str]:
        return [motivo for motivo in motivos if motivo]

    @staticmethod
    def _resolve_lookup_id(instance_or_id):
        if hasattr(instance_or_id, "pk") and getattr(instance_or_id, "pk") is not None:
            return instance_or_id.pk
        if hasattr(instance_or_id, "id"):
            return instance_or_id.id
        return instance_or_id

    @staticmethod
    def _atomic_if_persistent(*instances):
        if any(
            hasattr(instance, "_meta") for instance in instances if instance is not None
        ):
            return transaction.atomic()
        return nullcontext()

    @staticmethod
    def _uses_persistent_models(*instances):
        return any(
            hasattr(instance, "_meta") for instance in instances if instance is not None
        )

    @staticmethod
    def _resolver_usuario_auditoria(usuario):
        if getattr(usuario, "is_authenticated", False):
            return usuario
        return (
            User.objects.filter(is_staff=True).first()
            or User.objects.filter(is_superuser=True).first()
        )

    @staticmethod
    def _resolver_cantidad_debito(costo) -> int:
        monto = Decimal(costo or 0)
        if monto != monto.to_integral_value():
            raise ValueError(
                "El costo de la oferta debe ser un numero entero de creditos "
                "para poder debitarse del voucher."
            )
        return int(monto)

    @staticmethod
    def _obtener_ids_parametrias_habilitadas(oferta) -> list[int]:
        voucher_parametrias = getattr(oferta, "voucher_parametrias", None)
        if hasattr(voucher_parametrias, "values_list"):
            return list(voucher_parametrias.values_list("id", flat=True))
        return []

    @staticmethod
    def _obtener_vouchers_candidatos(
        *, ciudadano, programa, ids_parametrias_habilitadas
    ):
        vouchers_qs = Voucher.objects.select_related("parametria").filter(
            ciudadano_id=InscripcionService._resolve_lookup_id(ciudadano),
            programa_id=InscripcionService._resolve_lookup_id(programa),
            estado="activo",
        )
        if ids_parametrias_habilitadas:
            vouchers_qs = vouchers_qs.filter(
                parametria_id__in=ids_parametrias_habilitadas
            )
        return vouchers_qs.order_by("fecha_vencimiento", "id")

    @staticmethod
    def _resolver_unidad_formativa(comision):
        if getattr(comision, "oferta_id", None):
            return comision.oferta, "comision"
        return comision.curso, "comision_curso"

    @staticmethod
    def _resolver_lookup_comision(comision):
        _, relation = InscripcionService._resolver_unidad_formativa(comision)
        return {relation: comision}

    @staticmethod
    def _resolver_nombre_comision(inscripcion):
        entidad = (
            inscripcion.comision
            if inscripcion.comision_id
            else inscripcion.comision_curso
        )
        return entidad.nombre if entidad else "sin comisión"

    @staticmethod
    def _debitar_voucher_para_oferta(  # pylint: disable=too-many-arguments
        *, oferta, ciudadano, cantidad_debito, usuario, detalles
    ):
        ids_parametrias_habilitadas = (
            InscripcionService._obtener_ids_parametrias_habilitadas(oferta)
        )
        vouchers_qs = InscripcionService._obtener_vouchers_candidatos(
            ciudadano=ciudadano,
            programa=oferta.programa,
            ids_parametrias_habilitadas=ids_parametrias_habilitadas,
        )

        if not vouchers_qs.exists():
            raise ValueError(
                f"{ciudadano} no tiene voucher activo para el programa {oferta.programa}."
            )

        usuario_auditoria = InscripcionService._resolver_usuario_auditoria(usuario)
        if usuario_auditoria is None:
            raise ValueError(
                "No hay usuario disponible para registrar la auditoría del voucher."
            )

        ultimo_error = None
        for voucher in vouchers_qs:
            ok, msg = VoucherService.debitar_voucher(
                voucher=voucher,
                cantidad=cantidad_debito,
                usuario=usuario_auditoria,
                detalles=detalles,
            )
            if ok:
                return voucher
            ultimo_error = msg

        if ultimo_error:
            raise ValueError(ultimo_error)
        raise ValueError(
            f"{ciudadano} no tiene voucher válido para el programa {oferta.programa}."
        )

    @staticmethod
    def validar_inscripcion_unica(ciudadano, programa) -> tuple[bool, str]:
        """
        Verifica si el ciudadano puede inscribirse según la regla de inscripción
        única activa configurada en la parametría del voucher.

        Retorna (True, "") si puede inscribirse, o (False, mensaje) si no.
        """
        try:
            voucher = (
                Voucher.objects.select_related("parametria")
                .filter(
                    ciudadano_id=InscripcionService._resolve_lookup_id(ciudadano),
                    programa_id=InscripcionService._resolve_lookup_id(programa),
                    estado="activo",
                    parametria__isnull=False,
                )
                .order_by("fecha_vencimiento")
                .first()
            )
        except RuntimeError:
            if not InscripcionService._uses_persistent_models(ciudadano, programa):
                return True, ""
            raise

        if not voucher or not voucher.parametria:
            return True, ""

        if not voucher.parametria.inscripcion_unica_activa:
            return True, ""

        inscripcion_activa = (
            Inscripcion.objects.select_related("comision", "comision_curso__curso")
            .filter(
                ciudadano_id=InscripcionService._resolve_lookup_id(ciudadano),
                programa_id=InscripcionService._resolve_lookup_id(programa),
                estado__in=ESTADOS_INSCRIPCION_ACTIVA,
            )
            .first()
        )

        if inscripcion_activa:
            return False, (
                f"Ya tenés una inscripción activa en "
                f'"{InscripcionService._resolver_nombre_comision(inscripcion_activa)}" '
                f"(estado: {inscripcion_activa.get_estado_display()}). "
                f"Debés completarla o abandonarla antes de inscribirte en otro curso."
            )

        return True, ""

    @staticmethod
    def prevalidar_inscripcion(*, ciudadano, comision, programa=None) -> dict:
        unidad_formativa, _ = InscripcionService._resolver_unidad_formativa(comision)
        programa = programa or unidad_formativa.programa
        total_inscriptos = comision.inscripciones.count()
        cupos_disponibles = max((comision.cupo_total or 0) - total_inscriptos, 0)
        motivos: list[str] = []

        if unidad_formativa.estado != "activo":
            motivos.append("El curso no se encuentra activo para nuevas inscripciones.")

        if comision.estado != "activa":
            motivos.append(
                "La comisión no se encuentra activa para nuevas inscripciones."
            )

        if cupos_disponibles <= 0:
            motivos.append("La comisión no tiene cupos disponibles.")

        if programa is None:
            motivos.append(
                "La comisión debe tener un programa configurado para poder inscribir ciudadanos."
            )

        if Inscripcion.objects.filter(
            ciudadano=ciudadano,
            **InscripcionService._resolver_lookup_comision(comision),
        ).exists():
            motivos.append("El ciudadano ya está inscripto en esta comisión.")

        voucher_info = {
            "requerido": bool(unidad_formativa.usa_voucher),
            "programa_id": programa.id if programa else None,
            "programa_nombre": programa.nombre if programa else None,
            "parametrias_habilitadas": (
                InscripcionService._obtener_ids_parametrias_habilitadas(unidad_formativa)
                if unidad_formativa.usa_voucher
                else []
            ),
            "voucher_id": None,
            "parametria_id": None,
            "saldo_actual": None,
            "credito_requerido": None,
            "saldo_post_inscripcion": None,
        }

        if unidad_formativa.usa_voucher and programa is not None:
            credito_requerido = InscripcionService._resolver_cantidad_debito(
                getattr(unidad_formativa, "costo", None)
                or getattr(unidad_formativa, "costo_creditos", 0)
            )
            voucher_info["credito_requerido"] = credito_requerido

            vouchers_qs = InscripcionService._obtener_vouchers_candidatos(
                ciudadano=ciudadano,
                programa=programa,
                ids_parametrias_habilitadas=voucher_info["parametrias_habilitadas"],
            )
            voucher = vouchers_qs.first()

            if voucher is None:
                motivos.append(
                    f"{ciudadano} no tiene voucher activo para el programa {programa}."
                )
            else:
                voucher_info.update(
                    {
                        "voucher_id": voucher.id,
                        "parametria_id": voucher.parametria_id,
                        "saldo_actual": voucher.cantidad_disponible,
                        "saldo_post_inscripcion": (
                            voucher.cantidad_disponible - credito_requerido
                        ),
                    }
                )
                if voucher.cantidad_disponible < credito_requerido:
                    motivos.append(
                        f"Créditos insuficientes. Disponible: {voucher.cantidad_disponible}"
                    )

            puede, motivo = InscripcionService.validar_inscripcion_unica(
                ciudadano,
                programa,
            )
            motivos.extend(InscripcionService._normalizar_motivos(motivo if not puede else ""))

        return {
            "puede_inscribirse": not motivos,
            "motivos": motivos,
            "ciudadano": {
                "id": ciudadano.id,
                "documento": ciudadano.documento,
                "nombre": ciudadano.nombre_completo,
            },
            "comision": {
                "id": comision.id,
                "codigo_comision": comision.codigo_comision,
                "nombre": comision.nombre,
                "estado": comision.estado,
                "curso_id": comision.curso_id,
                "curso_nombre": comision.curso.nombre,
                "centro_id": comision.curso.centro_id,
                "centro_nombre": comision.curso.centro.nombre,
                "programa_id": programa.id if programa else None,
                "programa_nombre": programa.nombre if programa else None,
                "usa_voucher": unidad_formativa.usa_voucher,
                "cupo_total": comision.cupo_total,
                "cupos_disponibles": cupos_disponibles,
                "costo": getattr(unidad_formativa, "costo", None)
                or getattr(unidad_formativa, "costo_creditos", 0),
            },
            "voucher": voucher_info,
        }

    @staticmethod
    def crear_inscripcion(  # pylint: disable=too-many-arguments
        *,
        ciudadano,
        comision,
        programa=None,
        estado="inscripta",
        origen_canal="api",
        observaciones="",
        usuario=None,
    ) -> Inscripcion:
        unidad_formativa, relation = InscripcionService._resolver_unidad_formativa(
            comision
        )
        programa = programa or unidad_formativa.programa

        if programa is None:
            raise ValueError(
                "La comisión debe tener un programa configurado para poder inscribir ciudadanos."
            )

        if unidad_formativa.programa_id and programa.id != unidad_formativa.programa_id:
            raise ValueError(
                "La inscripción debe usar el mismo programa configurado en la comisión."
            )

        if Inscripcion.objects.filter(
            ciudadano=ciudadano,
            **InscripcionService._resolver_lookup_comision(comision),
        ).exists():
            raise ValueError("El ciudadano ya está inscripto en esta comisión.")

        # Validar inscripción única activa (solo si usa voucher)
        if unidad_formativa.usa_voucher:
            puede, motivo = InscripcionService.validar_inscripcion_unica(
                ciudadano, programa
            )
            if not puede:
                raise ValueError(motivo)

        with InscripcionService._atomic_if_persistent(ciudadano, comision, programa):
            inscripcion_kwargs = {
                "ciudadano": ciudadano,
                "programa": programa,
                "estado": estado,
                "origen_canal": origen_canal,
                "observaciones": observaciones or "",
                relation: comision,
            }
            inscripcion = Inscripcion.objects.create(**inscripcion_kwargs)

            if unidad_formativa.usa_voucher:
                cantidad_debito = InscripcionService._resolver_cantidad_debito(
                    getattr(unidad_formativa, "costo", None)
                    or getattr(unidad_formativa, "costo_creditos", 0)
                )
                voucher = InscripcionService._debitar_voucher_para_oferta(
                    oferta=unidad_formativa,
                    ciudadano=ciudadano,
                    cantidad_debito=cantidad_debito,
                    usuario=usuario,
                    detalles={
                        "inscripcion_id": inscripcion.id,
                        "comision_id": inscripcion.comision_id,
                        "comision_curso_id": inscripcion.comision_curso_id,
                        "comision": str(inscripcion.entidad_comision),
                        "origen": f"inscripcion_{relation}",
                    },
                )

                inscripcion.voucher_debito = cantidad_debito
                inscripcion.voucher_saldo = voucher.cantidad_disponible

        return inscripcion

    @staticmethod
    def crear_inscripcion_oferta(
        *,
        ciudadano,
        comision,
        estado="inscrito",
        inscrito_por=None,
    ):
        oferta = comision.oferta
        usuario_inscribe = InscripcionService._resolver_usuario_auditoria(inscrito_por)
        if usuario_inscribe is None:
            raise ValueError("No hay usuario disponible para registrar la inscripción.")

        with InscripcionService._atomic_if_persistent(ciudadano, comision, oferta):
            inscripcion_oferta = InscripcionOferta.objects.create(
                oferta=comision,
                ciudadano=ciudadano,
                estado=estado,
                inscrito_por=usuario_inscribe,
            )

            if oferta.usa_voucher:
                cantidad_debito = InscripcionService._resolver_cantidad_debito(
                    oferta.costo
                )
                voucher = InscripcionService._debitar_voucher_para_oferta(
                    oferta=oferta,
                    ciudadano=ciudadano,
                    cantidad_debito=cantidad_debito,
                    usuario=usuario_inscribe,
                    detalles={
                        "inscripcion_oferta_id": inscripcion_oferta.id,
                        "comision_id": comision.id,
                        "comision": str(comision),
                        "origen": "inscripcion_oferta",
                    },
                )

                VoucherUso.objects.create(
                    voucher=voucher,
                    inscripcion_oferta=inscripcion_oferta,
                    cantidad_usada=cantidad_debito,
                )

                inscripcion_oferta.voucher_debito = cantidad_debito
                inscripcion_oferta.voucher_saldo = voucher.cantidad_disponible

        return inscripcion_oferta
