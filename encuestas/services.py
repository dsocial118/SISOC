from __future__ import annotations

import logging
import os
import time
from decimal import Decimal, InvalidOperation
from typing import Iterable

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Prefetch, Q
from django.utils import timezone
from django.utils.dateparse import parse_date

from .models import (
    Encuesta,
    CumplimientoRonda,
    EstadoEncuesta,
    EstadoRonda,
    OpcionPregunta,
    OperadorCondicion,
    Pregunta,
    RecordatorioUsuario,
    RespuestaPregunta,
    RespuestaRonda,
    RondaEncuesta,
    SegmentacionDestinatario,
    SegmentacionEncuesta,
    TipoDocumento,
    TipoPregunta,
    TipoSegmentacion,
)
from .validators import parse_listado_destinatarios, parse_preguntas_payload

logger = logging.getLogger("django")


class RondaAbiertaError(ValidationError):
    """La operación requiere que la encuesta no tenga una ronda abierta."""


def get_encuestas_queryset():
    return Encuesta.objects.select_related("usuario_creador", "version_de").order_by(
        "-fecha_creacion"
    )


def tiene_ronda_abierta(encuesta) -> bool:
    return encuesta.rondas.filter(estado=EstadoRonda.ABIERTA).exists()


def crear_encuesta(*, usuario, **campos) -> Encuesta:
    encuesta = Encuesta(
        usuario_creador=usuario, usuario_ultima_modificacion=usuario, **campos
    )
    encuesta.full_clean()
    encuesta.save()
    return encuesta


def _clonar_preguntas(encuesta_origen: Encuesta, encuesta_destino: Encuesta) -> None:
    mapa_preguntas: dict[int, Pregunta] = {}
    for pregunta in encuesta_origen.preguntas.order_by("orden"):
        nueva_pregunta = Pregunta.objects.create(
            encuesta=encuesta_destino,
            texto=pregunta.texto,
            tipo=pregunta.tipo,
            obligatoria=pregunta.obligatoria,
            orden=pregunta.orden,
        )
        mapa_preguntas[pregunta.pk] = nueva_pregunta
        OpcionPregunta.objects.bulk_create(
            OpcionPregunta(
                pregunta=nueva_pregunta,
                texto=opcion.texto,
                valor=opcion.valor,
                orden=opcion.orden,
            )
            for opcion in pregunta.opciones.order_by("orden")
        )

    for pregunta in encuesta_origen.preguntas.exclude(pregunta_condicion__isnull=True):
        nueva_pregunta = mapa_preguntas[pregunta.pk]
        nueva_pregunta.pregunta_condicion = mapa_preguntas.get(
            pregunta.pregunta_condicion_id
        )
        nueva_pregunta.operador_condicion = pregunta.operador_condicion
        nueva_pregunta.valor_condicion = pregunta.valor_condicion
        nueva_pregunta.save(
            update_fields=[
                "pregunta_condicion",
                "operador_condicion",
                "valor_condicion",
            ]
        )


def _clonar_segmentacion(encuesta_origen: Encuesta, encuesta_destino: Encuesta) -> None:
    segmentacion_actual = getattr(encuesta_origen, "segmentacion", None)
    if segmentacion_actual is None:
        return
    nueva_segmentacion = SegmentacionEncuesta.objects.create(
        encuesta=encuesta_destino, tipo=segmentacion_actual.tipo
    )
    SegmentacionDestinatario.objects.bulk_create(
        SegmentacionDestinatario(
            segmentacion=nueva_segmentacion,
            tipo_documento=destinatario.tipo_documento,
            numero_documento=destinatario.numero_documento,
        )
        for destinatario in segmentacion_actual.destinatarios.all()
    )


def nueva_version(encuesta: Encuesta, *, usuario, **campos) -> Encuesta:
    if tiene_ronda_abierta(encuesta):
        raise RondaAbiertaError(
            "No se puede editar una encuesta mientras tenga una ronda abierta."
        )

    datos_version = {
        "titulo": encuesta.titulo,
        "descripcion": encuesta.descripcion,
        "es_anonima": encuesta.es_anonima,
        "es_obligatoria": encuesta.es_obligatoria,
        "intervalo_recordatorio_dias": encuesta.intervalo_recordatorio_dias,
        "es_recurrente": encuesta.es_recurrente,
        "intervalo_recurrencia_dias": encuesta.intervalo_recurrencia_dias,
        "duracion_ronda_dias": encuesta.duracion_ronda_dias,
    }
    datos_version.update(campos)

    nueva = Encuesta(
        version_de=encuesta,
        version=encuesta.version + 1,
        estado=EstadoEncuesta.BORRADOR,
        usuario_creador=encuesta.usuario_creador,
        usuario_ultima_modificacion=usuario,
        **datos_version,
    )
    nueva.full_clean()
    nueva.save()

    _clonar_preguntas(encuesta, nueva)
    _clonar_segmentacion(encuesta, nueva)
    return nueva


def actualizar_encuesta(encuesta: Encuesta, *, usuario, **campos) -> Encuesta:
    if tiene_ronda_abierta(encuesta):
        raise RondaAbiertaError(
            "No se puede editar una encuesta mientras tenga una ronda abierta."
        )

    if encuesta.rondas.exists():
        return nueva_version(encuesta, usuario=usuario, **campos)

    for campo, valor in campos.items():
        setattr(encuesta, campo, valor)
    encuesta.usuario_ultima_modificacion = usuario
    encuesta.full_clean()
    encuesta.save()
    return encuesta


def publicar(encuesta: Encuesta, *, usuario) -> RondaEncuesta:
    if encuesta.estado != EstadoEncuesta.BORRADOR:
        raise ValidationError("Solo se puede publicar una encuesta en borrador.")
    if not encuesta.preguntas.exists():
        raise ValidationError(
            "La encuesta debe tener al menos una pregunta para publicarse."
        )
    if not hasattr(encuesta, "segmentacion"):
        raise ValidationError(
            "La encuesta debe tener una segmentación configurada para publicarse."
        )

    encuesta.estado = EstadoEncuesta.PUBLICADA
    encuesta.usuario_ultima_modificacion = usuario
    encuesta.save(
        update_fields=[
            "estado",
            "usuario_ultima_modificacion",
            "fecha_ultima_modificacion",
        ]
    )
    return abrir_ronda(encuesta)


def abrir_ronda(encuesta: Encuesta, *, fecha_apertura=None) -> RondaEncuesta:
    if encuesta.estado != EstadoEncuesta.PUBLICADA:
        raise ValidationError("Solo se pueden abrir rondas de encuestas publicadas.")
    if tiene_ronda_abierta(encuesta):
        raise RondaAbiertaError("La encuesta ya tiene una ronda abierta.")

    apertura = fecha_apertura or timezone.now()
    numero_ronda = encuesta.rondas.count() + 1
    return RondaEncuesta.objects.create(
        encuesta=encuesta,
        numero_ronda=numero_ronda,
        fecha_apertura=apertura,
        fecha_cierre_programada=apertura
        + timezone.timedelta(days=encuesta.duracion_ronda_dias),
    )


def cerrar_ronda(ronda: RondaEncuesta, *, manual: bool = True) -> RondaEncuesta:
    if ronda.estado != EstadoRonda.ABIERTA:
        raise ValidationError("La ronda ya está cerrada.")

    ronda.estado = EstadoRonda.CERRADA
    ronda.fecha_cierre_real = timezone.now()
    ronda.cerrada_manualmente = manual
    ronda.save(update_fields=["estado", "fecha_cierre_real", "cerrada_manualmente"])
    return ronda


def reemplazar_preguntas(encuesta: Encuesta, preguntas_raw_json: str) -> None:
    """Reemplaza todas las preguntas de la encuesta a partir del JSON armado por
    el editor dinámico (ver validators.parse_preguntas_payload)."""
    if tiene_ronda_abierta(encuesta):
        raise RondaAbiertaError(
            "No se pueden modificar las preguntas mientras la encuesta tenga una "
            "ronda abierta."
        )

    preguntas = parse_preguntas_payload(preguntas_raw_json)

    encuesta.preguntas.all().delete()

    mapa_orden_a_pregunta: dict[int, Pregunta] = {}
    for parsed in preguntas:
        pregunta = Pregunta(
            encuesta=encuesta,
            texto=parsed.texto,
            tipo=parsed.tipo,
            obligatoria=parsed.obligatoria,
            orden=parsed.orden,
        )
        pregunta.full_clean()
        pregunta.save()
        mapa_orden_a_pregunta[parsed.orden] = pregunta
        OpcionPregunta.objects.bulk_create(
            OpcionPregunta(
                pregunta=pregunta, texto=texto_opcion, valor=texto_opcion, orden=indice
            )
            for indice, texto_opcion in enumerate(parsed.opciones, start=1)
        )

    for parsed in preguntas:
        if not parsed.condicion:
            continue
        pregunta = mapa_orden_a_pregunta[parsed.orden]
        pregunta.pregunta_condicion = mapa_orden_a_pregunta[
            parsed.condicion.orden_referencia
        ]
        pregunta.operador_condicion = parsed.condicion.operador
        pregunta.valor_condicion = parsed.condicion.valor
        pregunta.full_clean()
        pregunta.save(
            update_fields=[
                "pregunta_condicion",
                "operador_condicion",
                "valor_condicion",
            ]
        )


def serializar_preguntas(encuesta: Encuesta) -> list[dict]:
    """Serializa las preguntas de una encuesta al mismo formato que produce el
    editor dinámico, para prellenarlo al editar."""
    preguntas = list(encuesta.preguntas.order_by("orden").prefetch_related("opciones"))
    orden_por_pk = {pregunta.pk: pregunta.orden for pregunta in preguntas}

    resultado = []
    for pregunta in preguntas:
        item = {
            "orden": pregunta.orden,
            "texto": pregunta.texto,
            "tipo": pregunta.tipo,
            "obligatoria": pregunta.obligatoria,
            "opciones": [opcion.texto for opcion in pregunta.opciones.all()],
            "condicion": None,
        }
        if pregunta.pregunta_condicion_id:
            item["condicion"] = {
                "orden": orden_por_pk.get(pregunta.pregunta_condicion_id),
                "operador": pregunta.operador_condicion,
                "valor": pregunta.valor_condicion,
            }
        resultado.append(item)
    return resultado


def actualizar_segmentacion(
    encuesta: Encuesta,
    *,
    tipo: str,
    archivo=None,
    destinatarios: Iterable[dict] | None = None,
) -> SegmentacionEncuesta:
    segmentacion, _ = SegmentacionEncuesta.objects.get_or_create(
        encuesta=encuesta, defaults={"tipo": tipo}
    )
    segmentacion.tipo = tipo
    if archivo is not None:
        segmentacion.archivo_listado = archivo
    segmentacion.full_clean()
    segmentacion.save()

    if tipo != TipoSegmentacion.LISTADO_DOCUMENTOS:
        segmentacion.destinatarios.all().delete()
        return segmentacion

    if archivo is not None:
        filas = parse_listado_destinatarios(archivo)
        nuevos = {(fila.tipo_documento, fila.numero_documento) for fila in filas}
    elif destinatarios is not None:
        nuevos = {(d["tipo_documento"], d["numero_documento"]) for d in destinatarios}
    else:
        return segmentacion

    existentes = {
        (destinatario.tipo_documento, destinatario.numero_documento): destinatario
        for destinatario in segmentacion.destinatarios.all()
    }
    a_crear = nuevos - existentes.keys()
    a_borrar = existentes.keys() - nuevos

    SegmentacionDestinatario.objects.bulk_create(
        SegmentacionDestinatario(
            segmentacion=segmentacion, tipo_documento=tipo_doc, numero_documento=numero
        )
        for tipo_doc, numero in a_crear
    )
    if a_borrar:
        ids_a_borrar = [existentes[clave].pk for clave in a_borrar]
        SegmentacionDestinatario.objects.filter(pk__in=ids_a_borrar).delete()

    return segmentacion


def agregar_destinatario(
    encuesta: Encuesta, *, tipo_documento: str, numero_documento: str
) -> SegmentacionDestinatario:
    """Alta individual de un destinatario, sin reemplazar todo el listado.

    A diferencia de actualizar_encuesta/reemplazar_preguntas, esto no
    verifica tiene_ronda_abierta a propósito: la segmentación se puede
    modificar "en caliente" con la ronda ya abierta (regla de negocio 12).
    """
    segmentacion, _ = SegmentacionEncuesta.objects.get_or_create(
        encuesta=encuesta, defaults={"tipo": TipoSegmentacion.LISTADO_DOCUMENTOS}
    )
    if segmentacion.tipo != TipoSegmentacion.LISTADO_DOCUMENTOS:
        raise ValidationError(
            "Solo se pueden agregar destinatarios individuales cuando el tipo "
            "de segmentación es 'Listado de documentos'."
        )

    tipo_documento = (tipo_documento or "").strip().lower()
    numero_documento = (numero_documento or "").strip()
    if tipo_documento not in TipoDocumento.values:
        raise ValidationError("Tipo de documento inválido.")
    if not numero_documento.isdigit():
        raise ValidationError("El número de documento debe ser numérico.")

    destinatario, _ = SegmentacionDestinatario.objects.get_or_create(
        segmentacion=segmentacion,
        tipo_documento=tipo_documento,
        numero_documento=numero_documento,
    )
    return destinatario


def quitar_destinatario(encuesta: Encuesta, destinatario_pk: int) -> None:
    """Baja individual de un destinatario (ver nota de agregar_destinatario
    sobre aplicar cambios en caliente con la ronda abierta)."""
    segmentacion = getattr(encuesta, "segmentacion", None)
    if segmentacion is None:
        raise ValidationError("La encuesta no tiene segmentación configurada.")

    borrados, _ = segmentacion.destinatarios.filter(pk=destinatario_pk).delete()
    if not borrados:
        raise ValidationError("El destinatario no existe en esta segmentación.")


def _documentos_de_usuario(usuario) -> set[tuple[str, str]]:
    """Documentos con los que un usuario puede matchear una segmentación.

    El perfil conserva CUIL, no un CUIT separado. Para la segmentación, ambos
    tipos se comparan contra el mismo valor numérico: permite incluir a una
    persona cuando el listado la identifica como CUIT.
    """
    profile = getattr(usuario, "profile", None)
    if profile is None:
        return set()
    documentos = set()
    if profile.dni:
        documentos.add((TipoDocumento.DNI, profile.dni))
    if profile.cuil:
        documentos.add((TipoDocumento.CUIL, profile.cuil))
        documentos.add((TipoDocumento.CUIT, profile.cuil))
    return documentos


def _construir_filtro_documentos(documentos: set[tuple[str, str]]) -> Q:
    """Construye el filtro de destinatarios para los documentos del usuario."""
    filtro = Q()
    for tipo_documento, numero_documento in documentos:
        filtro |= Q(tipo_documento=tipo_documento, numero_documento=numero_documento)
    return filtro


def usuario_esta_segmentado(encuesta: Encuesta, usuario) -> bool:
    segmentacion = getattr(encuesta, "segmentacion", None)
    if segmentacion is None:
        return False
    if segmentacion.tipo == TipoSegmentacion.TODOS_LOS_USUARIOS:
        return True

    documentos = _documentos_de_usuario(usuario)
    if not documentos:
        return False
    filtro_documentos = _construir_filtro_documentos(documentos)
    destinatarios_usuario = getattr(segmentacion, "destinatarios_usuario", None)
    if destinatarios_usuario is not None:
        return bool(destinatarios_usuario)
    return segmentacion.destinatarios.filter(filtro_documentos).exists()


def get_rondas_pendientes(usuario) -> list[RondaEncuesta]:
    """Rondas abiertas que le corresponden a ``usuario``, en cola por fecha de
    vencimiento más próxima (regla de negocio 12)."""
    ahora = timezone.now()
    documentos = _documentos_de_usuario(usuario)
    destinatarios_queryset = SegmentacionDestinatario.objects.none()
    if documentos:
        destinatarios_queryset = SegmentacionDestinatario.objects.filter(
            _construir_filtro_documentos(documentos)
        )

    candidatas = list(
        RondaEncuesta.objects.filter(
            estado=EstadoRonda.ABIERTA,
            fecha_cierre_programada__gt=ahora,
        )
        .exclude(cumplimientos__usuario=usuario)
        .select_related("encuesta", "encuesta__segmentacion")
        .prefetch_related(
            Prefetch(
                "encuesta__segmentacion__destinatarios",
                queryset=destinatarios_queryset,
                to_attr="destinatarios_usuario",
            ),
            Prefetch(
                "recordatorios",
                queryset=RecordatorioUsuario.objects.filter(usuario=usuario),
                to_attr="recordatorios_usuario",
            ),
        )
        .order_by("fecha_cierre_programada")
    )

    pendientes = []
    for ronda in candidatas:
        if not usuario_esta_segmentado(ronda.encuesta, usuario):
            continue
        recordatorio = next(iter(ronda.recordatorios_usuario), None)
        if recordatorio and recordatorio.fecha_proximo_aviso > ahora:
            continue
        pendientes.append(ronda)
    return pendientes


_RONDAS_PENDIENTES_REQUEST_CACHE_ATTR = "_encuestas_rondas_pendientes_cache"


def get_rondas_pendientes_para_request(request) -> list[RondaEncuesta]:
    """Wrapper de get_rondas_pendientes cacheado en el propio ``request``.

    EncuestaObligatoriaMiddleware y el context processor ronda_pendiente
    necesitan el mismo dato en el mismo request (uno para bloquear, el otro
    para mostrar el modal); sin este cache cada uno dispara su propia
    consulta, duplicando el costo en cada página del sistema.
    """
    usuario = getattr(request, "user", None)
    if not usuario or not getattr(usuario, "is_authenticated", False):
        return []

    cache = getattr(request, _RONDAS_PENDIENTES_REQUEST_CACHE_ATTR, None)
    if cache is None:
        cache = get_rondas_pendientes(usuario)
        setattr(request, _RONDAS_PENDIENTES_REQUEST_CACHE_ATTR, cache)
    return cache


def posponer_ronda(ronda: RondaEncuesta, usuario) -> RecordatorioUsuario:
    if ronda.encuesta.es_obligatoria:
        raise ValidationError("Esta encuesta es obligatoria y no se puede posponer.")

    intervalo_dias = ronda.encuesta.intervalo_recordatorio_dias or 1
    proximo_aviso = timezone.now() + timezone.timedelta(days=intervalo_dias)
    recordatorio, _ = RecordatorioUsuario.objects.update_or_create(
        ronda=ronda, usuario=usuario, defaults={"fecha_proximo_aviso": proximo_aviso}
    )
    return recordatorio


def _pregunta_es_visible(pregunta: Pregunta, post_data, preguntas_por_orden) -> bool:
    if not pregunta.pregunta_condicion_id:
        return True
    referencia = preguntas_por_orden.get(pregunta.pregunta_condicion.orden)
    if referencia is None:
        return True

    if referencia.tipo == TipoPregunta.OPCION_MULTIPLE:
        cumple = pregunta.valor_condicion in post_data.getlist(
            f"respuesta-{referencia.pk}"
        )
    else:
        cumple = post_data.get(f"respuesta-{referencia.pk}") == pregunta.valor_condicion

    if pregunta.operador_condicion == OperadorCondicion.DISTINTO:
        return not cumple
    return cumple


def _asignar_valor_numerico(
    respuesta_pregunta: RespuestaPregunta, pregunta, valor
) -> None:
    try:
        respuesta_pregunta.valor_numero = Decimal(valor)
    except InvalidOperation as exc:
        raise ValidationError(
            f"La respuesta a '{pregunta.texto}' debe ser numérica."
        ) from exc
    if not respuesta_pregunta.valor_numero.is_finite():
        raise ValidationError(f"La respuesta a '{pregunta.texto}' debe ser numérica.")
    if pregunta.tipo == TipoPregunta.ESCALA and not (
        Decimal("1") <= respuesta_pregunta.valor_numero <= Decimal("10")
    ):
        raise ValidationError(
            f"La respuesta a '{pregunta.texto}' debe estar entre 1 y 10."
        )


def _asignar_valor_respuesta(
    respuesta_pregunta: RespuestaPregunta, pregunta: Pregunta, post_data
) -> None:
    if pregunta.tipo == TipoPregunta.OPCION_UNICA:
        valor = post_data.get(f"respuesta-{pregunta.pk}")
        opcion = pregunta.opciones.filter(valor=valor).first()
        if opcion is None:
            raise ValidationError(f"La respuesta a '{pregunta.texto}' no es válida.")
        respuesta_pregunta.save()
        respuesta_pregunta.opciones_seleccionadas.add(opcion)
        return

    if pregunta.tipo == TipoPregunta.OPCION_MULTIPLE:
        valores = post_data.getlist(f"respuesta-{pregunta.pk}")
        opciones = pregunta.opciones.filter(valor__in=valores)
        if opciones.count() != len(set(valores)):
            raise ValidationError(f"La respuesta a '{pregunta.texto}' no es válida.")
        respuesta_pregunta.save()
        respuesta_pregunta.opciones_seleccionadas.set(opciones)
        return

    valor = post_data.get(f"respuesta-{pregunta.pk}", "")
    if pregunta.tipo in (TipoPregunta.NUMERICO, TipoPregunta.ESCALA):
        _asignar_valor_numerico(respuesta_pregunta, pregunta, valor)
    elif pregunta.tipo == TipoPregunta.FECHA:
        parsed = parse_date(valor)
        if not parsed:
            raise ValidationError(
                f"La respuesta a '{pregunta.texto}' debe ser una fecha válida."
            )
        respuesta_pregunta.valor_fecha = parsed
    elif pregunta.tipo == TipoPregunta.SI_NO:
        if valor not in {"si", "no"}:
            raise ValidationError(f"La respuesta a '{pregunta.texto}' no es válida.")
        respuesta_pregunta.valor_texto = valor
    else:
        respuesta_pregunta.valor_texto = valor
    respuesta_pregunta.save()


def registrar_respuesta(ronda: RondaEncuesta, usuario, post_data) -> RespuestaRonda:
    """Registra la respuesta de ``usuario`` a ``ronda`` a partir del POST del
    modal (ver encuestas/templates/encuestas/partials/responder_modal.html).

    El contenido no se vincula a la identidad en encuestas anónimas: el
    cumplimiento se persiste por separado, sin referencia a la respuesta.
    """
    if ronda.estado != EstadoRonda.ABIERTA:
        raise ValidationError("Esta ronda ya no acepta respuestas.")
    if ronda.fecha_cierre_programada <= timezone.now():
        raise ValidationError("Esta ronda ya no acepta respuestas.")
    if CumplimientoRonda.objects.filter(ronda=ronda, usuario=usuario).exists():
        raise ValidationError("Ya respondiste esta encuesta.")
    if not usuario_esta_segmentado(ronda.encuesta, usuario):
        raise ValidationError("No estás habilitado para responder esta encuesta.")

    preguntas = list(
        ronda.encuesta.preguntas.order_by("orden").prefetch_related("opciones")
    )
    preguntas_por_orden = {pregunta.orden: pregunta for pregunta in preguntas}

    # Atómico a propósito: si una pregunta obligatoria posterior falla la
    # validación, no debe quedar una RespuestaRonda ni RespuestaPregunta a
    # medio completar (regla de negocio: no se guardan respuestas parciales).
    try:
        with transaction.atomic():
            respuesta_ronda = RespuestaRonda.objects.create(
                ronda=ronda,
                usuario=None if ronda.encuesta.es_anonima else usuario,
            )

            for pregunta in preguntas:
                if not _pregunta_es_visible(pregunta, post_data, preguntas_por_orden):
                    continue

                tiene_valor = bool(
                    post_data.getlist(f"respuesta-{pregunta.pk}")
                    if pregunta.tipo == TipoPregunta.OPCION_MULTIPLE
                    else post_data.get(f"respuesta-{pregunta.pk}")
                )
                if not tiene_valor:
                    if pregunta.obligatoria:
                        raise ValidationError(
                            f"La pregunta '{pregunta.texto}' es obligatoria."
                        )
                    continue

                respuesta_pregunta = RespuestaPregunta(
                    respuesta_ronda=respuesta_ronda, pregunta=pregunta
                )
                _asignar_valor_respuesta(respuesta_pregunta, pregunta, post_data)

            respuesta_ronda.completa = True
            respuesta_ronda.save(update_fields=["completa"])
            CumplimientoRonda.objects.create(ronda=ronda, usuario=usuario)
    except IntegrityError as exc:
        raise ValidationError("Ya respondiste esta encuesta.") from exc

    RecordatorioUsuario.objects.filter(ronda=ronda, usuario=usuario).delete()
    return respuesta_ronda


DEFAULT_ENCUESTAS_SCHEDULER_POLL_SECONDS = 300


def _poll_seconds_from_env(var_name: str, default: int) -> int:
    try:
        value = int(os.getenv(var_name, ""))
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


def get_encuestas_scheduler_poll_seconds() -> int:
    return _poll_seconds_from_env(
        "ENCUESTAS_SCHEDULER_POLL_SECONDS", DEFAULT_ENCUESTAS_SCHEDULER_POLL_SECONDS
    )


def _debe_abrir_nueva_ronda_recurrente(encuesta: Encuesta, *, ahora) -> bool:
    if not encuesta.es_recurrente or encuesta.estado != EstadoEncuesta.PUBLICADA:
        return False
    if tiene_ronda_abierta(encuesta):
        return False

    ultima_ronda = encuesta.rondas.order_by("-numero_ronda").first()
    if ultima_ronda is None:
        return False

    intervalo_dias = encuesta.intervalo_recurrencia_dias or 0
    proxima_apertura = ultima_ronda.fecha_apertura + timezone.timedelta(
        days=intervalo_dias
    )
    return ahora >= proxima_apertura


def procesar_rondas_pendientes() -> dict[str, int]:
    """Cierra rondas vencidas y abre la siguiente ronda de las encuestas
    recurrentes que ya cumplieron su intervalo. Pensado para correr
    periódicamente desde un worker (ver
    encuestas/management/commands/process_encuestas_rondas.py), no para
    llamarse directamente desde una vista."""
    ahora = timezone.now()

    rondas_cerradas = 0
    for ronda in RondaEncuesta.objects.filter(
        estado=EstadoRonda.ABIERTA, fecha_cierre_programada__lte=ahora
    ):
        cerrar_ronda(ronda, manual=False)
        rondas_cerradas += 1

    rondas_abiertas = 0
    for encuesta in Encuesta.objects.filter(
        es_recurrente=True, estado=EstadoEncuesta.PUBLICADA
    ):
        if _debe_abrir_nueva_ronda_recurrente(encuesta, ahora=ahora):
            abrir_ronda(encuesta, fecha_apertura=ahora)
            rondas_abiertas += 1

    return {"rondas_cerradas": rondas_cerradas, "rondas_abiertas": rondas_abiertas}


def run_encuestas_scheduler(*, once: bool = False) -> None:
    """Loop del worker de encuestas (ver docker-compose.yml: servicio
    encuestas_worker)."""
    logger.info("[encuestas] Scheduler de rondas iniciado.")
    poll_seconds = get_encuestas_scheduler_poll_seconds()

    while True:
        try:
            resultado = procesar_rondas_pendientes()
            if resultado["rondas_cerradas"] or resultado["rondas_abiertas"]:
                logger.info(
                    "[encuestas] %s ronda(s) cerrada(s) automáticamente, "
                    "%s ronda(s) recurrente(s) abierta(s).",
                    resultado["rondas_cerradas"],
                    resultado["rondas_abiertas"],
                )
        except Exception:  # noqa: BLE001 - el worker no debe morir por un ciclo fallido
            logger.exception("[encuestas] Error inesperado en el scheduler de rondas.")

        if once:
            break
        time.sleep(poll_seconds)
