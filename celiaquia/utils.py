"""
Utilidades comunes para el módulo de celiaquia.
"""
from django.http import JsonResponse


def error_response(message: str, status: int = 400, extra_data: dict = None):
    """
    Crear respuesta de error estandarizada.
    
    Args:
        message: Mensaje de error
        status: Código de estado HTTP
        extra_data: Datos adicionales para incluir en la respuesta
    
    Returns:
        JsonResponse con formato estandarizado
    """
    data = {
        "success": False,
        "error": message
    }
    
    if extra_data:
        data.update(extra_data)
    
    return JsonResponse(data, status=status)


def success_response(message: str, extra_data: dict = None):
    """
    Crear respuesta de éxito estandarizada.
    
    Args:
        message: Mensaje de éxito
        extra_data: Datos adicionales para incluir en la respuesta
    
    Returns:
        JsonResponse con formato estandarizado
    """
    data = {
        "success": True,
        "message": message
    }
    
    if extra_data:
        data.update(extra_data)
    
    return JsonResponse(data)