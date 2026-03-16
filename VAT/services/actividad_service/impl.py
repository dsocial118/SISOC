from VAT.models import Actividad


def actividades_disponibles_para_centro():
    return Actividad.objects.all()
