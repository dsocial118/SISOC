import json
import logging
import time
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from celiaquia.models import ExpedienteCiudadano
from centrodefamilia.services.consulta_renaper import consultar_datos_renaper
from iam.services import user_has_permission_code

logger = logging.getLogger(__name__)

ROLE_COORDINADOR_CELIAQUIA_PERMISSION = "auth.role_coordinadorceliaquia"
ROLE_TECNICO_CELIAQUIA_PERMISSION = "auth.role_tecnicoceliaquia"

RENAPER_TRANSIENT_ERROR_TYPES = {
    "timeout",
    "remote_error",
    "auth_error",
    "invalid_response",
    "unexpected_error",
}
RENAPER_REMOTE_UNAVAILABLE_MESSAGE = (
    "No pudimos validar con RENAPER en este momento. "
    "Por favor, intentá nuevamente en unos minutos."
)
RENAPER_INVALID_RESPONSE_MESSAGE = (
    "RENAPER devolvió una respuesta inválida y no pudimos completar la validación. "
    "Intentá nuevamente más tarde."
)
RENAPER_NO_MATCH_MESSAGE = (
    "RENAPER no pudo validar los datos ingresados. "
    "Verificá el DNI y el sexo registrados."
)


def _truncate(value, length=500):
    if isinstance(value, str) and len(value) > length:
        return f"{value[:length]}…"
    return value


def _build_raw_response_excerpt(raw_response):
    if raw_response in (None, ""):
        return None

    if isinstance(raw_response, (dict, list, tuple)):
        try:
            raw_response = json.dumps(raw_response, ensure_ascii=True)
        except (TypeError, ValueError):
            raw_response = str(raw_response)

    return _truncate(str(raw_response))


def _build_log_data(
    user,
    legajo=None,
    ciudadano=None,
    documento_original=None,
    documento_consulta=None,
    sexo_renaper=None,
):
    data = {
        "user_id": getattr(user, "id", None),
        "username": getattr(user, "get_username", lambda: None)(),
        "legajo_id": getattr(legajo, "pk", None),
        "expediente_id": getattr(legajo, "expediente_id", None),
        "ciudadano_id": getattr(ciudadano, "id", None),
        "documento_original": documento_original,
        "documento_consulta": documento_consulta,
        "sexo_consulta": sexo_renaper,
        "sexo_registrado": getattr(getattr(ciudadano, "sexo", None), "sexo", None),
    }
    return {k: v for k, v in data.items() if v is not None}


def _has_permission(user, permission_code: str) -> bool:
    return user_has_permission_code(user, permission_code)


def _mapear_sexo_para_renaper(ciudadano):
    sexo_map = {"Masculino": "M", "Femenino": "F", "X": "X"}
    sexo_valor = (getattr(getattr(ciudadano, "sexo", None), "sexo", "") or "").strip()
    return sexo_map.get(sexo_valor)


def _normalizar_documento_para_renaper(documento_original):
    if len(documento_original) == 11:
        return documento_original[2:10]
    return documento_original


def _es_dni_valido_para_renaper(documento_consulta):
    return documento_consulta.isdigit() and len(documento_consulta) == 8


def _resolver_ciudad_provincia(ciudadano):
    localidad = getattr(ciudadano, "localidad", None)
    if localidad:
        localidad_nombre = getattr(localidad, "nombre", localidad)
        if localidad_nombre:
            return str(localidad_nombre).title()

    return (getattr(ciudadano, "ciudad", "") or "").title()


def _build_datos_provincia(ciudadano, documento_consulta):
    fecha_nacimiento = getattr(ciudadano, "fecha_nacimiento", None)
    altura = getattr(ciudadano, "altura", None)
    provincia = getattr(ciudadano, "provincia", None)
    codigo_postal = getattr(ciudadano, "codigo_postal", None)
    return {
        "documento": documento_consulta,
        "nombre": (getattr(ciudadano, "nombre", "") or "").title(),
        "apellido": (getattr(ciudadano, "apellido", "") or "").title(),
        "fecha_nacimiento": (
            fecha_nacimiento.strftime("%d/%m/%Y") if fecha_nacimiento else None
        ),
        "sexo": getattr(getattr(ciudadano, "sexo", None), "sexo", None),
        "calle": (getattr(ciudadano, "calle", "") or "").title(),
        "altura": str(altura) if altura else "",
        "piso_departamento": (
            getattr(ciudadano, "piso_departamento", "") or ""
        ).title(),
        "ciudad": _resolver_ciudad_provincia(ciudadano),
        "provincia": getattr(provincia, "nombre", None),
        "codigo_postal": str(codigo_postal) if codigo_postal else "",
    }


def _resolver_sexo_y_consulta_renaper(documento_consulta, sexo_renaper):
    if sexo_renaper:
        return sexo_renaper, None

    for sexo_test in ["M", "F"]:
        resultado_test = _consultar_datos_renaper_con_reintentos(
            documento_consulta, sexo_test
        )
        if resultado_test.get("success"):
            return sexo_test, resultado_test

    return None, None


def _get_renaper_retry_config():
    max_retries = getattr(settings, "RENAPER_VALIDACION_MAX_RETRIES", 1)
    backoff_seconds = getattr(settings, "RENAPER_VALIDACION_BACKOFF_SECONDS", 0.0)

    try:
        max_retries = max(int(max_retries or 1), 1)
    except (TypeError, ValueError):
        max_retries = 1

    try:
        backoff_seconds = max(float(backoff_seconds or 0), 0.0)
    except (TypeError, ValueError):
        backoff_seconds = 0.0

    return max_retries, backoff_seconds


def _es_error_reintentable(error_type):
    return error_type in RENAPER_TRANSIENT_ERROR_TYPES


def _enriquecer_resultado_renaper(resultado, retry_attempt, max_retries):
    resultado_normalizado = dict(resultado or {})
    if not resultado_normalizado.get("success", False):
        resultado_normalizado.setdefault(
            "error", "Error desconocido al consultar Renaper"
        )
        resultado_normalizado.setdefault("error_type", "unexpected_error")

    resultado_normalizado["retry_attempt"] = retry_attempt
    resultado_normalizado["max_retries"] = max_retries
    return resultado_normalizado


def _build_error_log_data(log_data, resultado_renaper, stage="response"):
    return {
        **log_data,
        "stage": stage,
        "error": resultado_renaper.get("error"),
        "error_type": resultado_renaper.get("error_type"),
        "retry_attempt": resultado_renaper.get("retry_attempt"),
        "max_retries": resultado_renaper.get("max_retries"),
        "raw_response_excerpt": _build_raw_response_excerpt(
            resultado_renaper.get("raw_response")
        ),
    }


def _get_error_message(resultado_renaper):
    error_type = resultado_renaper.get("error_type")

    if error_type == "fallecido" or resultado_renaper.get("fallecido"):
        return "La persona figura como fallecida en Renaper"
    if error_type == "invalid_response":
        return RENAPER_INVALID_RESPONSE_MESSAGE
    if error_type == "no_match":
        return RENAPER_NO_MATCH_MESSAGE
    return RENAPER_REMOTE_UNAVAILABLE_MESSAGE


def _consultar_datos_renaper_con_reintentos(documento_consulta, sexo_renaper):
    max_retries, backoff_seconds = _get_renaper_retry_config()
    ultimo_resultado = None

    for intento in range(1, max_retries + 1):
        ultimo_resultado = _enriquecer_resultado_renaper(
            consultar_datos_renaper(documento_consulta, sexo_renaper),
            retry_attempt=intento,
            max_retries=max_retries,
        )
        if ultimo_resultado.get("success"):
            return ultimo_resultado

        if intento >= max_retries or not _es_error_reintentable(
            ultimo_resultado.get("error_type")
        ):
            break

        logger.warning(
            "renaper.validation.retrying_remote_query",
            extra={
                "data": {
                    "documento_consulta": documento_consulta,
                    "sexo_consulta": sexo_renaper,
                    "retry_attempt": intento + 1,
                    "max_retries": max_retries,
                    "error": ultimo_resultado.get("error"),
                    "error_type": ultimo_resultado.get("error_type"),
                    "raw_response_excerpt": _build_raw_response_excerpt(
                        ultimo_resultado.get("raw_response")
                    ),
                }
            },
        )

        if backoff_seconds > 0:
            time.sleep(backoff_seconds * (2 ** (intento - 1)))

    return ultimo_resultado or _enriquecer_resultado_renaper(
        {
            "success": False,
            "error": "Error desconocido al consultar Renaper",
            "error_type": "unexpected_error",
        },
        retry_attempt=max_retries,
        max_retries=max_retries,
    )


def _formatear_fecha_renaper(fecha_renaper):
    if not fecha_renaper:
        return fecha_renaper

    try:
        from datetime import datetime

        if "-" in fecha_renaper and len(fecha_renaper) == 10:
            fecha_obj = datetime.strptime(fecha_renaper, "%Y-%m-%d")
            return fecha_obj.strftime("%d/%m/%Y")
    except Exception:  # pylint: disable=broad-exception-caught
        return fecha_renaper

    return fecha_renaper


def _resolver_provincia_renaper(datos_renaper):
    provincia_valor = datos_renaper.get("provincia")
    if provincia_valor not in (None, ""):
        try:
            from core.models import Provincia

            provincia_obj = Provincia.objects.get(pk=provincia_valor)
            return provincia_obj.nombre
        except (Provincia.DoesNotExist, ValueError, TypeError):
            return "Provincia no encontrada"

    provincia_api = (datos_renaper.get("provincia_api") or "").strip()
    return provincia_api.title() if provincia_api else None


def _formatear_datos_renaper(datos_renaper, sexo_renaper, documento_consulta=None):
    documento_renaper = (
        datos_renaper.get("dni") or datos_renaper.get("documento") or documento_consulta
    )

    datos_renaper_formateados = {
        "documento": str(documento_renaper or ""),
        "nombre": (datos_renaper.get("nombre") or "").title(),
        "apellido": (datos_renaper.get("apellido") or "").title(),
        "fecha_nacimiento": _formatear_fecha_renaper(
            datos_renaper.get("fecha_nacimiento")
        ),
        "sexo": "Masculino" if sexo_renaper == "M" else "Femenino",
        "calle": (datos_renaper.get("calle") or "").title(),
        "altura": str(datos_renaper.get("altura") or ""),
        "piso_departamento": (
            datos_renaper.get("piso_departamento")
            or datos_renaper.get("piso_vivienda")
            or ""
        ).title(),
        "ciudad": (
            datos_renaper.get("ciudad") or datos_renaper.get("localidad_api") or ""
        ).title(),
        "provincia": _resolver_provincia_renaper(datos_renaper),
        "codigo_postal": str(datos_renaper.get("codigo_postal") or ""),
    }

    return datos_renaper_formateados


def _log_respuesta_renaper(log_data, resultado_renaper):
    success = resultado_renaper.get("success", False)
    fallecido = resultado_renaper.get("fallecido")
    response_summary = {
        "success": success,
        "keys": sorted(list(resultado_renaper.keys())),
        "fallecido": fallecido,
    }

    if not success:
        error_type = resultado_renaper.get("error_type")
        log_extra = {"data": _build_error_log_data(log_data, resultado_renaper)}

        if error_type == "no_match":
            logger.info("renaper.validation.no_match", extra=log_extra)
        elif error_type in {"timeout", "remote_error"}:
            logger.warning("renaper.validation.remote_unavailable", extra=log_extra)
        elif error_type == "auth_error":
            logger.error("renaper.validation.remote_unavailable", extra=log_extra)
        elif error_type == "invalid_response":
            logger.error("renaper.validation.invalid_response", extra=log_extra)
        elif error_type == "fallecido":
            logger.info("renaper.validation.fallecido", extra=log_extra)
        else:
            logger.error("renaper.validation.response_error", extra=log_extra)
        return

    response_summary["data_keys"] = sorted(
        list(resultado_renaper.get("data", {}).keys())
    )
    logger.info(
        "renaper.validation.response_ok",
        extra={
            "data": {
                **log_data,
                "stage": "response",
                "response": response_summary,
            }
        },
    )


class ValidacionRenaperView(View):
    """Vista para validar datos del ciudadano contra Renaper"""

    def dispatch(self, request, *args, **kwargs):
        # Verificar permisos - solo técnicos y coordinadores
        user = request.user
        if not user.is_authenticated:
            raise PermissionDenied("Autenticación requerida.")

        is_admin = user.is_superuser
        is_coord = _has_permission(user, ROLE_COORDINADOR_CELIAQUIA_PERMISSION)
        is_tec = _has_permission(user, ROLE_TECNICO_CELIAQUIA_PERMISSION)

        if not (is_admin or is_coord or is_tec):
            raise PermissionDenied("Permiso denegado.")

        return super().dispatch(request, *args, **kwargs)

    @method_decorator(csrf_protect)
    def post(self, request, pk, legajo_id):
        # Si viene el parámetro 'validacion_estado', guardar el estado.
        validacion_estado = request.POST.get("validacion_estado")
        if validacion_estado:
            return self._guardar_validacion_estado(
                request, pk, legajo_id, validacion_estado
            )

        # Si no, hacer la consulta normal a Renaper.
        return self._consultar_renaper(request, pk, legajo_id)

    def _guardar_validacion_estado(self, request, pk, legajo_id, validacion_estado):
        """Guarda el estado de validación Renaper (1=correcto, 2=incorrecto, 3=subsanar)."""
        try:
            legajo = get_object_or_404(
                ExpedienteCiudadano, pk=legajo_id, expediente__pk=pk
            )

            if validacion_estado not in ["1", "2", "3"]:
                logger.warning(
                    "renaper.validation.invalid_status",
                    extra={
                        "data": {
                            "legajo_id": legajo_id,
                            "expediente_id": pk,
                            "estado_recibido": validacion_estado,
                            "user_id": getattr(request.user, "id", None),
                            "username": getattr(
                                request.user, "get_username", lambda: None
                            )(),
                        }
                    },
                )
                return JsonResponse(
                    {"success": False, "error": "Estado de validación inválido"}
                )

            legajo.estado_validacion_renaper = int(validacion_estado)

            comentario = request.POST.get("comentario")
            if validacion_estado == "3" and comentario:
                legajo.subsanacion_motivo = comentario
                legajo.revision_tecnico = "SUBSANAR"
                legajo.save(
                    update_fields=[
                        "estado_validacion_renaper",
                        "subsanacion_motivo",
                        "revision_tecnico",
                        "modificado_en",
                    ]
                )
            else:
                legajo.save(
                    update_fields=["estado_validacion_renaper", "modificado_en"]
                )

            mensajes = {"1": "Aceptado", "2": "Rechazado", "3": "Subsanar"}
            mensaje = mensajes.get(validacion_estado, "Desconocido")

            logger.info(
                "renaper.validation.status_saved",
                extra={
                    "data": {
                        "legajo_id": legajo_id,
                        "expediente_id": legajo.expediente_id,
                        "estado_guardado": mensaje,
                        "requiere_subsanacion": validacion_estado == "3",
                        "user_id": getattr(request.user, "id", None),
                        "username": getattr(
                            request.user, "get_username", lambda: None
                        )(),
                    }
                },
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": f"Validación Renaper guardada: {mensaje}",
                    "validacion_estado": int(validacion_estado),
                }
            )
        except Exception:  # pylint: disable=broad-exception-caught
            logger.exception(
                "renaper.validation.status_error",
                extra={
                    "data": {
                        "legajo_id": legajo_id,
                        "expediente_id": pk,
                        "user_id": getattr(request.user, "id", None),
                        "username": getattr(
                            request.user, "get_username", lambda: None
                        )(),
                    }
                },
            )
            return JsonResponse(
                {
                    "success": False,
                    "error": "No se pudo guardar la validación por un error interno.",
                },
                status=500,
            )

    def _consultar_renaper(self, request, pk, legajo_id):
        try:
            user = request.user

            # Obtener el legajo
            legajo = get_object_or_404(
                ExpedienteCiudadano, pk=legajo_id, expediente__pk=pk
            )

            # Si es técnico, verificar que esté asignado al expediente
            if (
                _has_permission(user, ROLE_TECNICO_CELIAQUIA_PERMISSION)
                and not user.is_superuser
            ):
                asignaciones = legajo.expediente.asignaciones_tecnicos.filter(
                    tecnico=user
                )
                if not asignaciones.exists():
                    logger.warning(
                        "renaper.validation.unauthorized",
                        extra={
                            "data": {
                                "legajo_id": legajo_id,
                                "expediente_id": pk,
                                "user_id": getattr(user, "id", None),
                                "username": getattr(
                                    user, "get_username", lambda: None
                                )(),
                            }
                        },
                    )
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "No sos el técnico asignado a este expediente.",
                        },
                        status=403,
                    )

            ciudadano = legajo.ciudadano

            if not ciudadano:
                logger.warning(
                    "renaper.validation.missing_ciudadano",
                    extra={
                        "data": {
                            "legajo_id": legajo_id,
                            "expediente_id": pk,
                            "user_id": getattr(user, "id", None),
                            "username": getattr(user, "get_username", lambda: None)(),
                        }
                    },
                )
                return JsonResponse(
                    {
                        "success": False,
                        "error": "El ciudadano asociado al legajo no existe.",
                    }
                )

            # Validaciones básicas
            if not ciudadano.documento:
                logger.warning(
                    "renaper.validation.missing_documento",
                    extra={"data": _build_log_data(user, legajo, ciudadano)},
                )
                return JsonResponse(
                    {
                        "success": False,
                        "error": "El ciudadano no tiene documento cargado",
                    }
                )

            sexo_renaper = _mapear_sexo_para_renaper(ciudadano)

            if not sexo_renaper:
                logger.warning(
                    "renaper.validation.missing_sexo",
                    extra={"data": _build_log_data(user, legajo, ciudadano)},
                )

            documento_original = str(ciudadano.documento)
            documento_consulta = _normalizar_documento_para_renaper(documento_original)

            if not _es_dni_valido_para_renaper(documento_consulta):
                logger.warning(
                    "renaper.validation.invalid_documento",
                    extra={
                        "data": _build_log_data(
                            user,
                            legajo,
                            ciudadano,
                            documento_original=documento_original,
                        )
                    },
                )
                return JsonResponse(
                    {
                        "success": False,
                        "error": f"No se pudo extraer DNI válido del documento: {documento_original}",
                    }
                )

            datos_provincia = _build_datos_provincia(ciudadano, documento_consulta)

            # Si no se pudo determinar sexo, intentar con ambos
            if not sexo_renaper:
                logger.info(
                    "renaper.validation.trying_both_sexes",
                    extra={
                        "data": _build_log_data(
                            user,
                            legajo,
                            ciudadano,
                            documento_original=documento_original,
                            documento_consulta=documento_consulta,
                        )
                    },
                )
                sexo_renaper, resultado_renaper = _resolver_sexo_y_consulta_renaper(
                    documento_consulta, sexo_renaper
                )

                if not sexo_renaper:
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "No se pudo determinar el sexo del ciudadano. Configure el sexo manualmente.",
                        }
                    )

            else:
                resultado_renaper = None

            log_data = _build_log_data(
                user,
                legajo,
                ciudadano,
                documento_original=documento_original,
                documento_consulta=documento_consulta,
                sexo_renaper=sexo_renaper,
            )

            logger.info(
                "renaper.validation.request",
                extra={
                    "data": {
                        **log_data,
                        "stage": "request",
                    }
                },
            )

            if resultado_renaper is None:
                resultado_renaper = _consultar_datos_renaper_con_reintentos(
                    documento_consulta, sexo_renaper
                )

            _log_respuesta_renaper(log_data, resultado_renaper)
            success = resultado_renaper.get("success", False)
            fallecido = resultado_renaper.get("fallecido")

            if fallecido:
                return JsonResponse(
                    {
                        "success": False,
                        "error": _get_error_message(resultado_renaper),
                    }
                )

            if not success:
                return JsonResponse(
                    {
                        "success": False,
                        "error": _get_error_message(resultado_renaper),
                    }
                )

            datos_renaper = resultado_renaper["data"]

            datos_renaper_formateados = _formatear_datos_renaper(
                datos_renaper, sexo_renaper, documento_consulta
            )

            # La validación se guardará cuando el usuario elija "Datos correctos" o "Datos incorrectos"

            logger.info(
                "renaper.validation.result_ready",
                extra={
                    "data": {
                        **log_data,
                        "stage": "result",
                        "campos_provincia": list(datos_provincia.keys()),
                        "campos_renaper": list(datos_renaper_formateados.keys()),
                    }
                },
            )

            return JsonResponse(
                {
                    "success": True,
                    "datos_provincia": datos_provincia,
                    "datos_renaper": datos_renaper_formateados,
                    "ciudadano_nombre": f"{ciudadano.nombre} {ciudadano.apellido}",
                    "documento": documento_consulta,
                }
            )

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.exception(
                "renaper.validation.unhandled_error",
                extra={
                    "data": {
                        "legajo_id": legajo_id,
                        "expediente_id": pk,
                        "user_id": getattr(request.user, "id", None),
                        "username": getattr(
                            request.user, "get_username", lambda: None
                        )(),
                    }
                },
            )
            return JsonResponse(
                {
                    "success": False,
                    "error": "Ha ocurrido un error inesperado. Por favor, contacte al administrador.",
                },
                status=500,
            )
