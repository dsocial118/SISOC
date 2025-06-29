from centrodefamilia.models import Centro, ParticipanteActividad
from ciudadanos.models import (
    Ciudadano,
    DimensionEconomia,
    DimensionEducacion,
    DimensionFamilia,
    DimensionSalud,
    DimensionTrabajo,
    DimensionVivienda,
)


def puede_operar(centro):
    """
    Verifica si un centro puede operar:
    - Si es tipo 'adherido', debe tener un centro faro activo asociado.
    - Si es tipo 'faro', puede operar por defecto.
    """
    if centro.tipo == "adherido":
        return bool(centro.faro_asociado and centro.faro_asociado.activo)
    return True


def obtener_centros_adheridos_de_faro(faro):
    """
    Retorna todos los centros adheridos vinculados a un centro faro específico.
    Solo devuelve los que estén activos.
    """
    return Centro.objects.filter(faro_asociado=faro, activo=True)


def validar_cuit(cuit):
    """
    Verifica que el CUIT sea numérico y tenga entre 10 y 11 dígitos.
    """
    return str(cuit).isdigit() and len(str(cuit)) in (10, 11)


class ParticipanteService:
    @staticmethod
    def contar_participantes_por_actividad(actividad_centro):
        """Cuenta cuantos participantes hay en una actividad"""
        return ParticipanteActividad.objects.filter(
            actividad_centro=actividad_centro
        ).count()

    @staticmethod
    def cargar_participantes_desde_lista(lista_dnis, actividad_centro):
        """Carga masiva desde una lista de CUITs"""
        existing = set(
            ParticipanteActividad.objects.filter(
                actividad_centro=actividad_centro,
                cuit__in=lista_dnis
            ).values_list("cuit", flat=True)
        )
        nuevos = [
            ParticipanteActividad(cuit=cuit, actividad_centro=actividad_centro)
            for cuit in lista_dnis
            if cuit not in existing
        ]
        ParticipanteActividad.objects.bulk_create(nuevos, ignore_conflicts=True)
        return len(nuevos)

    @staticmethod
    def crear_ciudadano_con_dimensiones(data):
        """Crea un ciudadano y todas sus dimensiones asociadas"""
        ciudadano = Ciudadano.objects.create(
            nombre=data["nombre"],
            apellido=data["apellido"],
            documento=data["dni"],
            fecha_nacimiento=data["fecha_nacimiento"],
            tipo_documento=data.get("tipo_documento"),
            sexo=data.get("genero"),
        )
        for Modelo in (
            DimensionEconomia,
            DimensionEducacion,
            DimensionFamilia,
            DimensionSalud,
            DimensionTrabajo,
            DimensionVivienda,
        ):
            Modelo.objects.create(ciudadano=ciudadano)
        return ciudadano

    @staticmethod
    def crear_participante(actividad_id, ciudadano):
        """Asocia un ciudadano a una actividad"""
        return ParticipanteActividad.objects.create(
            actividad_centro_id=actividad_id,
            ciudadano=ciudadano
        )
