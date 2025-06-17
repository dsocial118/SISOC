from .models import Centro, ActividadCentro, ParticipanteActividad
from django.core.exceptions import ValidationError


class CentroService:

    @staticmethod
    def obtener_adheridos(centro_faro):
        """Devuelve los centros adheridos a un FARO activo"""
        if not centro_faro or centro_faro.tipo != "faro":
            return Centro.objects.none()
        return Centro.objects.filter(faro_asociado=centro_faro, activo=True)

    @staticmethod
    def puede_asociar_adherido(centro):
        """Devuelve True si el centro puede tener adheridos"""
        return centro.tipo == "faro" and centro.activo

    @staticmethod
    def es_centro_valido_para_actividad(centro):
        """Valida si un centro puede tener actividades (debe estar activo)"""
        return centro.activo


class ActividadCentroService:

    @staticmethod
    def obtener_actividades_por_centro(centro):
        return ActividadCentro.objects.filter(centro=centro)


class ParticipanteService:

    @staticmethod
    def contar_participantes_por_actividad(actividad_centro):
        return ParticipanteActividad.objects.filter(
            actividad_centro=actividad_centro
        ).count()

    @staticmethod
    def cargar_participantes_desde_lista(lista_dnis, actividad_centro):
        """Carga masiva desde una lista de CUITs"""
        existing = set(
            ParticipanteActividad.objects.filter(
                actividad_centro=actividad_centro, cuit__in=lista_dnis
            ).values_list("cuit", flat=True)
        )

        nuevos = [
            ParticipanteActividad(cuit=cuit, actividad_centro=actividad_centro)
            for cuit in lista_dnis
            if cuit not in existing
        ]

        ParticipanteActividad.objects.bulk_create(nuevos, ignore_conflicts=True)
        return len(nuevos)
