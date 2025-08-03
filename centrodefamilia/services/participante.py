import threading
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


# Excepciones específicas para flujo de inscripción
class AlreadyRegistered(Exception):
    """Se lanza cuando un ciudadano ya está inscrito en la actividad."""


class CupoExcedido(Exception):
    """Se lanza cuando la actividad alcanzó su cupo máximo."""


class SexoNoPermitido(Exception):
    """Se lanza cuando el sexo del ciudadano no está permitido en la actividad."""


# Funciones auxiliares originales


def puede_operar(centro):
    """
    Verifica si un centro adherido puede operar solo si su faro asociado está activo.
    """
    if centro.tipo == "adherido":
        return bool(centro.faro_asociado and centro.faro_asociado.activo)
    return True


def obtener_centros_adheridos_de_faro(faro):
    """
    Retorna centros adheridos activos de un faro específico.
    """
    return Centro.objects.filter(faro_asociado=faro, activo=True)


def validar_cuit(cuit):
    """
    Valida que el CUIT esté compuesto solo por dígitos y su longitud.
    """
    s = str(cuit)
    return s.isdigit() and len(s) in (10, 11)


def validar_ciudadano_en_rango_para_actividad(ciudadano, actividad_centro):
    """
    Restringe inscritos en centros adheridos a ciertos IDs de ciudadanos.
    """
    if actividad_centro.centro.tipo == "adherido" and not 1 <= ciudadano.id <= 975:
        raise ValueError(
            f"El ciudadano ID {ciudadano.id} no está habilitado para inscribirse en este centro adherido."
        )


class ActividadService:
    """
    Servicio para obtener instancias de ActividadCentro con manejo de errores.
    """

    @staticmethod
    def obtener_o_error(actividad_id):
        actividad = ActividadCentro.objects.filter(pk=actividad_id).first()
        if not actividad:
            raise LookupError("Actividad no encontrada.")
        return actividad


class ParticipanteService:
    """
    Servicio de inscripción con gestión de estados, cupos y lista de espera.
    Incluye carga masiva, validaciones y asignación de programas.
    """

    @staticmethod
    def contar_inscritos(actividad_centro):
        """Cuenta solo los inscritos efectivos (estado='inscrito')."""
        return ParticipanteActividad.objects.filter(
            actividad_centro=actividad_centro, estado="inscrito"
        ).count()

    @staticmethod
    def obtener_inscritos(actividad_centro):
        """Devuelve queryset de participantes en estado 'inscrito'."""
        return ParticipanteActividad.objects.filter(
            actividad_centro=actividad_centro, estado="inscrito"
        ).select_related("ciudadano")

    @staticmethod
    def obtener_lista_espera(actividad_centro):
        """Devuelve queryset de participantes en estado 'lista_espera'."""
        return ParticipanteActividad.objects.filter(
            actividad_centro=actividad_centro, estado="lista_espera"
        ).select_related("ciudadano")

    @staticmethod
    def cargar_participantes_desde_lista(lista_dnis, actividad_centro):
        """
        Carga masiva desde una lista de documentos (DNI), ignora duplicados.
        """
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
        """
        Tarea en background para crear dimensiones y asignar programa.
        """
        for Modelo in (
            DimensionEconomia,
            DimensionEducacion,
            DimensionFamilia,
            DimensionSalud,
            DimensionTrabajo,
            DimensionVivienda,
        ):
            Modelo.objects.create(ciudadano=ciudadano)
        _, created = CiudadanoPrograma.objects.get_or_create(
            ciudadano=ciudadano,
            programas_id=actividad_id,
            defaults={"creado_por": usuario},
        )
        if created:
            HistorialCiudadanoProgramas.objects.create(
                programa_id=actividad_id,
                ciudadano=ciudadano,
                accion="agregado",
                usuario=usuario,
            )

    @staticmethod
    def crear_ciudadano_con_dimensiones(datos, usuario, actividad_id):
        """
        Crea un ciudadano y dispara la creación de dimensiones en background.
        """
        ciudadano = Ciudadano.objects.create(
            nombre=datos.get("nombre"),
            apellido=datos.get("apellido"),
            documento=datos.get("dni"),
            fecha_nacimiento=datos.get("fecha_nacimiento"),
            tipo_documento=datos.get("tipo_documento"),
            sexo=datos.get("genero"),
        )
        threading.Thread(
            target=ParticipanteService._crear_dimensiones_y_programa,
            args=(ciudadano, usuario, actividad_id),
            daemon=True,
        ).start()
        return ciudadano

    @staticmethod
    def crear_participante(actividad_id, ciudadano, estado):
        """
        Crea un registro de ParticipanteActividad con estado dado.
        """
        actividad = ActividadService.obtener_o_error(actividad_id)
        return ParticipanteActividad.objects.create(
            actividad_centro=actividad, ciudadano=ciudadano, estado=estado
        )

    @staticmethod
    def validar_ciudadano(ciudadano, actividad_centro):
        """
        Ejecuta validaciones custom para el ciudadano en la actividad.
        """
        validar_ciudadano_en_rango_para_actividad(ciudadano, actividad_centro)

    @classmethod
    @transaction.atomic
    def procesar_creacion(cls, usuario, actividad_id, datos=None, **kwargs):
        """
        Flujo completo de creación de inscripción:
        - Verifica duplicados
        - Verifica cupo (lanza CupoExcedido si está lleno y no allow_waitlist)
        - Obtiene o crea ciudadano
        - Valida género y rango
        - Registra inscripción con estado 'inscrito' o 'lista_espera'
        Retorna ('inscrito'|'lista_espera', participante).
        """
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
            threading.Thread(
                target=cls._crear_dimensiones_y_programa,
                args=(ciudadano, usuario, actividad_id),
                daemon=True,
            ).start()
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
