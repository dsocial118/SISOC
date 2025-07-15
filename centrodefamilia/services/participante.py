from django.forms import CharField
from centrodefamilia.models import Centro, ActividadCentro, ParticipanteActividad
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
from django.db.models.functions import Cast


class AlreadyRegistered(Exception):
    """Se lanza cuando un ciudadano ya está inscrito en la actividad."""


class CupoExcedido(Exception):
    """Se lanza cuando la actividad alcanzó su cupo máximo."""


class SexoNoPermitido(Exception):
    """Se lanza cuando el sexo del ciudadano no está permitido en la actividad."""


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
    if actividad_centro.centro.tipo == "adherido" and not 1 <= ciudadano.id <= 1984:
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
        """Carga masiva desde una lista de documentos (DNI)"""
        existing = set(
            ParticipanteActividad.objects.filter(
                actividad_centro=actividad_centro, ciudadano__documento__in=lista_dnis
            ).values_list("ciudadano__documento", flat=True)
        )
        ciudadanos = Ciudadano.objects.filter(documento__in=lista_dnis)

        nuevos = [
            ParticipanteActividad(ciudadano=c, actividad_centro=actividad_centro)
            for c in ciudadanos
            if c.documento not in existing
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
        _, created = CiudadanoPrograma.objects.get_or_create(
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
    def procesar_creacion(cls, usuario, actividad_id, datos=None, ciudadano_id=None):
        # Validar inscripción duplicada
        if (
            ciudadano_id
            and ParticipanteActividad.objects.filter(
                actividad_centro_id=actividad_id, ciudadano_id=ciudadano_id
            ).exists()
        ):
            raise AlreadyRegistered("Este ciudadano ya está inscrito en la actividad.")

        # Verificar cupo
        actividad = ActividadService.obtener_o_error(actividad_id)
        total = ParticipanteActividad.objects.filter(
            actividad_centro_id=actividad_id
        ).count()
        if total >= actividad.cantidad_personas:
            raise CupoExcedido(
                "Se alcanzó el cupo máximo de asistentes para esta actividad."
            )

        # Obtener o crear ciudadano
        if ciudadano_id:
            ciudadano = Ciudadano.objects.filter(pk=ciudadano_id).first()
            if not ciudadano:
                raise LookupError("Ciudadano no encontrado.")
        else:
            # Validar sexo antes de crear
            genero = datos.get("genero")
            if actividad.sexoact.exists() and genero not in actividad.sexoact.all():
                raise SexoNoPermitido(
                    "El sexo del ciudadano no coincide con los permitidos para esta actividad."
                )
            ciudadano = cls.crear_ciudadano_con_dimensiones(datos)

        # Validar sexo para todos los casos
        if actividad.sexoact.exists() and ciudadano.sexo not in actividad.sexoact.all():
            raise SexoNoPermitido(
                "El sexo del ciudadano no coincide con los permitidos para esta actividad."
            )

        # Registrar participante
        cls.validar_ciudadano(ciudadano, actividad)
        participante = cls.crear_participante(actividad_id, ciudadano)
        cls.asignar_programa(ciudadano, usuario)
        tipo = "existente" if ciudadano_id else "nuevo"
        return tipo, participante

    @staticmethod
    def buscar_ciudadanos(query, max_results=10):
        cleaned = (query or "").strip()
        if len(cleaned) < 4 or not cleaned.isdigit():
            return []

        qs = (
            Ciudadano.objects
                # asegúrate de usar django.db.models.CharField() aquí
                .annotate(doc_str=Cast("documento", output_field=CharField()))
                .filter(doc_str__startswith=cleaned)
                .order_by("documento")[:max_results]
        )
        return list(qs)


    @staticmethod
    def obtener_participantes_con_ciudadanos(actividad_centro):
        return ParticipanteActividad.objects.filter(
            actividad_centro=actividad_centro
        ).select_related("ciudadano")
