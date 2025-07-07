from django.core.exceptions import ValidationError
from django.db.models import CharField
from django.db.models.functions import Cast

from centrodefamilia.models import (
    ActividadCentro,
    ParticipanteActividad,
    Centro,
)

from ciudadanos.models import (
    Ciudadano,
    DimensionEconomia,
    DimensionEducacion,
    DimensionFamilia,
    DimensionSalud,
    DimensionTrabajo,
    DimensionVivienda,
    CiudadanoPrograma,
    HistorialCiudadanoProgramas,
)


def puede_operar(centro):
    if centro.tipo == "adherido":
        return bool(centro.faro_asociado and centro.faro_asociado.activo)
    return True


def obtener_centros_adheridos_de_faro(faro):
    return Centro.objects.filter(faro_asociado=faro, activo=True)


def validar_cuit(cuit):
    s = str(cuit)
    return s.isdigit() and len(s) in (10, 11)


def validar_ciudadano_en_rango_para_actividad(ciudadano, actividad_centro):
    if actividad_centro.centro.tipo == "adherido":
        if not (1 <= ciudadano.id <= 1984):
            raise ValueError(
                f"El ciudadano ID {ciudadano.id} no está habilitado para inscribirse en este centro adherido."
            )


class ActividadService:
    @staticmethod
    def obtener_o_error(actividad_id):
        actividad = ActividadCentro.objects.filter(pk=actividad_id).first()
        if not actividad:
            raise LookupError("Actividad no encontrada.")
        return actividad


class ParticipanteService:
    @staticmethod
    def contar_participantes_por_actividad(actividad_centro):
        return ParticipanteActividad.objects.filter(
            actividad_centro=actividad_centro
        ).count()

    @staticmethod
    def cargar_participantes_desde_lista(lista_dnis, actividad_centro):
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

    @staticmethod
    def crear_ciudadano_con_dimensiones(datos):
        ciudadano = Ciudadano.objects.create(
            nombre=datos.get("nombre"),
            apellido=datos.get("apellido"),
            documento=datos.get("dni"),
            fecha_nacimiento=datos.get("fecha_nacimiento"),
            tipo_documento=datos.get("tipo_documento"),
            sexo=datos.get("genero"),
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
        return ParticipanteActividad.objects.create(
            actividad_centro_id=actividad_id, ciudadano=ciudadano
        )

    @staticmethod
    def validar_ciudadano(ciudadano, actividad_centro):
        validar_ciudadano_en_rango_para_actividad(ciudadano, actividad_centro)

    @staticmethod
    def asignar_programa(ciudadano, usuario, programa_id=1):
        cp, created = CiudadanoPrograma.objects.get_or_create(
            ciudadano=ciudadano,
            programas_id=programa_id,
            defaults={"creado_por": usuario},
        )
        if created:
            HistorialCiudadanoProgramas.objects.create(
                programa_id=programa_id,
                ciudadano=ciudadano,
                accion="agregado",
                usuario=usuario,
            )

    @classmethod
    def agregar_existente(cls, usuario, actividad_id, ciudadano_id):
        actividad = ActividadService.obtener_o_error(actividad_id)
        ciudadano = Ciudadano.objects.filter(pk=ciudadano_id).first()
        if not ciudadano:
            raise LookupError("Ciudadano no encontrado.")
        cls.validar_ciudadano(ciudadano, actividad)
        participante = cls.crear_participante(actividad_id, ciudadano)
        cls.asignar_programa(ciudadano, usuario)
        return participante

    @classmethod
    def crear_nuevo_con_dimensiones(cls, usuario, actividad_id, datos):
        actividad = ActividadService.obtener_o_error(actividad_id)
        ciudadano = cls.crear_ciudadano_con_dimensiones(datos)
        cls.validar_ciudadano(ciudadano, actividad)
        participante = cls.crear_participante(actividad_id, ciudadano)
        cls.asignar_programa(ciudadano, usuario)
        return participante

    @staticmethod
    def buscar_ciudadanos(query, max_results=10):
        cleaned = (query or "").strip().lower()
        if len(cleaned) < 4:
            return []
        return list(
            Ciudadano.objects.annotate(doc_str=Cast("documento", CharField()))
            .filter(doc_str__startswith=cleaned)
            .order_by("documento")[:max_results]
        )
