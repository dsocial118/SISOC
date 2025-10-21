import logging
from django.shortcuts import get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from celiaquia.models import ExpedienteCiudadano
from ciudadanos.services.consulta_renaper import consultar_datos_renaper

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
        # Si viene el parámetro 'validacion_estado', guardar el estado
        validacion_estado = request.POST.get("validacion_estado")
        if validacion_estado:
            return self._guardar_validacion_estado(
                request, pk, legajo_id, validacion_estado
            )

        # Si no, hacer la consulta normal a Renaper
        return self._consultar_renaper(request, pk, legajo_id)

    def _guardar_validacion_estado(self, request, pk, legajo_id, validacion_estado):
        """Guarda el estado de validación Renaper (1=correcto, 2=incorrecto)"""
        try:
            legajo = get_object_or_404(
                ExpedienteCiudadano, pk=legajo_id, expediente__pk=pk
            )

            # Validar que el estado sea válido
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

            # Guardar el estado
            legajo.estado_validacion_renaper = int(validacion_estado)

            # Si es subsanación, guardar el comentario y cambiar estado de revisión
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

        except Exception as exc:  # pylint: disable=broad-exception-caught
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

            # Mapear sexo del ciudadano
            sexo_renaper = None
            if ciudadano.sexo:
                sexo_map = {"Masculino": "M", "Femenino": "F", "X": "X"}
                sexo_valor = (getattr(ciudadano.sexo, "sexo", "") or "").strip()
                sexo_renaper = sexo_map.get(sexo_valor)

            if not sexo_renaper:
                logger.warning(
                    "renaper.validation.missing_sexo",
                    extra={"data": _build_log_data(user, legajo, ciudadano)},
                )

            # Convertir CUIT (11 dígitos) a DNI (8 dígitos) para Renaper
            documento_original = str(ciudadano.documento)

            if len(documento_original) == 11:  # Es CUIT de provincia
                documento_consulta = documento_original[2:10]
            else:
                documento_consulta = documento_original

            # Validar que sea DNI válido (8 dígitos numéricos)
            if not documento_consulta.isdigit() or len(documento_consulta) != 8:
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

            # Datos provinciales
            datos_provincia = {
                "documento": documento_consulta,
                "nombre": (getattr(ciudadano, "nombre", "") or "").title(),
                "apellido": (getattr(ciudadano, "apellido", "") or "").title(),
                "fecha_nacimiento": (
                    ciudadano.fecha_nacimiento.strftime("%d/%m/%Y")
                    if ciudadano.fecha_nacimiento
                    else None
                ),
                "sexo": ciudadano.sexo.sexo if ciudadano.sexo else None,
                "calle": (getattr(ciudadano, "calle", "") or "").title(),
                "altura": str(ciudadano.altura) if ciudadano.altura else "",
                "piso_departamento": (
                    getattr(ciudadano, "piso_departamento", "") or ""
                ).title(),
                "ciudad": (getattr(ciudadano, "ciudad", "") or "").title(),
                "provincia": (
                    ciudadano.provincia.nombre if ciudadano.provincia else None
                ),
                "codigo_postal": (
                    str(ciudadano.codigo_postal) if ciudadano.codigo_postal else ""
                ),
            }

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
                # Intentar primero con M, luego con F
                for sexo_test in ["M", "F"]:
                    resultado_test = consultar_datos_renaper(
                        documento_consulta, sexo_test
                    )
                    if resultado_test.get("success"):
                        sexo_renaper = sexo_test
                        break

                if not sexo_renaper:
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "No se pudo determinar el sexo del ciudadano. Configure el sexo manualmente.",
                        }
                    )

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

            resultado_renaper = consultar_datos_renaper(
                documento_consulta, sexo_renaper
            )

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
                    resultado_renaper.get("raw_response", "Sin respuesta"),
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
            else:
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

            # Formatear fecha de Renaper al formato dd/mm/yyyy
            fecha_renaper = datos_renaper.get("fecha_nacimiento")
            if fecha_renaper:
                try:
                    from datetime import datetime

                    # Si viene en formato YYYY-MM-DD, convertir a DD/MM/YYYY
                    if "-" in fecha_renaper and len(fecha_renaper) == 10:
                        fecha_obj = datetime.strptime(fecha_renaper, "%Y-%m-%d")
                        fecha_renaper = fecha_obj.strftime("%d/%m/%Y")
                except:
                    pass  # Si hay error, mantener formato original

            # Formatear datos de Renaper para comparación (mismo formato que provincia)
            datos_renaper_formateados = {
                "documento": datos_renaper.get("documento"),
                "nombre": (datos_renaper.get("nombre") or "").title(),
                "apellido": (datos_renaper.get("apellido") or "").title(),
                "fecha_nacimiento": fecha_renaper,
                "sexo": "Masculino" if sexo_renaper == "M" else "Femenino",
                "calle": (datos_renaper.get("calle") or "").title(),
                "altura": str(datos_renaper.get("altura") or ""),
                "piso_departamento": (
                    datos_renaper.get("piso_departamento") or ""
                ).title(),
                "ciudad": (datos_renaper.get("ciudad") or "").title(),
                "provincia": None,  # Se mapea desde provincia_id
                "codigo_postal": str(datos_renaper.get("codigo_postal") or ""),
            }

            # Mapear provincia desde ID
            if datos_renaper.get("provincia"):
                try:
                    from core.models import Provincia

                    provincia_obj = Provincia.objects.get(pk=datos_renaper["provincia"])
                    datos_renaper_formateados["provincia"] = provincia_obj.nombre
                except (Provincia.DoesNotExist, ValueError, TypeError):
                    datos_renaper_formateados["provincia"] = "Provincia no encontrada"

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
