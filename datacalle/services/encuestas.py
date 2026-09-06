"""Lógica de negocio de los casos (encuestas) de DataCalle.

El instrumento viaja completo en ``respuestas``; acá sólo se copian a columnas
indexadas los pocos datos que necesitan tableros y filtros, y se resuelven las
reglas de negocio del upsert (D2.5 y D2.7).
"""

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from datacalle.models import Encuesta, Relevamiento


def _texto(respuestas, clave):
    valor = respuestas.get(clave)
    if valor in (None, ""):
        return ""
    return str(valor)[:64]


def _si_no(respuestas, clave):
    """Los catálogos usan ``si``/``no``; devuelve ``None`` si no vino la clave."""
    valor = respuestas.get(clave)
    if valor is None:
        return None
    return str(valor).strip().lower() == "si"


def _entero(respuestas, clave):
    try:
        return int(respuestas.get(clave))
    except (TypeError, ValueError):
        return None


def _coordenadas(respuestas):
    """Saca lat/lon de ``ubicacionGrupo`` descartando el 0,0 y los fuera de rango."""
    ubicacion = respuestas.get("ubicacionGrupo")
    if not isinstance(ubicacion, dict):
        return None, None
    try:
        lat = float(ubicacion.get("lat"))
        lon = float(ubicacion.get("lon"))
    except (TypeError, ValueError):
        return None, None
    if abs(lat) > 90 or abs(lon) > 180:
        return None, None
    if lat == 0 and lon == 0:
        return None, None
    return lat, lon


def aplicar_columnas_indexadas(encuesta):
    """Copia de ``respuestas`` a las columnas indexadas (D2.9)."""
    respuestas = encuesta.respuestas or {}
    encuesta.grupo_id = _texto(respuestas, "grupoId")
    encuesta.es_cabecera_grupo = bool(_si_no(respuestas, "esCabeceraGrupo"))
    encuesta.persona_entrevistada = _texto(respuestas, "personaEntrevistada")
    encuesta.personas_observadas = _entero(respuestas, "personasObservadas")
    encuesta.realiza_entrevista = _texto(respuestas, "realizaEntrevista")
    encuesta.codigo_entrevistado = _texto(respuestas, "codigoEntrevistado")
    encuesta.lugar_hallazgo = _texto(respuestas, "lugarHallazgo")
    encuesta.es_menor_de_edad = _si_no(respuestas, "esMenorDeEdad")
    encuesta.lat, encuesta.lon = _coordenadas(respuestas)
    return encuesta


class RelevamientoCerrado(Exception):
    """El operativo ya está finalizado y no admite más casos (409)."""


@transaction.atomic
def upsert_encuesta(*, encuesta_id, relevamiento, datos, user, origen=None):
    """Alta o actualización idempotente de un caso por UUID.

    Reintentar con el mismo UUID actualiza, no duplica. Con el primer caso el
    relevamiento pasa a ``en_curso``.
    """
    if relevamiento.estado == Relevamiento.Estado.FINALIZADO:
        raise RelevamientoCerrado()

    encuesta = Encuesta.all_objects.filter(pk=encuesta_id).first()
    creada = encuesta is None
    if creada:
        encuesta = Encuesta(id=encuesta_id, relevamiento=relevamiento)
        encuesta.origen = origen or Encuesta.Origen.APP
        encuesta.relevador = user
    elif encuesta.deleted_at is not None:
        # Reenviar un caso borrado lo revive: la app es la fuente de verdad.
        encuesta.deleted_at = None
        encuesta.deleted_by = None

    encuesta.relevamiento = relevamiento
    for campo in ("variante", "estado", "fecha_inicio", "fecha_hora_fin"):
        if campo in datos:
            setattr(encuesta, campo, datos[campo])
    if "respuestas" in datos:
        encuesta.respuestas = datos["respuestas"] or {}

    aplicar_columnas_indexadas(encuesta)
    encuesta.save()

    if relevamiento.estado == Relevamiento.Estado.PLANIFICADO:
        relevamiento.estado = Relevamiento.Estado.EN_CURSO
        relevamiento.save(update_fields=["estado", "updated_at"])

    return encuesta, creada


@transaction.atomic
def cerrar_relevamiento(*, relevamiento, user, datos=None):
    """Cierre desde la app, con los datos de campo del recorrido (D2.5).

    Es idempotente: cerrar dos veces no es un error para la app, que reintenta
    desde la outbox.
    """
    datos = datos or {}
    ya_estaba_cerrado = relevamiento.estado == Relevamiento.Estado.FINALIZADO
    if ya_estaba_cerrado:
        return relevamiento, False

    relevamiento.estado = Relevamiento.Estado.FINALIZADO
    relevamiento.fecha_cierre = datos.get("fecha_cierre") or timezone.now()
    relevamiento.cerrado_por = user
    if datos.get("lat") is not None:
        relevamiento.lat = datos["lat"]
    if datos.get("lon") is not None:
        relevamiento.lon = datos["lon"]
    if datos.get("observacion_asentamiento") is not None:
        relevamiento.observacion_asentamiento = datos["observacion_asentamiento"]
    if datos.get("otra_observacion") is not None:
        relevamiento.otra_observacion = datos["otra_observacion"] or ""
    relevamiento.save()
    return relevamiento, True


def get_encuestas_queryset(relevamiento=None):
    queryset = Encuesta.objects.select_related("relevamiento", "relevador")
    if relevamiento is not None:
        queryset = queryset.filter(relevamiento=relevamiento)
    return queryset


def resumen_de_casos(relevamiento):
    """Números del operativo, con las reglas de conteo del instrumento 2026.

    "Personas observadas" se suma **sólo** de los casos cabecera de grupo: el
    módulo observacional se carga una vez y los demás casos del grupo lo
    heredan, así que sumar todos multiplicaría el total (D2.9).
    """
    casos = get_encuestas_queryset(relevamiento)
    personas = (
        casos.filter(es_cabecera_grupo=True).aggregate(
            total=Sum("personas_observadas")
        )["total"]
        or 0
    )
    return {
        "casos": casos.count(),
        "personas_observadas": personas,
        "entrevistas": casos.filter(realiza_entrevista="si").count(),
        # "Rechazada" mezcla dos cosas: quien no quiso o no pudo responder y el
        # menor de edad a quien no correspondía preguntarle. Se separan mirando
        # si `realizaEntrevista` llegó o no.
        "sin_entrevista": casos.filter(estado=Encuesta.Estado.RECHAZADA)
        .exclude(realiza_entrevista="")
        .count(),
        "menores": casos.filter(es_menor_de_edad=True, realiza_entrevista="").count(),
    }
