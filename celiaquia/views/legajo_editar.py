import json
import logging
from django.views import View
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.db import transaction

from celiaquia.models import Expediente, ExpedienteCiudadano
from ciudadanos.models import Ciudadano, Sexo, Nacionalidad

logger = logging.getLogger("django")


def _user_in_group(user, group_name: str) -> bool:
    return user.is_authenticated and user.groups.filter(name=group_name).exists()


def _is_admin(user) -> bool:
    return user.is_authenticated and user.is_superuser


def _is_provincial(user) -> bool:
    try:
        return bool(user.profile.es_usuario_provincial and user.profile.provincia_id)
    except:
        return False


@method_decorator(csrf_protect, name="dispatch")
class EditarLegajoView(View):
    def get(self, request, pk, legajo_id):
        """Obtener datos actuales del legajo para el modal"""
        user = request.user

        expediente = get_object_or_404(Expediente, pk=pk)
        legajo = get_object_or_404(
            ExpedienteCiudadano, pk=legajo_id, expediente=expediente
        )

        # Verificar permisos
        if not (
            _is_admin(user)
            or _user_in_group(user, "TecnicoCeliaquia")
            or _user_in_group(user, "CoordinadorCeliaquia")
        ):
            if _is_provincial(user):
                # Provincias solo pueden editar en ciertos estados
                if expediente.estado.nombre not in ["CREADO", "PROCESADO", "EN_ESPERA"]:
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "No puede editar legajos después de enviar el expediente.",
                        },
                        status=403,
                    )
            else:
                return JsonResponse(
                    {"success": False, "error": "Permiso denegado."}, status=403
                )

        ciudadano = legajo.ciudadano

        data = {
            "success": True,
            "legajo": {
                "id": legajo.pk,
                "apellido": ciudadano.apellido or "",
                "nombre": ciudadano.nombre or "",
                "documento": ciudadano.documento or "",
                "fecha_nacimiento": (
                    ciudadano.fecha_nacimiento.strftime("%Y-%m-%d")
                    if ciudadano.fecha_nacimiento
                    else ""
                ),
                "sexo": ciudadano.sexo_id if ciudadano.sexo else "",
                "nacionalidad": (
                    ciudadano.nacionalidad_id if ciudadano.nacionalidad else ""
                ),
                "telefono": ciudadano.telefono or "",
                "email": ciudadano.email or "",
                "calle": ciudadano.calle or "",
                "altura": ciudadano.altura or "",
                "codigo_postal": ciudadano.codigo_postal or "",
            },
        }

        return JsonResponse(data)

    def post(self, request, pk, legajo_id):
        """Actualizar datos del legajo"""
        user = request.user

        expediente = get_object_or_404(Expediente, pk=pk)
        legajo = get_object_or_404(
            ExpedienteCiudadano, pk=legajo_id, expediente=expediente
        )

        # Verificar permisos
        if not (
            _is_admin(user)
            or _user_in_group(user, "TecnicoCeliaquia")
            or _user_in_group(user, "CoordinadorCeliaquia")
        ):
            if _is_provincial(user):
                # Provincias solo pueden editar en ciertos estados
                if expediente.estado.nombre not in ["CREADO", "PROCESADO", "EN_ESPERA"]:
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "No puede editar legajos después de enviar el expediente.",
                        },
                        status=403,
                    )
            else:
                return JsonResponse(
                    {"success": False, "error": "Permiso denegado."}, status=403
                )

        try:
            with transaction.atomic():
                ciudadano = legajo.ciudadano

                # Actualizar campos básicos
                ciudadano.apellido = request.POST.get("apellido", "").strip()
                ciudadano.nombre = request.POST.get("nombre", "").strip()
                ciudadano.documento = request.POST.get("documento", "").strip()

                # Validar campos obligatorios
                if (
                    not ciudadano.apellido
                    or not ciudadano.nombre
                    or not ciudadano.documento
                ):
                    raise ValidationError(
                        "Apellido, nombre y documento son obligatorios."
                    )

                # Fecha de nacimiento
                fecha_str = request.POST.get("fecha_nacimiento", "").strip()
                if fecha_str:
                    from datetime import datetime

                    try:
                        ciudadano.fecha_nacimiento = datetime.strptime(
                            fecha_str, "%Y-%m-%d"
                        ).date()
                    except ValueError:
                        raise ValidationError("Formato de fecha inválido.")

                # Sexo
                sexo_id = request.POST.get("sexo", "").strip()
                if sexo_id:
                    try:
                        ciudadano.sexo = Sexo.objects.get(pk=sexo_id)
                    except Sexo.DoesNotExist:
                        ciudadano.sexo = None
                else:
                    ciudadano.sexo = None

                # Nacionalidad
                nacionalidad_id = request.POST.get("nacionalidad", "").strip()
                if nacionalidad_id:
                    try:
                        ciudadano.nacionalidad = Nacionalidad.objects.get(
                            pk=nacionalidad_id
                        )
                    except Nacionalidad.DoesNotExist:
                        ciudadano.nacionalidad = None
                else:
                    ciudadano.nacionalidad = None

                # Campos opcionales
                ciudadano.telefono = request.POST.get("telefono", "").strip() or None
                ciudadano.email = request.POST.get("email", "").strip() or None
                ciudadano.calle = request.POST.get("calle", "").strip() or None
                ciudadano.altura = request.POST.get("altura", "").strip() or None
                ciudadano.codigo_postal = (
                    request.POST.get("codigo_postal", "").strip() or None
                )

                # Guardar cambios
                ciudadano.save()

                logger.info(
                    "Legajo %s editado por usuario %s - Ciudadano: %s %s (DNI: %s)",
                    legajo.pk,
                    user.username,
                    ciudadano.nombre,
                    ciudadano.apellido,
                    ciudadano.documento,
                )

                return JsonResponse(
                    {
                        "success": True,
                        "message": f"Datos de {ciudadano.nombre} {ciudadano.apellido} actualizados correctamente.",
                    }
                )

        except ValidationError as e:
            logger.warning("Validación fallida al editar legajo %s: %s", legajo.pk, e, exc_info=True)
            return JsonResponse({"success": False, "error": "Los datos ingresados no son válidos."}, status=400)
        except Exception as e:
            logger.error("Error editando legajo %s: %s", legajo.pk, e, exc_info=True)
            return JsonResponse(
                {"success": False, "error": "Error interno al actualizar los datos."},
                status=500,
            )
