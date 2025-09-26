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
        try:
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
            
            # Validaciones básicas
            if not ciudadano.sexo:
                return JsonResponse({
                    "success": False,
                    "error": "El ciudadano no tiene sexo configurado"
                })
            
            # Convertir CUIT (11 dígitos) a DNI (8 dígitos) para Renaper
            documento_original = str(ciudadano.documento)
            
            if len(documento_original) == 11:  # Es CUIT de provincia
                documento_consulta = documento_original[2:10]
            else:
                documento_consulta = documento_original
            
            # Validar que sea DNI válido (8 dígitos numéricos)
            if not documento_consulta.isdigit() or len(documento_consulta) != 8:
                return JsonResponse({
                    "success": False,
                    "error": f"No se pudo extraer DNI válido del documento: {documento_original}"
                })
            
            # Datos provinciales
            datos_provincia = {
                "documento": documento_consulta,
                "nombre": getattr(ciudadano, 'nombre', '') or "",
                "apellido": getattr(ciudadano, 'apellido', '') or "",
                "fecha_nacimiento": ciudadano.fecha_nacimiento.strftime("%d/%m/%Y") if ciudadano.fecha_nacimiento else None,
                "sexo": ciudadano.sexo.sexo if ciudadano.sexo else None,
                "calle": getattr(ciudadano, 'calle', '') or "",
                "altura": str(ciudadano.altura) if ciudadano.altura else "",
                "piso_departamento": getattr(ciudadano, 'piso_departamento', '') or "",
                "ciudad": getattr(ciudadano, 'ciudad', '') or "",
                "provincia": ciudadano.provincia.nombre if ciudadano.provincia else None,
                "codigo_postal": str(ciudadano.codigo_postal) if ciudadano.codigo_postal else "",
            }
            
            # Consultar Renaper
            sexo_renaper = "M" if ciudadano.sexo.sexo == "Masculino" else "F"
            
            print(f"\n=== ENVIANDO A RENAPER ===")
            print(f"DNI: {documento_consulta}")
            print(f"Sexo: {sexo_renaper}")
            print(f"Documento original: {documento_original}")
            print(f"Sexo ciudadano: {ciudadano.sexo.sexo if ciudadano.sexo else 'None'}")
            print(f"Ciudadano ID: {ciudadano.id}")
            print(f"Legajo ID: {legajo.pk}")
            
            resultado_renaper = consultar_datos_renaper(documento_consulta, sexo_renaper)
            
            print(f"\n=== RESPUESTA DE RENAPER ===")
            print(f"Success: {resultado_renaper.get('success')}")
            print(f"Keys: {list(resultado_renaper.keys())}")
            if not resultado_renaper.get('success'):
                print(f"Error: {resultado_renaper.get('error')}")
                print(f"Raw response: {resultado_renaper.get('raw_response', 'N/A')}")
            else:
                print(f"Data keys: {list(resultado_renaper.get('data', {}).keys())}")
            print(f"========================\n")
            
            if not resultado_renaper.get("success", False):
                error_msg = resultado_renaper.get('error', 'Error desconocido al consultar Renaper')
                raw_response = resultado_renaper.get('raw_response', 'Sin respuesta raw')
                
                print(f"\n=== ERROR RENAPER ===")
                print(f"DNI: {documento_consulta}")
                print(f"Error: {error_msg}")
                print(f"Raw response: {raw_response}")
                print(f"==================\n")
                
                logger.error(
                    "Error Renaper para DNI %s: %s. Raw response: %s", 
                    documento_consulta, error_msg, raw_response
                )
                
                return JsonResponse({
                    "success": False,
                    "error": f"Error al consultar Renaper: {error_msg}",
                    "debug_info": {
                        "dni_consultado": documento_consulta,
                        "sexo": sexo_renaper,
                        "raw_response": str(raw_response)[:200]  # Primeros 200 chars
                    }
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
                try:
                    from core.models import Provincia
                    provincia_obj = Provincia.objects.get(pk=datos_renaper["provincia"])
                    datos_renaper_formateados["provincia"] = provincia_obj.nombre
                except (Provincia.DoesNotExist, ValueError, TypeError):
                    datos_renaper_formateados["provincia"] = "Provincia no encontrada"
            
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
                "Error inesperado al validar con Renaper legajo %s: %s", 
                legajo_id, str(e), exc_info=True
            )
            return JsonResponse({
                "success": False,
                "error": f"Error inesperado: {str(e)}"
            }, status=500)