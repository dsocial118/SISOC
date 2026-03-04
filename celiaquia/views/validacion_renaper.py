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

logger = logging.getLogger(__name__)


def _truncate(value, length=500):
    if isinstance(value, str) and len(value) > length:
        return f"{value[:length]}…"
    return value


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


def _in_group(user, name: str) -> bool:
    return user.is_authenticated and user.groups.filter(name=name).exists()


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


def _build_datos_provincia(ciudadano, documento_consulta):
    return {
        "documento": documento_consulta,
        "nombre": (getattr(ciudadano, "nombre", "") or "").title(),
        "apellido": (getattr(ciudadano, "apellido", "") or "").title(),
        "fecha_nacimiento": (
            ciudadano.fecha_nacimiento.strftime("%d/%m/%Y")
            if ciudadano.fecha_nacimiento
            else None
        ),
        "sexo": getattr(getattr(ciudadano, "sexo", None), "sexo", None),
        "calle": (getattr(ciudadano, "calle", "") or "").title(),
        "altura": str(ciudadano.altura) if ciudadano.altura else "",
        "piso_departamento": (
            getattr(ciudadano, "piso_departamento", "") or ""
        ).title(),
        "ciudad": (getattr(ciudadano, "ciudad", "") or "").title(),
        "provincia": ciudadano.provincia.nombre if ciudadano.provincia else None,
        "codigo_postal": (
            str(ciudadano.codigo_postal) if ciudadano.codigo_postal else ""
        ),
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


def _consultar_datos_renaper_con_reintentos(documento_consulta, sexo_renaper):
    max_retries, backoff_seconds = _get_renaper_retry_config()
    ultimo_resultado = None

    for intento in range(1, max_retries + 1):
        ultimo_resultado = consultar_datos_renaper(documento_consulta, sexo_renaper)
        if ultimo_resultado.get("success"):
            return ultimo_resultado

        if intento >= max_retries:
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
                }
            },
        )

        if backoff_seconds > 0:
            time.sleep(backoff_seconds * (2 ** (intento - 1)))

    return ultimo_resultado or {
        "success": False,
        "error": "Error desconocido al consultar Renaper",
    }


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


def _formatear_datos_renaper(datos_renaper, sexo_renaper, documento_consulta=None):
    datos_renaper_formateados = {
        "documento": datos_renaper.get("documento") or documento_consulta,
        "nombre": (datos_renaper.get("nombre") or "").title(),
        "apellido": (datos_renaper.get("apellido") or "").title(),
        "fecha_nacimiento": _formatear_fecha_renaper(
            datos_renaper.get("fecha_nacimiento")
        ),
        "sexo": "Masculino" if sexo_renaper == "M" else "Femenino",
        "calle": (datos_renaper.get("calle") or "").title(),
        "altura": str(datos_renaper.get("altura") or ""),
        "piso_departamento": (datos_renaper.get("piso_departamento") or "").title(),
        "ciudad": (datos_renaper.get("ciudad") or "").title(),
        "provincia": None,
        "codigo_postal": str(datos_renaper.get("codigo_postal") or ""),
    }

    if datos_renaper.get("provincia"):
        try:
            from core.models import Provincia

            provincia_obj = Provincia.objects.get(pk=datos_renaper["provincia"])
            datos_renaper_formateados["provincia"] = provincia_obj.nombre
        except (Provincia.DoesNotExist, ValueError, TypeError):
            datos_renaper_formateados["provincia"] = "Provincia no encontrada"

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
        response_summary["error"] = resultado_renaper.get("error")
        response_summary["raw_response_excerpt"] = _truncate(
            resultado_renaper.get("raw_response", "Sin respuesta")
        )
        logger.warning(
            "renaper.validation.response_error",
            extra={
                "data": {
                    **log_data,
                    "stage": "response",
                    "response": response_summary,
                }
            },
        )
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
        is_coord = _in_group(user, "CoordinadorCeliaquia")
        is_tec = _in_group(user, "TecnicoCeliaquia")

        if not (is_admin or is_coord or is_tec):
            raise PermissionDenied("Permiso denegado.")

        return super().dispatch(request, *args, **kwargs)

    @method_decorator(csrf_protect)
    def post(self, request, pk, legajo_id):
        # Solo hacer la consulta a Renaper (sin guardar estado)
        return self._consultar_renaper(request, pk, legajo_id)

    def _consultar_renaper(self, request, pk, legajo_id):
        try:
            user = request.user

            # Obtener el legajo
            legajo = get_object_or_404(
                ExpedienteCiudadano, pk=legajo_id, expediente__pk=pk
            )

            # Si es técnico, verificar que esté asignado al expediente
            if _in_group(user, "TecnicoCeliaquia") and not user.is_superuser:
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
                logger.warning(
                    "renaper.validation.fallecido",
                    extra={
                        "data": {
                            **log_data,
                            "stage": "response",
                            "fallecido": True,
                        }
                    },
                )
                return JsonResponse(
                    {
                        "success": False,
                        "error": "La persona figura como fallecida en Renaper",
                    }
                )

            if not success:
                error_msg = resultado_renaper.get(
                    "error", "Error desconocido al consultar Renaper"
                )
                raw_response = resultado_renaper.get(
                    "raw_response", "Sin respuesta raw"
                )

                logger.error(
                    "renaper.validation.remote_error",
                    extra={
                        "data": {
                            **log_data,
                            "stage": "response",
                            "error": error_msg,
                            "raw_response_excerpt": _truncate(raw_response),
                        }
                    },
                )

                return JsonResponse(
                    {
                        "success": False,
                        "error": "Ocurrió un error El Cuit o el Sexo no coincide con esos datos.",
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
