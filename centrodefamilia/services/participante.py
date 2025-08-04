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
import logging

logger = logging.getLogger(__name__)

class AlreadyRegistered(Exception):
    """Se lanza cuando un ciudadano ya está inscrito en la actividad."""

class CupoExcedido(Exception):
    """Se lanza cuando la actividad alcanzó su cupo máximo."""

class SexoNoPermitido(Exception):
    """Se lanza cuando el sexo del ciudadano no está permitido en la actividad."""

def puede_operar(centro):
    try:
        if centro.tipo == "adherido":
            return bool(centro.faro_asociado and centro.faro_asociado.activo)
        return True
    except Exception as e:
        logger.error("Ocurrió un error inesperado en puede_operar", exc_info=True)
        return False

def obtener_centros_adheridos_de_faro(faro):
    try:
        return Centro.objects.filter(faro_asociado=faro, activo=True)
    except Exception as e:
        logger.error("Ocurrió un error inesperado en obtener_centros_adheridos_de_faro", exc_info=True)
        return Centro.objects.none()

def validar_cuit(cuit):
    try:
        s = str(cuit)
        return s.isdigit() and len(s) in (10, 11)
    except Exception as e:
        logger.error("Ocurrió un error inesperado en validar_cuit", exc_info=True)
        return False

def validar_ciudadano_en_rango_para_actividad(ciudadano, actividad_centro):
    try:
        if actividad_centro.centro.tipo == "adherido" and not 1 <= ciudadano.id <= 975:
            raise ValueError(
                f"El ciudadano ID {ciudadano.id} no está habilitado para inscribirse en este centro adherido."
            )
    except Exception as e:
        logger.error("Ocurrió un error inesperado en validar_ciudadano_en_rango_para_actividad", exc_info=True)
        raise

class ActividadService:
    @staticmethod
    def obtener_o_error(actividad_id):
        try:
            actividad = ActividadCentro.objects.filter(pk=actividad_id).first()
            if not actividad:
                raise LookupError("Actividad no encontrada.")
            return actividad
        except Exception as e:
            logger.error("Ocurrió un error inesperado en obtener_o_error", exc_info=True)
            raise

class ParticipanteService:
    @staticmethod
    def contar_participantes_por_actividad(actividad_centro):
        try:
            return ParticipanteActividad.objects.filter(
                actividad_centro=actividad_centro
            ).count()
        except Exception as e:
            logger.error("Ocurrió un error inesperado en contar_participantes_por_actividad", exc_info=True)
            return 0

    @staticmethod
    def cargar_participantes_desde_lista(lista_dnis, actividad_centro):
        """Carga masiva desde una lista de documentos (DNI)"""
        try:
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
        except Exception as e:
            logger.error("Ocurrió un error inesperado en cargar_participantes_desde_lista", exc_info=True)
            return 0

    @staticmethod
    def crear_ciudadano_con_dimensiones(datos):
        try:
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
        except Exception as e:
            logger.error("Ocurrió un error inesperado en crear_ciudadano_con_dimensiones", exc_info=True)
            return None

    @staticmethod
    def crear_participante(actividad_id, ciudadano):
        try:
            return ParticipanteActividad.objects.create(
                actividad_centro_id=actividad_id, ciudadano=ciudadano
            )
        except Exception as e:
            logger.error("Ocurrió un error inesperado en crear_participante", exc_info=True)
            return None

    @staticmethod
    def validar_ciudadano(ciudadano, actividad_centro):
        try:
            validar_ciudadano_en_rango_para_actividad(ciudadano, actividad_centro)
        except Exception as e:
            logger.error("Ocurrió un error inesperado en validar_ciudadano", exc_info=True)
            raise

    @staticmethod
    def asignar_programa(ciudadano, usuario, programa_id=1):
        try:
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
        except Exception as e:
            logger.error("Ocurrió un error inesperado en asignar_programa", exc_info=True)

    @classmethod
    def procesar_creacion(cls, usuario, actividad_id, datos=None, ciudadano_id=None):
        try:
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
        except Exception as e:
            logger.error("Ocurrió un error inesperado en procesar_creacion", exc_info=True)
            raise

    @staticmethod
    def buscar_ciudadanos(query, max_results=10):
        try:
            cleaned = (query or "").strip()
            if len(cleaned) < 4 or not cleaned.isdigit():
                return []
            qs = Ciudadano.objects.extra(
                where=["CAST(documento AS CHAR) LIKE %s"], params=[cleaned + "%"]
            ).order_by("documento")[:max_results]
            return list(qs)
        except Exception as e:
            logger.error("Ocurrió un error inesperado en buscar_ciudadanos", exc_info=True)
            return []

    @staticmethod
    def obtener_participantes_con_ciudadanos(actividad_centro):
        try:
            return ParticipanteActividad.objects.filter(
                actividad_centro=actividad_centro
            ).select_related("ciudadano")
        except Exception as e:
            logger.error("Ocurrió un error inesperado en obtener_participantes_con_ciudadanos", exc_info=True)
            return ParticipanteActividad.objects.none()