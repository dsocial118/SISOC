from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO

from django.utils import timezone
from django.utils.text import slugify
from openpyxl import Workbook
from openpyxl.styles import Font

from .models import RespuestaPregunta, RondaEncuesta, TipoPregunta

TIPOS_CON_DISTRIBUCION = (
    TipoPregunta.OPCION_UNICA,
    TipoPregunta.OPCION_MULTIPLE,
    TipoPregunta.SI_NO,
)
TIPOS_NUMERICOS = (TipoPregunta.NUMERICO, TipoPregunta.ESCALA)
ETIQUETAS_SI_NO = {"si": "Sí", "no": "No"}


@dataclass
class OpcionResultado:
    texto: str
    cantidad: int
    porcentaje: float


@dataclass
class ResultadoPregunta:
    pregunta_id: int
    texto: str
    tipo: str
    total_respuestas: int
    opciones: list[OpcionResultado] = field(default_factory=list)
    promedio: float | None = None
    minimo: float | None = None
    maximo: float | None = None
    respuestas_texto: list[str] = field(default_factory=list)


@dataclass
class PuntajeRespuesta:
    respuesta_ronda_id: int
    fecha_respuesta: object
    usuario: str | None
    obtenido: int
    total_posible: int
    porcentaje: float


def _distribucion_si_no(respuestas_pregunta) -> list[OpcionResultado]:
    conteo: dict[str, int] = {}
    for respuesta in respuestas_pregunta:
        valor = respuesta.valor_texto or ""
        conteo[valor] = conteo.get(valor, 0) + 1
    total = sum(conteo.values())
    return [
        OpcionResultado(
            texto=ETIQUETAS_SI_NO.get(valor, valor or "Sin respuesta"),
            cantidad=cantidad,
            porcentaje=round(cantidad * 100 / total, 1) if total else 0.0,
        )
        for valor, cantidad in conteo.items()
    ]


def _distribucion_opciones(pregunta, respuestas_pregunta) -> list[OpcionResultado]:
    conteo_por_opcion_id: dict[int, int] = {}
    total_selecciones = 0
    for respuesta in respuestas_pregunta:
        for opcion in respuesta.opciones_seleccionadas.all():
            conteo_por_opcion_id[opcion.pk] = conteo_por_opcion_id.get(opcion.pk, 0) + 1
            total_selecciones += 1

    return [
        OpcionResultado(
            texto=opcion.texto,
            cantidad=conteo_por_opcion_id.get(opcion.pk, 0),
            porcentaje=(
                round(
                    conteo_por_opcion_id.get(opcion.pk, 0) * 100 / total_selecciones, 1
                )
                if total_selecciones
                else 0.0
            ),
        )
        for opcion in pregunta.opciones.order_by("orden")
    ]


def _resultado_numerico(resultado: ResultadoPregunta, respuestas_pregunta) -> None:
    valores = [
        r.valor_numero for r in respuestas_pregunta if r.valor_numero is not None
    ]
    if not valores:
        return
    resultado.promedio = float(sum(valores) / len(valores))
    resultado.minimo = float(min(valores))
    resultado.maximo = float(max(valores))


def _resultado_texto_libre(resultado: ResultadoPregunta, respuestas_pregunta) -> None:
    resultado.respuestas_texto = [
        respuesta.valor_texto
        or (respuesta.valor_fecha.isoformat() if respuesta.valor_fecha else "")
        for respuesta in respuestas_pregunta
    ]


def get_resultados_ronda(ronda: RondaEncuesta) -> list[ResultadoPregunta]:
    """Agrega las respuestas de una ronda por pregunta.

    Nunca expone qué usuario respondió qué (regla de negocio 1): solo cuenta
    y agrupa valores, incluso para encuestas identificadas — el detalle por
    usuario solo existe en la exportación (build_export_rows).
    """
    preguntas = ronda.encuesta.preguntas.order_by("orden").prefetch_related("opciones")
    resultados = []
    for pregunta in preguntas:
        respuestas_pregunta = list(
            RespuestaPregunta.objects.filter(
                respuesta_ronda__ronda=ronda, pregunta=pregunta
            ).prefetch_related("opciones_seleccionadas")
        )
        resultado = ResultadoPregunta(
            pregunta_id=pregunta.pk,
            texto=pregunta.texto,
            tipo=pregunta.tipo,
            total_respuestas=len(respuestas_pregunta),
        )
        if pregunta.tipo == TipoPregunta.SI_NO:
            resultado.opciones = _distribucion_si_no(respuestas_pregunta)
        elif pregunta.tipo in TIPOS_CON_DISTRIBUCION:
            resultado.opciones = _distribucion_opciones(pregunta, respuestas_pregunta)
        elif pregunta.tipo in TIPOS_NUMERICOS:
            _resultado_numerico(resultado, respuestas_pregunta)
        else:
            _resultado_texto_libre(resultado, respuestas_pregunta)
        resultados.append(resultado)
    return resultados


def encuesta_pondera(encuesta) -> bool:
    return encuesta.preguntas.filter(pondera=True).exists()


def _puntaje_maximo_pregunta(pregunta) -> int:
    """Puntos máximos que aporta una pregunta al total posible.

    El total posible de una encuesta es fijo (decisión de negocio explícita):
    suma los puntos de TODAS las preguntas que ponderan, aunque a una persona
    en particular no le hayan aparecido algunas por la lógica condicional.
    """
    if not pregunta.pondera:
        return 0
    if pregunta.tipo == TipoPregunta.SI_NO:
        return max(pregunta.puntaje_si or 0, pregunta.puntaje_no or 0)
    if pregunta.tipo == TipoPregunta.OPCION_UNICA:
        return max((opcion.puntaje for opcion in pregunta.opciones.all()), default=0)
    if pregunta.tipo == TipoPregunta.OPCION_MULTIPLE:
        return sum(opcion.puntaje for opcion in pregunta.opciones.all())
    if pregunta.tipo == TipoPregunta.ESCALA:
        return 10
    return 0


def puntaje_total_posible(encuesta) -> int:
    preguntas = encuesta.preguntas.prefetch_related("opciones")
    return sum(_puntaje_maximo_pregunta(pregunta) for pregunta in preguntas)


def _puntaje_obtenido_pregunta(pregunta, respuesta_pregunta) -> int:
    if not pregunta.pondera or respuesta_pregunta is None:
        return 0
    if pregunta.tipo == TipoPregunta.SI_NO:
        if respuesta_pregunta.valor_texto == "si":
            return pregunta.puntaje_si or 0
        if respuesta_pregunta.valor_texto == "no":
            return pregunta.puntaje_no or 0
        return 0
    if pregunta.tipo in (TipoPregunta.OPCION_UNICA, TipoPregunta.OPCION_MULTIPLE):
        return sum(
            opcion.puntaje for opcion in respuesta_pregunta.opciones_seleccionadas.all()
        )
    if pregunta.tipo == TipoPregunta.ESCALA:
        return int(respuesta_pregunta.valor_numero or 0)
    return 0


def get_puntajes_ronda(ronda: RondaEncuesta) -> list[PuntajeRespuesta]:
    """Puntaje obtenido por cada respuesta de la ronda, del más alto al más
    bajo. Devuelve lista vacía si la encuesta no tiene ninguna pregunta que
    pondere (no tiene sentido mostrar una sección de puntajes en 0).

    El nombre de usuario nunca se expone en encuestas anónimas (regla de
    negocio 1), igual que en get_resultados_ronda / build_export_rows.
    """
    encuesta = ronda.encuesta
    if not encuesta_pondera(encuesta):
        return []

    total_posible = puntaje_total_posible(encuesta)
    preguntas = list(encuesta.preguntas.prefetch_related("opciones"))
    respuestas_ronda = ronda.respuestas.select_related("usuario").prefetch_related(
        "respuestas_pregunta__opciones_seleccionadas"
    )

    resultado = []
    for respuesta_ronda in respuestas_ronda:
        detalle_por_pregunta = {
            detalle.pregunta_id: detalle
            for detalle in respuesta_ronda.respuestas_pregunta.all()
        }
        obtenido = sum(
            _puntaje_obtenido_pregunta(pregunta, detalle_por_pregunta.get(pregunta.pk))
            for pregunta in preguntas
        )
        usuario = respuesta_ronda.usuario
        resultado.append(
            PuntajeRespuesta(
                respuesta_ronda_id=respuesta_ronda.pk,
                fecha_respuesta=respuesta_ronda.fecha_respuesta,
                usuario=(
                    None
                    if encuesta.es_anonima
                    else (usuario.get_full_name() or usuario.username)
                ),
                obtenido=obtenido,
                total_posible=total_posible,
                porcentaje=(
                    round(obtenido * 100 / total_posible, 1) if total_posible else 0.0
                ),
            )
        )
    resultado.sort(key=lambda puntaje: puntaje.obtenido, reverse=True)
    return resultado


def _formatear_numero(valor) -> str:
    # valor_numero es DecimalField(decimal_places=2): un "7" cargado como
    # escala se guarda como Decimal("7.00"). Se recorta a la mínima
    # expresión (7, o 4.5) en vez de mostrar siempre dos decimales.
    texto = f"{valor:.2f}".rstrip("0").rstrip(".")
    return texto or "0"


def _formatear_valor_respuesta(pregunta, respuesta_pregunta) -> str:
    if respuesta_pregunta is None:
        return ""
    if pregunta.tipo in (TipoPregunta.OPCION_UNICA, TipoPregunta.OPCION_MULTIPLE):
        return ", ".join(
            opcion.texto for opcion in respuesta_pregunta.opciones_seleccionadas.all()
        )
    if pregunta.tipo in TIPOS_NUMERICOS:
        valor = respuesta_pregunta.valor_numero
        return _formatear_numero(valor) if valor is not None else ""
    if pregunta.tipo == TipoPregunta.FECHA:
        valor = respuesta_pregunta.valor_fecha
        return valor.isoformat() if valor else ""
    if pregunta.tipo == TipoPregunta.SI_NO:
        return ETIQUETAS_SI_NO.get(
            respuesta_pregunta.valor_texto, respuesta_pregunta.valor_texto or ""
        )
    return respuesta_pregunta.valor_texto or ""


def build_export_headers(encuesta, preguntas) -> list[str]:
    headers = ["Ronda", "Versión", "Fecha de respuesta"]
    if not encuesta.es_anonima:
        headers.append("Usuario")
    if encuesta_pondera(encuesta):
        headers.extend(["Puntaje obtenido", "Puntaje total"])
    headers.extend(pregunta.texto for pregunta in preguntas)
    return headers


def build_export_rows(ronda: RondaEncuesta) -> tuple[list, list[list[str]]]:
    """Filas para exportar resultados: una por RespuestaRonda.

    Si la encuesta es anónima, la columna Usuario directamente no se genera
    (regla de negocio 1: el contenido nunca se vincula a la identidad en
    ningún reporte, incluida la exportación).
    """
    preguntas = list(
        ronda.encuesta.preguntas.order_by("orden").prefetch_related("opciones")
    )
    pondera = encuesta_pondera(ronda.encuesta)
    total_posible = puntaje_total_posible(ronda.encuesta) if pondera else 0
    filas = []
    respuestas_ronda = ronda.respuestas.select_related("usuario").prefetch_related(
        "respuestas_pregunta__opciones_seleccionadas"
    )
    for respuesta_ronda in respuestas_ronda:
        detalle_por_pregunta = {
            detalle.pregunta_id: detalle
            for detalle in respuesta_ronda.respuestas_pregunta.all()
        }
        fecha_local = timezone.localtime(respuesta_ronda.fecha_respuesta)
        fila = [
            ronda.numero_ronda,
            ronda.encuesta.version,
            fecha_local.strftime("%d/%m/%Y %H:%M"),
        ]
        if not ronda.encuesta.es_anonima:
            usuario = respuesta_ronda.usuario
            fila.append(usuario.get_full_name() or usuario.username)
        if pondera:
            obtenido = sum(
                _puntaje_obtenido_pregunta(
                    pregunta, detalle_por_pregunta.get(pregunta.pk)
                )
                for pregunta in preguntas
            )
            fila.extend([obtenido, total_posible])
        fila.extend(
            _formatear_valor_respuesta(pregunta, detalle_por_pregunta.get(pregunta.pk))
            for pregunta in preguntas
        )
        filas.append(fila)
    return preguntas, filas


def build_resultados_csv_rows(
    ronda: RondaEncuesta,
) -> tuple[list[str], list[list[str]]]:
    preguntas, filas = build_export_rows(ronda)
    return build_export_headers(ronda.encuesta, preguntas), filas


def build_resultados_excel(ronda: RondaEncuesta) -> bytes:
    preguntas, filas = build_export_rows(ronda)
    headers = build_export_headers(ronda.encuesta, preguntas)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Resultados"
    worksheet.freeze_panes = "A2"
    worksheet.append(headers)
    for cell in worksheet[1]:
        cell.font = Font(bold=True)
    for fila in filas:
        worksheet.append(fila)

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def build_resultados_filename(encuesta, ronda: RondaEncuesta, extension: str) -> str:
    slug = slugify(encuesta.titulo) or f"encuesta-{encuesta.pk}"
    return f"resultados_{slug}_ronda{ronda.numero_ronda}.{extension}"
