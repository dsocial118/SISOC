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

            return JsonResponse(
                {
                    "success": True,
                    "message": f"Validación Renaper guardada: {mensaje}",
                    "validacion_estado": int(validacion_estado),
                }
            )

        except Exception as e:
            logger.error(
                "Error al guardar validación Renaper legajo %s: %s",
                legajo_id,
                str(e),
                exc_info=True,
            )
            return JsonResponse(
                {"success": False, "error": f"Error al guardar validación: {str(e)}"},
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
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "No sos el técnico asignado a este expediente.",
                        },
                        status=403,
                    )

            ciudadano = legajo.ciudadano

            # Validaciones básicas
            if not ciudadano.sexo:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "El ciudadano no tiene sexo configurado",
                    }
                )

            # Convertir CUIT (11 dígitos) a DNI (8 dígitos) para Renaper
            documento_original = str(ciudadano.documento)

            if len(documento_original) == 11:  # Es CUIT de provincia
                documento_consulta = documento_original[2:10]
            else:
                documento_consulta = documento_original

            # Validar que sea DNI válido (8 dígitos numéricos)
            if not documento_consulta.isdigit() or len(documento_consulta) != 8:
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

            # Consultar Renaper
            sexo_renaper = "M" if ciudadano.sexo.sexo == "Masculino" else "F"

            print(f"\n=== ENVIANDO A RENAPER ===")
            print(f"DNI: {documento_consulta}")
            print(f"Sexo: {sexo_renaper}")
            print(f"Documento original: {documento_original}")
            print(
                f"Sexo ciudadano: {ciudadano.sexo.sexo if ciudadano.sexo else 'None'}"
            )
            print(f"Ciudadano ID: {ciudadano.id}")
            print(f"Legajo ID: {legajo.pk}")

            resultado_renaper = consultar_datos_renaper(
                documento_consulta, sexo_renaper
            )

            print(f"\n=== RESPUESTA DE RENAPER ===")
            print(f"Success: {resultado_renaper.get('success')}")
            print(f"Keys: {list(resultado_renaper.keys())}")
            if not resultado_renaper.get("success"):
                print(f"Error: {resultado_renaper.get('error')}")
                print(f"Raw response: {resultado_renaper.get('raw_response', 'N/A')}")
            else:
                print(f"Data keys: {list(resultado_renaper.get('data', {}).keys())}")
            print(f"========================\n")

            if not resultado_renaper.get("success", False):
                error_msg = resultado_renaper.get(
                    "error", "Error desconocido al consultar Renaper"
                )
                raw_response = resultado_renaper.get(
                    "raw_response", "Sin respuesta raw"
                )

                print(f"\n=== ERROR RENAPER ===")
                print(f"DNI: {documento_consulta}")
                print(f"Error: {error_msg}")
                print(f"Raw response: {raw_response}")
                print(f"==================\n")

                logger.error(
                    "Error Renaper para DNI %s: %s. Raw response: %s",
                    documento_consulta,
                    error_msg,
                    raw_response,
                )

                return JsonResponse(
                    {
                        "success": False,
                        "error": f"Error al consultar Renaper: {error_msg}",
                        "debug_info": {
                            "dni_consultado": documento_consulta,
                            "sexo": sexo_renaper,
                            "raw_response": str(raw_response)[
                                :200
                            ],  # Primeros 200 chars
                        },
                    }
                )

            if resultado_renaper.get("fallecido"):
                return JsonResponse(
                    {
                        "success": False,
                        "error": "La persona figura como fallecida en Renaper",
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

            return JsonResponse(
                {
                    "success": True,
                    "datos_provincia": datos_provincia,
                    "datos_renaper": datos_renaper_formateados,
                    "ciudadano_nombre": f"{ciudadano.nombre} {ciudadano.apellido}",
                    "documento": documento_consulta,
                }
            )

        except Exception as e:
            logger.error(
                "Error inesperado al validar con Renaper legajo %s: %s",
                legajo_id,
                str(e),
                exc_info=True,
            )
            return JsonResponse(
                {"success": False, "error": f"Error inesperado: {str(e)}"}, status=500
            )
