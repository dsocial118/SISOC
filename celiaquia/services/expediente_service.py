import logging
from functools import lru_cache
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from celiaquia.models import EstadoExpediente, Expediente
from celiaquia.services.importacion_service import ImportacionService
from celiaquia.services.legajo_service import LegajoService

logger = logging.getLogger("django")
User = get_user_model()


@lru_cache(maxsize=16)
def _estado_id(nombre: str) -> int:
    return EstadoExpediente.objects.get_or_create(nombre=nombre)[0].pk


def _set_estado(expediente: Expediente, nombre: str, usuario=None) -> None:
    """Actualiza el estado del expediente y el usuario modificador."""

    expediente.estado_id = _estado_id(nombre)
    update_fields = ["estado"]
    if usuario is not None:
        expediente.usuario_modificador = usuario
        update_fields.append("usuario_modificador")
    expediente.save(update_fields=update_fields)


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

        _set_estado(expediente, "EN_ESPERA", usuario)
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
        try:
            if expediente.estado.nombre != "EN_ESPERA":
                raise ValidationError("El expediente no está en EN_ESPERA.")
        except AttributeError:
            pass

        if not LegajoService.all_legajos_loaded(expediente):
            raise ValidationError(
                "Debes subir un archivo para cada legajo antes de confirmar."
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
