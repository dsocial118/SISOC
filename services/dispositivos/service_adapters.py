"""Adaptadores seguros para el proceso independiente antes del corte de tráfico."""

from django.http import HttpResponse


def permisos_requeridos(_permissions):
    """Niega tráfico hasta configurar el adaptador de identidad del servicio."""

    def decorator(view):
        def unavailable(_request, *args, **kwargs):
            return HttpResponse(
                "El servicio Dispositivos aún no recibe tráfico.", status=503
            )

        unavailable.__name__ = view.__name__
        unavailable.__doc__ = view.__doc__
        return unavailable

    return decorator
