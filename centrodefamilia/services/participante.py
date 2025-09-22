import logging
from django.db import transaction

from centrodefamilia.models import (
    Centro,
    ActividadCentro,
    ParticipanteActividad,
    ParticipanteActividadHistorial,
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

logger = logging.getLogger("django")


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
    if actividad_centro.centro.tipo == "adherido" and not ciudadano.demo_centro_familia:
        raise ValueError(
            f"El ciudadano {ciudadano.apellido}, {ciudadano.nombre} no está habilitado para inscribirse en este centro adherido."
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
    def contar_inscritos(actividad_centro):
        return ParticipanteActividad.objects.filter(
            actividad_centro=actividad_centro, estado="inscrito"
        ).count()

    @staticmethod
    def obtener_inscritos(actividad_centro):
        return ParticipanteActividad.objects.filter(
            actividad_centro=actividad_centro, estado="inscrito"
        ).select_related("ciudadano")

    @staticmethod
    def obtener_lista_espera(actividad_centro):
        return ParticipanteActividad.objects.filter(
            actividad_centro=actividad_centro, estado="lista_espera"
        ).select_related("ciudadano")

    @staticmethod
    def cargar_participantes_desde_lista(lista_dnis, actividad_centro):
        existing = set(
            ParticipanteActividad.objects.filter(
                actividad_centro=actividad_centro, ciudadano__documento__in=lista_dnis
            ).values_list("ciudadano__documento", flat=True)
        )
        ciudadanos = Ciudadano.objects.filter(documento__in=lista_dnis)

        nuevos = [
            ParticipanteActividad(actividad_centro=actividad_centro, ciudadano=c)
            for c in ciudadanos
            if c.documento not in existing
        ]
        ParticipanteActividad.objects.bulk_create(nuevos, ignore_conflicts=True)
        return len(nuevos)

    @staticmethod
    def _crear_dimensiones_y_programa(ciudadano, usuario, actividad_id):
        # Forzar siempre programa ID = 1
        programa_id = 1

        for Modelo in (
            DimensionEconomia,
            DimensionEducacion,
            DimensionFamilia,
            DimensionSalud,
            DimensionTrabajo,
            DimensionVivienda,
        ):
            Modelo.objects.update_or_create(ciudadano=ciudadano)

            creado = CiudadanoPrograma.objects.update_or_create(
                ciudadano=ciudadano,
                programas_id=programa_id,
                defaults={"creado_por": usuario},
            )
        if creado:
            HistorialCiudadanoProgramas.objects.create(
                programa_id=programa_id,
                ciudadano=ciudadano,
                accion="agregado",
                usuario=usuario,
            )

    @staticmethod
    def crear_ciudadano_con_dimensiones(datos, usuario, actividad_id):
        ciudadano = Ciudadano.objects.create(
            nombre=datos.get("nombre"),
            apellido=datos.get("apellido"),
            documento=datos.get("dni"),
            fecha_nacimiento=datos.get("fecha_nacimiento"),
            tipo_documento=datos.get("tipo_documento"),
            sexo=datos.get("genero"),
        )
        ParticipanteService._crear_dimensiones_y_programa(
            ciudadano, usuario, actividad_id
        )
        return ciudadano

    @staticmethod
    def crear_participante(actividad_id, ciudadano, estado):
        actividad = ActividadService.obtener_o_error(actividad_id)
        return ParticipanteActividad.objects.create(
            actividad_centro=actividad, ciudadano=ciudadano, estado=estado
        )

    @staticmethod
    def validar_ciudadano(ciudadano, actividad_centro):
        validar_ciudadano_en_rango_para_actividad(ciudadano, actividad_centro)

    @classmethod
    @transaction.atomic
    def procesar_creacion(cls, usuario, actividad_id, datos=None, **kwargs):
        ciudadano_id = kwargs.get("ciudadano_id")
        allow_waitlist = kwargs.get("allow_waitlist", False)

        if (
            ciudadano_id
            and ParticipanteActividad.objects.filter(
                actividad_centro_id=actividad_id,
                ciudadano_id=ciudadano_id,
                estado__in=["inscrito", "lista_espera"],
            ).exists()
        ):
            raise AlreadyRegistered("Ya está inscrito o en lista de espera.")

        actividad = ActividadService.obtener_o_error(actividad_id)
        ocupados = cls.contar_inscritos(actividad)

        if ocupados >= actividad.cantidad_personas and not allow_waitlist:
            raise CupoExcedido("Cupo máximo alcanzado.")

        if ciudadano_id:
            ciudadano = Ciudadano.objects.filter(pk=ciudadano_id).first()
            if not ciudadano:
                raise LookupError("Ciudadano no encontrado.")
            cls._crear_dimensiones_y_programa(ciudadano, usuario, actividad_id)
        else:
            genero = datos.get("genero")
            if actividad.sexoact.exists() and genero not in actividad.sexoact.all():
                raise SexoNoPermitido("Sexo no permitido para esta actividad.")
            ciudadano = cls.crear_ciudadano_con_dimensiones(
                datos, usuario, actividad_id
            )

        if actividad.sexoact.exists() and ciudadano.sexo not in actividad.sexoact.all():
            raise SexoNoPermitido("Sexo no permitido para esta actividad.")
        cls.validar_ciudadano(ciudadano, actividad)

        estado = (
            "inscrito" if ocupados < actividad.cantidad_personas else "lista_espera"
        )
        participante = cls.crear_participante(actividad_id, ciudadano, estado)

        ParticipanteActividadHistorial.objects.create(
            participante=participante,
            estado_anterior=None,
            estado_nuevo=estado,
            usuario=usuario,
        )
        return estado, participante

    @classmethod
    @transaction.atomic
    def dar_de_baja(cls, participante_id, usuario):
        participante = ParticipanteActividad.objects.select_for_update().get(
            pk=participante_id
        )
        prev = participante.estado
        if prev == "dado_baja":
            return participante
        participante.estado = "dado_baja"
        participante.save()

        ParticipanteActividadHistorial.objects.create(
            participante=participante,
            estado_anterior=prev,
            estado_nuevo="dado_baja",
            usuario=usuario,
        )
        cls.promover_lista_espera(participante.actividad_centro, usuario)
        return participante

    @classmethod
    @transaction.atomic
    def promover_lista_espera(cls, actividad_centro, usuario):
        siguiente = (
            ParticipanteActividad.objects.filter(
                actividad_centro=actividad_centro, estado="lista_espera"
            )
            .order_by("fecha_registro")
            .first()
        )
        if not siguiente:
            return None
        prev = siguiente.estado
        siguiente.estado = "inscrito"
        siguiente.save()

        ParticipanteActividadHistorial.objects.create(
            participante=siguiente,
            estado_anterior=prev,
            estado_nuevo="inscrito",
            usuario=usuario,
        )
        return siguiente

    @staticmethod
    def buscar_ciudadanos_por_documento(query, max_results=10):
        cleaned = (query or "").strip()
        if len(cleaned) < 4 or not cleaned.isdigit():
            return []
        return list(
            Ciudadano.objects.filter(documento__startswith=cleaned).order_by(
                "documento"
            )[:max_results]
        )
