from centrodefamilia.models import Actividad



def actividades_disponibles_para_centro():
    """
    Devuelve todas las actividades cargadas por el técnico
    (puede extenderse para aplicar filtros por centro en el futuro).
    """
    return Actividad.objects.all()
