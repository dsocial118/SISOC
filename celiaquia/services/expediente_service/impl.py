import logging
import json
from functools import lru_cache
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from celiaquia.models import EstadoExpediente, Expediente, ExpedienteEstadoHistorial
from celiaquia.services.importacion_service import ImportacionService
from celiaquia.services.legajo_service import LegajoService

logger = logging.getLogger("django")
User = get_user_model()


@lru_cache(maxsize=16)
def _estado_id(nombre: str) -> int:
    return EstadoExpediente.objects.get_or_create(nombre=nombre)[0].pk


def _set_estado(
    expediente: Expediente, nombre: str, usuario=None, observaciones=None
) -> None:
    """Actualiza el estado del expediente y el usuario modificador."""

    expediente.estado_id = _estado_id(nombre)
    update_fields = ["estado"]
    if usuario is not None:
        expediente.usuario_modificador = usuario
        update_fields.append("usuario_modificador")
    expediente.save(update_fields=update_fields)

    if observaciones and getattr(expediente, "pk", None):
        historial_actual = (
            ExpedienteEstadoHistorial.objects.filter(
                expediente=expediente,
                estado_nuevo_id=expediente.estado_id,
            )
            .order_by("-fecha")
            .first()
        )
        if historial_actual:
            historial_actual.observaciones = observaciones
            historial_actual.save(update_fields=["observaciones"])


def _build_resumen_importacion_alerta(*, creados_total=0, errores_actuales=0):
    resumen_lineas = [
        f"Importacion procesada. Se crearon {creados_total} legajos y el expediente paso a EN ESPERA."
    ]
    if errores_actuales:
        resumen_lineas.append(f"Errores detectados: {errores_actuales}.")
    return "\n".join(resumen_lineas)


def _build_excluidos_importacion_alerta(excluidos):
    excluidos_lineas = []
    if excluidos:
        cantidad = len(excluidos)
        sujeto = "No se creó 1 legajo" if cantidad == 1 else f"No se crearon {cantidad} legajos"
        predicado = (
            "porque pertenece a otro expediente."
            if cantidad == 1
            else "porque pertenecen a otro expediente."
        )
        excluidos_lineas.append(
            f"{sujeto} {predicado}"
        )
        for item in excluidos[:10]:
            if not isinstance(item, dict):
                excluidos_lineas.append(str(item))
                continue
            documento = item.get("documento", "-")
            apellido = item.get("apellido", "-")
            nombre = item.get("nombre", "-")
            estado = (
                item.get("estado_programa")
                or item.get("estado_legajo_origen")
                or item.get("motivo")
                or "-"
            )
            expediente_origen = item.get("expediente_origen_id", "-")
            excluidos_lineas.append(
                f"- Documento {documento} - {apellido}, {nombre} - Estado legajo: {estado} - Exp #{expediente_origen}"
            )
        restantes = len(excluidos) - 10
        if restantes > 0:
            excluidos_lineas.append(f"... y {restantes} mas.")
    return "\n".join(excluidos_lineas)


def _build_observaciones_importacion(result: dict) -> str:
    creados = result.get("validos", 0)
    errores = result.get("errores", 0)
    excluidos = result.get("excluidos") or []

    resumen_lineas = [
        f"Importacion procesada. Se crearon {creados} legajos y el expediente paso a EN ESPERA."
    ]
    if errores:
        resumen_lineas.append(f"Errores detectados: {errores}.")

    excluidos_lineas = []
    if excluidos:
        cantidad = len(excluidos)
        sujeto = "No se creó 1 legajo" if cantidad == 1 else f"No se crearon {cantidad} legajos"
        predicado = (
            "porque pertenece a otro expediente."
            if cantidad == 1
            else "porque pertenecen a otro expediente."
        )
        excluidos_lineas.append(
            f"{sujeto} {predicado}"
        )
        for item in excluidos[:10]:
            if not isinstance(item, dict):
                excluidos_lineas.append(str(item))
                continue
            documento = item.get("documento", "-")
            apellido = item.get("apellido", "-")
            nombre = item.get("nombre", "-")
            estado = (
                item.get("estado_programa")
                or item.get("estado_legajo_origen")
                or item.get("motivo")
                or "-"
            )
            expediente_origen = item.get("expediente_origen_id", "-")
            excluidos_lineas.append(
                f"- Documento {documento} - {apellido}, {nombre} - Estado legajo: {estado} - Exp #{expediente_origen}"
            )
        restantes = len(excluidos) - 10
        if restantes > 0:
            excluidos_lineas.append(f"... y {restantes} mas.")

    return json.dumps(
        {
            "resumen": _build_resumen_importacion_alerta(
                creados_total=creados,
                errores_actuales=errores,
            ),
            "excluidos": _build_excluidos_importacion_alerta(excluidos),
            "excluidos_detalle": excluidos,
            "tiene_errores": bool(errores),
            "creados_total": creados,
            "errores_actuales": errores,
        }
    )


class ExpedienteService:
    @staticmethod
    @transaction.atomic
    def create_expediente(usuario_provincia, datos_metadatos, excel_masivo):
        create_kwargs = dict(
            usuario_provincia=usuario_provincia,
            estado_id=_estado_id("CREADO"),
            numero_expediente=datos_metadatos.get("numero_expediente") or None,
            observaciones=datos_metadatos.get("observaciones", ""),
            excel_masivo=excel_masivo,
        )
        try:
            if hasattr(Expediente, "provincia_id"):
                create_kwargs["provincia_id"] = getattr(
                    getattr(usuario_provincia, "profile", None), "provincia_id", None
                )
        except Exception:
            pass

        expediente = Expediente.objects.create(**create_kwargs)
        logger.info(
            "Expediente creado por usuario_provincia=%s id=%s",
            usuario_provincia.username,
            expediente.pk,
        )
        return expediente

    @staticmethod
    @transaction.atomic
    def procesar_expediente(expediente: Expediente, usuario):
        if not expediente.excel_masivo:
            raise ValidationError("No hay archivo Excel cargado para procesar.")

        result = ImportacionService.importar_legajos_desde_excel(
            expediente, expediente.excel_masivo, usuario
        )
        _set_estado(expediente, "PROCESADO", usuario)
        logger.info(
            "Expediente %s procesado: legajos_creados=%s errores=%s excluidos=%s",
            expediente.pk,
            result.get("validos", 0),
            result.get("errores", 0),
            result.get("excluidos_count", 0),
        )

        _set_estado(
            expediente,
            "EN_ESPERA",
            usuario,
            observaciones=_build_observaciones_importacion(result),
        )
        logger.info("Expediente %s pasó a estado EN_ESPERA", expediente.pk)

        return {
            "creados": result.get("validos", 0),
            "errores": result.get("errores", 0),
            "excluidos": result.get("excluidos_count", 0),  # <-- NUEVO
            "excluidos_detalle": result.get("excluidos", []),  # <-- NUEVO
        }

    @staticmethod
    @transaction.atomic
    def confirmar_envio(expediente: Expediente, usuario):
        if expediente.estado.nombre != "EN_ESPERA":
            raise ValidationError(
                f"El expediente no está en estado EN_ESPERA. Estado actual: {expediente.estado.nombre}"
            )

        legajos_qs = expediente.expediente_ciudadanos
        if hasattr(legajos_qs, "select_related"):
            legajos_qs = legajos_qs.select_related("ciudadano")

        responsables_ids = LegajoService.obtener_ids_responsables_expediente(
            expediente, legajos_qs
        )
        for leg in legajos_qs.all():
            if hasattr(leg, "archivos_ok"):
                leg.archivos_ok = LegajoService.tiene_archivos_requeridos(
                    leg, responsables_ids
                )
                leg.save(update_fields=["archivos_ok"])

        if not LegajoService.all_legajos_loaded(expediente):
            raise ValidationError(
                "Debes subir toda la documentacion obligatoria de cada legajo antes de confirmar."
            )

        _set_estado(expediente, "CONFIRMACION_DE_ENVIO", usuario)
        total = expediente.expediente_ciudadanos.count()
        logger.info(
            "Expediente %s confirmado (ENVÍO). Legajos=%s", expediente.pk, total
        )
        return {"validos": total, "errores": 0}

    @staticmethod
    @transaction.atomic
    def asignar_tecnico(expediente: Expediente, tecnico, usuario):
        if isinstance(tecnico, int):
            tecnico = User.objects.get(pk=tecnico)

        from celiaquia.models import (
            AsignacionTecnico,
        )  # pylint: disable=import-outside-toplevel

        asignacion, _ = AsignacionTecnico.objects.get_or_create(
            expediente=expediente, tecnico=tecnico
        )

        _set_estado(expediente, "ASIGNADO", usuario)
        logger.info(
            "Técnico %s asignado al expediente %s", tecnico.username, expediente.pk
        )
        return expediente
