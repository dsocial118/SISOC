"""Buscador de trayectoria formativa INET por ciudadano (DNI o CUIT/CUIL).

Reemplaza la consulta SQL manual que se corría contra la base para responder
"¿en qué cursos se anotó esta persona?": resuelve ambas rutas de inscripción
(comision_curso / comision) reusando `base_inscripciones_queryset_for_user`,
respeta el alcance territorial del usuario y excluye bajas lógicas (managers
`objects` de SoftDeleteModelMixin).
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from io import BytesIO

from django.db.models import Count, F, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce, Replace
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font

from VAT.models import Inscripcion, InstitucionIdentificadorHist
from VAT.services.vat_inscripciones_base import base_inscripciones_queryset_for_user
from ciudadanos.models import Ciudadano

DOCUMENTO_LENGTHS = (7, 8)
CUIL_LENGTH = 11

ESTADO_LABELS = dict(Inscripcion.ESTADO_INSCRIPCION_CHOICES)
RESULTADO_LABELS = dict(Inscripcion.RESULTADO_FINAL_CHOICES)
ORIGEN_LABELS = dict(Inscripcion.ORIGEN_CANAL_CHOICES)
SIN_CALIFICAR = "sin_calificar"

TRAYECTORIA_HEADERS = [
    "Fecha inscripción",
    "Curso",
    "Comisión",
    "Período",
    "Centro",
    "CUE",
    "Provincia",
    "Localidad",
    "Dirección",
    "Estado inscripción",
    "Resultado final",
    "Asistencia",
    "Estado curso",
    "Estado comisión",
    "Origen",
]


def normalizar_identificador(q: str) -> str:
    """Deja solo dígitos: ignora puntos, guiones y espacios."""
    return re.sub(r"\D", "", q or "")


def buscar_ciudadanos(q: str):
    """Busca por documento (7-8 dígitos) o por CUIT/CUIL (11 dígitos).

    Con 11 dígitos se busca por el documento contenido en el CUIL (posiciones
    3 a 10) y por `cuil_cuit` normalizado, para no depender de que el campo
    esté guardado con o sin guiones.
    """
    digitos = normalizar_identificador(q)

    if len(digitos) in DOCUMENTO_LENGTHS:
        return Ciudadano.objects.filter(documento=int(digitos)).order_by(
            "apellido", "nombre"
        )

    if len(digitos) == CUIL_LENGTH:
        documento_candidato = int(digitos[2:10])
        cuil_normalizado = Replace(
            Replace(F("cuil_cuit"), Value("-"), Value("")),
            Value("."),
            Value(""),
        )
        return (
            Ciudadano.objects.annotate(cuil_cuit_normalizado=cuil_normalizado)
            .filter(Q(documento=documento_candidato) | Q(cuil_cuit_normalizado=digitos))
            .order_by("apellido", "nombre")
            .distinct()
        )

    return Ciudadano.objects.none()


def build_trayectoria_queryset(user, ciudadano):
    """Trayectoria INET de un ciudadano, respetando el alcance del usuario."""
    cue_subquery = Subquery(
        InstitucionIdentificadorHist.objects.filter(
            centro_id=OuterRef("centro_id_ref"),
            tipo_identificador="cue",
            es_actual=True,
        )
        .order_by("-vigencia_desde")
        .values("valor_identificador")[:1]
    )

    return (
        base_inscripciones_queryset_for_user(user)
        .filter(ciudadano=ciudadano)
        .select_related(
            "comision_curso__ubicacion__localidad",
            "comision__ubicacion__localidad",
            "comision_curso__curso__centro__localidad",
            "comision__oferta__centro__localidad",
        )
        .annotate(
            cue_ref=cue_subquery,
            direccion_ref=Coalesce(
                F("comision_curso__ubicacion__domicilio"),
                F("comision__ubicacion__domicilio"),
                F("comision_curso__curso__centro__domicilio_actividad"),
                F("comision__oferta__centro__domicilio_actividad"),
            ),
            localidad_ref=Coalesce(
                F("comision_curso__ubicacion__localidad__nombre"),
                F("comision__ubicacion__localidad__nombre"),
                F("comision_curso__curso__centro__localidad__nombre"),
                F("comision__oferta__centro__localidad__nombre"),
                Value("Sin localidad"),
            ),
            periodo_inicio_ref=Coalesce(
                F("comision_curso__fecha_inicio"),
                F("comision__fecha_inicio"),
            ),
            periodo_fin_ref=Coalesce(
                F("comision_curso__fecha_fin"),
                F("comision__fecha_fin"),
            ),
            presentes_ref=Count(
                "asistencias__id",
                filter=Q(asistencias__presente=True),
                distinct=True,
            ),
            ausentes_ref=Count(
                "asistencias__id",
                filter=Q(asistencias__presente=False),
                distinct=True,
            ),
        )
        .order_by("-fecha_inscripcion")
    )


def build_resumen(inscripciones) -> dict:
    """Contadores de estado/resultado/asistencia sobre una lista ya materializada."""
    inscripciones = list(inscripciones)
    total = len(inscripciones)
    por_estado = Counter(inscripcion.estado for inscripcion in inscripciones)
    por_resultado = Counter(
        inscripcion.resultado_final or SIN_CALIFICAR for inscripcion in inscripciones
    )
    presentes = sum(inscripcion.presentes_ref for inscripcion in inscripciones)
    ausentes = sum(inscripcion.ausentes_ref for inscripcion in inscripciones)
    total_asistencia = presentes + ausentes
    porcentaje = round(presentes * 100 / total_asistencia, 2) if total_asistencia else 0

    return {
        "total": total,
        "en_curso": por_estado.get("inscripta", 0)
        + por_estado.get("validada_presencial", 0),
        "pre_inscriptas": por_estado.get("pre_inscripta", 0),
        "en_espera": por_estado.get("en_espera", 0),
        "completadas": por_estado.get("completada", 0),
        "abandonadas": por_estado.get("abandonada", 0),
        "rechazadas": por_estado.get("rechazada", 0),
        "aprobadas": por_resultado.get(Inscripcion.RESULTADO_APROBADO, 0),
        "desaprobadas": por_resultado.get(Inscripcion.RESULTADO_DESAPROBADO, 0),
        "sin_calificar": por_resultado.get(SIN_CALIFICAR, 0),
        "presentes": presentes,
        "ausentes": ausentes,
        "porcentaje_asistencia": porcentaje,
    }


def asistencia_texto(inscripcion) -> str:
    total = inscripcion.presentes_ref + inscripcion.ausentes_ref
    if not total:
        return "Sin registros"
    porcentaje = round(inscripcion.presentes_ref * 100 / total)
    return f"{porcentaje}% ({inscripcion.presentes_ref}/{total})"


def _periodo_texto(inscripcion) -> str:
    if inscripcion.periodo_inicio_ref and inscripcion.periodo_fin_ref:
        return (
            f"{inscripcion.periodo_inicio_ref:%d/%m/%Y} — "
            f"{inscripcion.periodo_fin_ref:%d/%m/%Y}"
        )
    return ""


def _trayectoria_row_cells(inscripcion) -> list:
    return [
        (
            inscripcion.fecha_inscripcion.strftime("%d/%m/%Y %H:%M")
            if inscripcion.fecha_inscripcion
            else ""
        ),
        inscripcion.unidad_formativa_nombre or "",
        inscripcion.comision_codigo_ref or "",
        _periodo_texto(inscripcion),
        inscripcion.centro_nombre_ref or "",
        inscripcion.cue_ref or "",
        inscripcion.provincia_nombre_ref or "",
        inscripcion.localidad_ref or "",
        inscripcion.direccion_ref or "",
        ESTADO_LABELS.get(inscripcion.estado, inscripcion.estado),
        RESULTADO_LABELS.get(inscripcion.resultado_final, "Sin calificar"),
        asistencia_texto(inscripcion),
        inscripcion.estado_curso_ref or "",
        inscripcion.estado_comision_ref or "",
        ORIGEN_LABELS.get(inscripcion.origen_canal, inscripcion.origen_canal),
    ]


def _export_filename(ciudadano, extension: str) -> str:
    identificador = ciudadano.documento or ciudadano.pk
    return f"vat_trayectoria_ciudadano_{identificador}.{extension}"


def export_trayectoria_to_csv(user, ciudadano) -> HttpResponse:
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = (
        f"attachment; filename={_export_filename(ciudadano, 'csv')}"
    )
    response.write("﻿")  # BOM: Excel respeta los acentos en UTF-8
    writer = csv.writer(response)
    writer.writerow(TRAYECTORIA_HEADERS)
    for inscripcion in build_trayectoria_queryset(user, ciudadano):
        writer.writerow(_trayectoria_row_cells(inscripcion))
    return response


def export_trayectoria_to_excel(user, ciudadano) -> HttpResponse:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Trayectoria INET"
    worksheet.freeze_panes = "A2"
    worksheet.append(TRAYECTORIA_HEADERS)
    for cell in worksheet[1]:
        cell.font = Font(bold=True)

    for inscripcion in build_trayectoria_queryset(user, ciudadano):
        worksheet.append(_trayectoria_row_cells(inscripcion))

    output = BytesIO()
    workbook.save(output)
    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        f"attachment; filename={_export_filename(ciudadano, 'xlsx')}"
    )
    return response
