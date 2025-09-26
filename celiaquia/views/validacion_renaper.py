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
        user = request.user
        
        # Obtener el legajo
        legajo = get_object_or_404(
            ExpedienteCiudadano, 
            pk=legajo_id, 
            expediente__pk=pk
        )
        
        # Si es técnico, verificar que esté asignado al expediente
        if _in_group(user, "TecnicoCeliaquia") and not user.is_superuser:
            asignaciones = legajo.expediente.asignaciones_tecnicos.filter(tecnico=user)
            if not asignaciones.exists():
                return JsonResponse({
                    "success": False, 
                    "error": "No sos el técnico asignado a este expediente."
                }, status=403)
        
        ciudadano = legajo.ciudadano
        
        # Convertir CUIT a DNI si es necesario
        documento_consulta = ciudadano.documento
        if len(str(documento_consulta)) == 11:  # Es un CUIT
            # Extraer DNI del CUIT (posiciones 2-9)
            documento_consulta = str(documento_consulta)[2:10]
        
        # Datos provinciales
        datos_provincia = {
            "documento": documento_consulta,
            "nombre": ciudadano.nombre,
            "apellido": ciudadano.apellido,
            "fecha_nacimiento": ciudadano.fecha_nacimiento.strftime("%d/%m/%Y") if ciudadano.fecha_nacimiento else None,
            "sexo": ciudadano.sexo.sexo if ciudadano.sexo else None,
            "calle": ciudadano.calle,
            "altura": ciudadano.altura,
            "piso_departamento": ciudadano.piso_departamento,
            "ciudad": ciudadano.ciudad,
            "provincia": ciudadano.provincia.nombre if ciudadano.provincia else None,
            "codigo_postal": ciudadano.codigo_postal,
        }
        
        # Consultar Renaper
        try:
            
            sexo_renaper = "M" if ciudadano.sexo and ciudadano.sexo.sexo == "Masculino" else "F"
            resultado_renaper = consultar_datos_renaper(documento_consulta, sexo_renaper)
            
            if not resultado_renaper.get("success", False):
                error_msg = resultado_renaper.get('error', 'Error desconocido al consultar Renaper')
                logger.warning("Error Renaper para DNI %s: %s", ciudadano.documento, error_msg)
                return JsonResponse({
                    "success": False,
                    "error": f"Error al consultar Renaper: {error_msg}"
                })
            
            if resultado_renaper.get("fallecido"):
                return JsonResponse({
                    "success": False,
                    "error": "La persona figura como fallecida en Renaper"
                })
            
            datos_renaper = resultado_renaper["data"]
            
            # Formatear datos de Renaper para comparación
            datos_renaper_formateados = {
                "documento": datos_renaper.get("documento"),
                "nombre": datos_renaper.get("nombre"),
                "apellido": datos_renaper.get("apellido"),
                "fecha_nacimiento": datos_renaper.get("fecha_nacimiento"),
                "sexo": "Masculino" if sexo_renaper == "M" else "Femenino",
                "calle": datos_renaper.get("calle"),
                "altura": datos_renaper.get("altura"),
                "piso_departamento": datos_renaper.get("piso_departamento"),
                "ciudad": datos_renaper.get("ciudad"),
                "provincia": None,  # Se mapea desde provincia_id
                "codigo_postal": datos_renaper.get("codigo_postal"),
            }
            
            # Mapear provincia desde ID
            if datos_renaper.get("provincia"):
                from core.models import Provincia
                try:
                    provincia_obj = Provincia.objects.get(pk=datos_renaper["provincia"])
                    datos_renaper_formateados["provincia"] = provincia_obj.nombre
                except Provincia.DoesNotExist:
                    pass
            
            # Marcar como validado con Renaper
            legajo.validado_renaper = True
            legajo.save(update_fields=["validado_renaper", "modificado_en"])
            
            return JsonResponse({
                "success": True,
                "datos_provincia": datos_provincia,
                "datos_renaper": datos_renaper_formateados,
                "ciudadano_nombre": f"{ciudadano.nombre} {ciudadano.apellido}",
                "documento": documento_consulta
            })
            
        except Exception as e:
            logger.error(
                "Error al validar con Renaper legajo %s: %s", 
                legajo.pk, e, exc_info=True
            )
            return JsonResponse({
                "success": False,
                "error": f"Error inesperado al consultar Renaper: {str(e)}"
            }, status=500)