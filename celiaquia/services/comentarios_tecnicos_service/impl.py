"""Comentarios técnicos de legajo y su publicación a la Provincia (issue #2318).

Reglas de negocio que implementa este servicio:

- Cada alta crea un comentario nuevo; nunca se sobrescriben los anteriores.
- Los comentarios nacen **internos**: sólo Nación los ve.
- La Provincia recibe únicamente los que tienen observaciones (``Sí``), y recién
  cuando el técnico solicita una subsanación o rechaza el legajo. Los ``No``
  quedan internos para siempre.
- El motivo de Subsanar/Rechazar se arma **en backend** concatenando esas
  observaciones en orden cronológico y sin duplicados. Lo que muestra la
  pantalla es una previsualización, no la fuente de verdad.
"""

import logging
import re

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from celiaquia.comentarios_tecnicos import (
    CODIGO_OTROS,
    TipoDocumentoComentario,
    es_codigo_valido,
    normalizar_tipo_documento,
    texto_observacion,
)
from celiaquia.models import ExpedienteCiudadano, HistorialComentarios

logger = logging.getLogger("django")

#: Texto que se guarda cuando la revisión no encontró observaciones.
TEXTO_SIN_OBSERVACIONES = "Sin observaciones."

#: Separador entre observaciones dentro del motivo concatenado.
SEPARADOR_OBSERVACIONES = "\n"

#: Separador entre el bloque concatenado y el texto libre complementario.
SEPARADOR_TEXTO_LIBRE = "\n\n"

_VALORES_SI = {"1", "true", "on", "yes", "si", "sí", "s"}
_VALORES_NO = {"0", "false", "off", "no", "n"}

_ESPACIOS = re.compile(r"\s+")


def normalizar_si_no(valor):
    """Interpreta el "¿Tiene observaciones?" del formulario.

    Devuelve ``True``/``False``, o ``None`` si el valor no es interpretable
    (campo vacío o basura), para que quien llama lo trate como falta de dato.
    """
    if isinstance(valor, bool):
        return valor
    texto = str(valor or "").strip().lower()
    if texto in _VALORES_SI:
        return True
    if texto in _VALORES_NO:
        return False
    return None


def _clave_dedup(tipo_documento, observacion_codigo, texto):
    """Clave de deduplicación de una observación.

    Para las observaciones del catálogo alcanza con (tipo, código). Para
    ``OTROS`` el texto es lo que distingue una de otra, así que entra normalizado
    para que dos redacciones idénticas salvo mayúsculas o espacios cuenten como
    una sola.
    """
    texto_normalizado = _ESPACIOS.sub(" ", (texto or "").strip()).casefold()
    return (tipo_documento or "", observacion_codigo or "", texto_normalizado)


class ComentariosTecnicosService:
    """Alta, consulta, concatenación y publicación de comentarios técnicos."""

    @staticmethod
    def registrar(  # pylint: disable=too-many-arguments
        legajo: ExpedienteCiudadano,
        *,
        tipo_documento,
        tiene_observaciones,
        observacion_codigo=None,
        observacion_libre="",
        usuario=None,
    ) -> HistorialComentarios:
        """Registra un comentario técnico interno sobre el legajo.

        Valida la combinación de opciones según el requerimiento: el tipo de
        documento es obligatorio, el Sí/No es obligatorio, y la observación se
        exige sólo cuando la respuesta es ``Sí``. Cuando es ``No`` la
        observación se descarta (la UI la oculta, pero el POST puede arrastrar
        el valor anterior).

        Devuelve el `HistorialComentarios` creado, siempre con
        ``es_interno=True``.
        """
        tipo = normalizar_tipo_documento(tipo_documento)
        if not tipo:
            raise ValidationError("Seleccioná un tipo de documento válido.")

        respuesta = normalizar_si_no(tiene_observaciones)
        if respuesta is None:
            raise ValidationError("Indicá si la revisión tiene observaciones.")

        if not respuesta:
            codigo = None
            texto = TEXTO_SIN_OBSERVACIONES
        else:
            codigo = (observacion_codigo or "").strip().upper()
            if not codigo:
                raise ValidationError("Seleccioná una observación.")
            if not es_codigo_valido(tipo, codigo):
                raise ValidationError(
                    "La observación seleccionada no corresponde al tipo de documento."
                )
            if codigo == CODIGO_OTROS:
                texto = (observacion_libre or "").strip()
                if not texto:
                    raise ValidationError(
                        'Redactá la observación cuando elegís la opción "Otros".'
                    )
            else:
                texto = texto_observacion(tipo, codigo)

        comentario = HistorialComentarios.objects.create(
            legajo=legajo,
            tipo_comentario=HistorialComentarios.TIPO_COMENTARIO_TECNICO,
            comentario=texto,
            usuario=usuario,
            estado_relacionado=legajo.revision_tecnico,
            es_interno=True,
            tipo_documento=tipo,
            tiene_observaciones=respuesta,
            observacion_codigo=codigo,
        )

        logger.info(
            "Comentario técnico registrado: legajo=%s tipo=%s observaciones=%s "
            "codigo=%s user=%s",
            legajo.pk,
            tipo,
            respuesta,
            codigo,
            getattr(usuario, "id", None),
        )
        return comentario

    @staticmethod
    def historial(legajo: ExpedienteCiudadano):
        """Comentarios técnicos del legajo en orden cronológico ascendente."""
        return (
            legajo.historial_comentarios.filter(
                tipo_comentario=HistorialComentarios.TIPO_COMENTARIO_TECNICO
            )
            .select_related("usuario")
            .order_by("fecha_creacion", "pk")
        )

    @staticmethod
    def deduplicar(comentarios):
        """Descarta las observaciones repetidas conservando la primera de cada una.

        Se usa tanto para armar el motivo como para no mostrarle a la Provincia
        la misma observación varias veces: el técnico puede registrarla más de
        una vez y el historial interno las conserva todas.
        """
        vistos = set()
        unicos = []
        for comentario in comentarios:
            clave = _clave_dedup(
                comentario.tipo_documento,
                comentario.observacion_codigo,
                comentario.comentario,
            )
            if clave in vistos:
                continue
            vistos.add(clave)
            unicos.append(comentario)
        return unicos

    @staticmethod
    def observaciones_publicables(legajo: ExpedienteCiudadano):
        """Comentarios técnicos con observaciones (``Sí``), cronológicos y sin
        duplicados.

        Son los únicos que se le comunican a la Provincia y los que alimentan el
        motivo de Subsanar y Rechazar.
        """
        return ComentariosTecnicosService.deduplicar(
            ComentariosTecnicosService.historial(legajo).filter(
                tiene_observaciones=True
            )
        )

    @staticmethod
    def lineas_concatenadas(legajo: ExpedienteCiudadano):
        """Observaciones publicables como líneas de texto, prefijadas por tipo."""
        etiquetas = dict(TipoDocumentoComentario.choices)
        return [
            f"{etiquetas.get(c.tipo_documento, c.tipo_documento)}: {c.comentario}"
            for c in ComentariosTecnicosService.observaciones_publicables(legajo)
        ]

    @staticmethod
    def texto_concatenado(legajo: ExpedienteCiudadano) -> str:
        """Concatenación de las observaciones publicables. "" si no hay ninguna."""
        return SEPARADOR_OBSERVACIONES.join(
            ComentariosTecnicosService.lineas_concatenadas(legajo)
        )

    @staticmethod
    def componer_motivo(legajo: ExpedienteCiudadano, texto_libre: str = "") -> str:
        """Motivo final de una subsanación o un rechazo.

        Une las observaciones técnicas concatenadas con el texto libre
        complementario, que es opcional. Si el legajo no tiene observaciones
        registradas, el texto libre pasa a ser obligatorio: sin ninguno de los
        dos no hay motivo que comunicar y se corta con `ValidationError` sin
        tocar el estado del legajo.
        """
        concatenado = ComentariosTecnicosService.texto_concatenado(legajo)
        libre = (texto_libre or "").strip()

        if not concatenado and not libre:
            raise ValidationError(
                "El legajo no tiene comentarios técnicos con observaciones: "
                "completá el texto libre para poder continuar."
            )

        partes = [parte for parte in (concatenado, libre) if parte]
        return SEPARADOR_TEXTO_LIBRE.join(partes)

    @staticmethod
    def publicar(legajo: ExpedienteCiudadano, usuario=None) -> int:
        """Publica a la Provincia los comentarios técnicos con observaciones.

        Baja el flag `es_interno` y sella `publicado_en`/`publicado_por`, que es
        el registro de auditoría de la publicación. Los comentarios sin
        observaciones quedan internos, y los ya publicados conservan la fecha y
        el usuario del evento original.

        Devuelve la cantidad de comentarios publicados en esta llamada.
        """
        publicados = legajo.historial_comentarios.filter(
            Q(tipo_comentario=HistorialComentarios.TIPO_COMENTARIO_TECNICO)
            & Q(tiene_observaciones=True)
            & Q(es_interno=True)
        ).update(
            es_interno=False,
            publicado_en=timezone.now(),
            publicado_por=usuario,
        )

        if publicados:
            logger.info(
                "Comentarios técnicos publicados a Provincia: legajo=%s cantidad=%s "
                "user=%s",
                legajo.pk,
                publicados,
                getattr(usuario, "id", None),
            )
        return publicados
