from __future__ import annotations

import csv
from io import BytesIO
from dataclasses import dataclass
from datetime import datetime

from django.db.models import Count, F, Q, Value
from django.db.models.functions import Coalesce, TruncMonth
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font

from VAT.models import Centro, Comision, ComisionCurso, Curso, Inscripcion
from VAT.services.access_scope import filter_centros_queryset_for_user


DATE_INPUT_FORMAT = "%Y-%m-%d"
GROUP_BY_ALLOWED = ("centro", "provincia", "curso", "comision", "mes")
NIVEL_ALLOWED = ("centro", "provincia", "inet")
BOOLEAN_TEXT = {"true": True, "false": False}


@dataclass(frozen=True)
class ReporteFiltros:
    nivel: str = "inet"
    fecha_desde: str = ""
    fecha_hasta: str = ""
    provincia_id: str = ""
    municipio_id: str = ""
    centro_id: str = ""
    comision_id: str = ""
    curso_id: str = ""
    programa_id: str = ""
    titulo_id: str = ""
    modalidad_id: str = ""
    estado: str = ""
    usa_voucher: str = ""
    estado_curso: str = ""
    estado_comision: str = ""
    group_by: str = "centro"


def _parse_date(value: str):
    if not value:
        return None
    try:
        return datetime.strptime(value, DATE_INPUT_FORMAT).date()
    except ValueError:
        return None


def _normalize_id(value: str) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _unique_choice_tuples(*choices_lists):
    merged = []
    seen = set()
    for choices in choices_lists:
        for value, label in choices:
            if value in seen:
                continue
            seen.add(value)
            merged.append((value, label))
    return merged


def _base_queryset_for_user(user):
    centros_ids = filter_centros_queryset_for_user(Centro.objects.all(), user).values(
        "id"
    )
    return (
        Inscripcion.objects.select_related(
            "comision",
            "comision__oferta",
            "comision__oferta__centro",
            "comision__oferta__centro__provincia",
            "comision__oferta__centro__municipio",
            "comision__oferta__programa",
            "comision__oferta__plan_curricular",
            "comision__oferta__plan_curricular__modalidad_cursada",
            "comision_curso",
            "comision_curso__curso",
            "comision_curso__curso__centro",
            "comision_curso__curso__centro__provincia",
            "comision_curso__curso__centro__municipio",
            "comision_curso__curso__programa",
            "comision_curso__curso__modalidad",
            "comision_curso__curso__plan_estudio",
        )
        .filter(
            Q(comision_curso__curso__centro_id__in=centros_ids)
            | Q(comision__oferta__centro_id__in=centros_ids)
        )
        .annotate(
            centro_id_ref=Coalesce(
                F("comision_curso__curso__centro_id"),
                F("comision__oferta__centro_id"),
            ),
            centro_nombre_ref=Coalesce(
                F("comision_curso__curso__centro__nombre"),
                F("comision__oferta__centro__nombre"),
                Value("Sin centro"),
            ),
            provincia_id_ref=Coalesce(
                F("comision_curso__curso__centro__provincia_id"),
                F("comision__oferta__centro__provincia_id"),
            ),
            provincia_nombre_ref=Coalesce(
                F("comision_curso__curso__centro__provincia__nombre"),
                F("comision__oferta__centro__provincia__nombre"),
                Value("Sin provincia"),
            ),
            municipio_id_ref=Coalesce(
                F("comision_curso__curso__centro__municipio_id"),
                F("comision__oferta__centro__municipio_id"),
            ),
            municipio_nombre_ref=Coalesce(
                F("comision_curso__curso__centro__municipio__nombre"),
                F("comision__oferta__centro__municipio__nombre"),
                Value("Sin municipio"),
            ),
            unidad_formativa_id=Coalesce(
                F("comision_curso__curso_id"),
                F("comision__oferta_id"),
            ),
            unidad_formativa_nombre=Coalesce(
                F("comision_curso__curso__nombre"),
                F("comision__oferta__nombre_local"),
                F("comision__oferta__plan_curricular__nombre"),
                Value("Sin curso/oferta"),
            ),
            comision_id_ref=Coalesce(F("comision_curso_id"), F("comision_id")),
            comision_codigo_ref=Coalesce(
                F("comision_curso__codigo_comision"),
                F("comision__codigo_comision"),
                Value("Sin comisión"),
            ),
            programa_id_ref=Coalesce(
                Value(None),
                F("comision__oferta__programa_id"),
            ),
            programa_nombre_ref=Coalesce(
                F("comision__oferta__programa__nombre"),
                Value("Sin programa"),
            ),
            titulo_id_ref=Coalesce(
                F("comision_curso__curso__plan_estudio__titulos__id"),
                F("comision__oferta__plan_curricular__titulos__id"),
            ),
            titulo_nombre_ref=Coalesce(
                F("comision_curso__curso__plan_estudio__titulos__nombre"),
                F("comision__oferta__plan_curricular__titulos__nombre"),
                Value("Sin título"),
            ),
            modalidad_id_ref=Coalesce(
                F("comision_curso__curso__modalidad_id"),
                F("comision__oferta__plan_curricular__modalidad_cursada_id"),
            ),
            modalidad_nombre_ref=Coalesce(
                F("comision_curso__curso__modalidad__nombre"),
                F("comision__oferta__plan_curricular__modalidad_cursada__nombre"),
                Value("Sin modalidad"),
            ),
            usa_voucher_ref=Coalesce(
                F("comision_curso__curso__usa_voucher"),
                F("comision__oferta__usa_voucher"),
            ),
            estado_curso_ref=F("comision_curso__curso__estado"),
            estado_comision_ref=Coalesce(
                F("comision_curso__estado"),
                F("comision__estado"),
            ),
        )
    )


def _apply_filters(queryset, filtros: ReporteFiltros):
    fecha_desde = _parse_date(filtros.fecha_desde)
    fecha_hasta = _parse_date(filtros.fecha_hasta)

    if fecha_desde:
        queryset = queryset.filter(fecha_inscripcion__date__gte=fecha_desde)
    if fecha_hasta:
        queryset = queryset.filter(fecha_inscripcion__date__lte=fecha_hasta)

    provincia_id = _normalize_id(filtros.provincia_id)
    municipio_id = _normalize_id(filtros.municipio_id)
    centro_id = _normalize_id(filtros.centro_id)
    comision_id = _normalize_id(filtros.comision_id)
    curso_id = _normalize_id(filtros.curso_id)
    programa_id = _normalize_id(filtros.programa_id)
    titulo_id = _normalize_id(filtros.titulo_id)
    modalidad_id = _normalize_id(filtros.modalidad_id)

    if filtros.nivel == "centro" and centro_id:
        queryset = queryset.filter(centro_id_ref=centro_id)
    elif filtros.nivel == "provincia" and provincia_id:
        queryset = queryset.filter(provincia_id_ref=provincia_id)

    if provincia_id:
        queryset = queryset.filter(provincia_id_ref=provincia_id)
    if municipio_id:
        queryset = queryset.filter(municipio_id_ref=municipio_id)
    if centro_id:
        queryset = queryset.filter(centro_id_ref=centro_id)
    if comision_id:
        queryset = queryset.filter(comision_id_ref=comision_id)
    if curso_id:
        queryset = queryset.filter(comision_curso__curso_id=curso_id)
    if programa_id:
        queryset = queryset.filter(programa_id_ref=programa_id)
    if titulo_id:
        queryset = queryset.filter(titulo_id_ref=titulo_id)
    if modalidad_id:
        queryset = queryset.filter(modalidad_id_ref=modalidad_id)
    if filtros.estado:
        queryset = queryset.filter(estado=filtros.estado)
    if filtros.usa_voucher.lower() in BOOLEAN_TEXT:
        queryset = queryset.filter(
            usa_voucher_ref=BOOLEAN_TEXT[filtros.usa_voucher.lower()]
        )
    if filtros.estado_curso:
        queryset = queryset.filter(estado_curso_ref=filtros.estado_curso)
    if filtros.estado_comision:
        queryset = queryset.filter(estado_comision_ref=filtros.estado_comision)

    return queryset.distinct()


def _row_annotations():
    return {
        "inscripciones_total": Count("id", distinct=True),
        "preinscriptos": Count(
            "id",
            filter=Q(estado="pre_inscripta"),
            distinct=True,
        ),
        "en_espera": Count("id", filter=Q(estado="en_espera"), distinct=True),
        "inscriptos": Count("id", filter=Q(estado="inscripta"), distinct=True),
        "validados_presencial": Count(
            "id",
            filter=Q(estado="validada_presencial"),
            distinct=True,
        ),
        "completados": Count("id", filter=Q(estado="completada"), distinct=True),
        "abandonados": Count("id", filter=Q(estado="abandonada"), distinct=True),
        "registros_asistencia": Count("asistencias__id"),
        "presentes": Count("asistencias__id", filter=Q(asistencias__presente=True)),
        "ausentes": Count("asistencias__id", filter=Q(asistencias__presente=False)),
        "sesiones_programadas": Count(
            "comision_curso__sesiones__id",
            filter=Q(comision_curso__sesiones__estado="programada"),
            distinct=True,
        )
        + Count(
            "comision__sesiones__id",
            filter=Q(comision__sesiones__estado="programada"),
            distinct=True,
        ),
        "sesiones_realizadas": Count(
            "comision_curso__sesiones__id",
            filter=Q(comision_curso__sesiones__estado="realizada"),
            distinct=True,
        )
        + Count(
            "comision__sesiones__id",
            filter=Q(comision__sesiones__estado="realizada"),
            distinct=True,
        ),
    }


def _group_fields(group_by: str):
    if group_by == "provincia":
        return ["provincia_id_ref", "provincia_nombre_ref"]
    if group_by == "curso":
        return ["unidad_formativa_id", "unidad_formativa_nombre"]
    if group_by == "comision":
        return ["comision_id_ref", "comision_codigo_ref", "centro_nombre_ref"]
    if group_by == "mes":
        return ["mes_ref"]
    return ["centro_id_ref", "centro_nombre_ref", "provincia_nombre_ref"]


def _serialize_rows(rows, group_by: str):
    serialized = []
    for row in rows:
        presentes = row.get("presentes") or 0
        ausentes = row.get("ausentes") or 0
        total_asistencia = presentes + ausentes
        porcentaje = (presentes * 100 / total_asistencia) if total_asistencia else 0

        if group_by == "provincia":
            grupo = row.get("provincia_nombre_ref")
        elif group_by == "curso":
            grupo = row.get("unidad_formativa_nombre")
        elif group_by == "comision":
            grupo = row.get("comision_codigo_ref")
        elif group_by == "mes":
            mes_ref = row.get("mes_ref")
            grupo = mes_ref.strftime("%Y-%m") if mes_ref else "Sin fecha"
        else:
            grupo = row.get("centro_nombre_ref")

        item = {
            "grupo": grupo,
            "porcentaje_asistencia": round(porcentaje, 2),
        }
        item.update(row)
        serialized.append(item)

    return serialized


def build_reporte_inscripciones_asistencia(user, filtros: ReporteFiltros):
    group_by = filtros.group_by if filtros.group_by in GROUP_BY_ALLOWED else "centro"
    nivel = filtros.nivel if filtros.nivel in NIVEL_ALLOWED else "inet"

    queryset = _apply_filters(_base_queryset_for_user(user), filtros)
    if group_by == "mes":
        queryset = queryset.annotate(mes_ref=TruncMonth("fecha_inscripcion"))

    grouping_fields = _group_fields(group_by)
    rows = list(
        queryset.values(*grouping_fields)
        .annotate(**_row_annotations())
        .order_by("-inscripciones_total", *grouping_fields)
    )

    resumen = queryset.aggregate(**_row_annotations())
    resumen_presentes = resumen.get("presentes") or 0
    resumen_ausentes = resumen.get("ausentes") or 0
    resumen_total_asistencia = resumen_presentes + resumen_ausentes
    resumen["porcentaje_asistencia"] = round(
        (
            (resumen_presentes * 100 / resumen_total_asistencia)
            if resumen_total_asistencia
            else 0
        ),
        2,
    )

    return {
        "nivel": nivel,
        "group_by": group_by,
        "rows": _serialize_rows(rows, group_by),
        "resumen": resumen,
    }


def build_detalle_personas_inscriptas(
    user,
    filtros: ReporteFiltros,
    max_rows: int = 250,
):
    queryset = _apply_filters(_base_queryset_for_user(user), filtros)
    return list(
        queryset.values(
            "id",
            "ciudadano__documento",
            "ciudadano__apellido",
            "ciudadano__nombre",
            "estado",
            "fecha_inscripcion",
            "centro_nombre_ref",
            "comision_codigo_ref",
            "unidad_formativa_nombre",
        ).order_by("-fecha_inscripcion")[:max_rows]
    )


def get_filter_options(user):
    centros_qs = filter_centros_queryset_for_user(
        Centro.objects.select_related("provincia", "municipio"), user
    )
    provincias = (
        centros_qs.values("provincia_id", "provincia__nombre")
        .distinct()
        .order_by("provincia__nombre")
    )
    municipios = (
        centros_qs.values("municipio_id", "municipio__nombre")
        .distinct()
        .order_by("municipio__nombre")
    )
    centros = centros_qs.values("id", "nombre").order_by("nombre")

    inscripciones_scope = _base_queryset_for_user(user)
    programas = (
        inscripciones_scope.values("programa_id_ref", "programa_nombre_ref")
        .exclude(programa_id_ref__isnull=True)
        .distinct()
        .order_by("programa_nombre_ref")
    )
    titulos = (
        inscripciones_scope.values("titulo_id_ref", "titulo_nombre_ref")
        .exclude(titulo_id_ref__isnull=True)
        .distinct()
        .order_by("titulo_nombre_ref")
    )
    modalidades = (
        inscripciones_scope.values("modalidad_id_ref", "modalidad_nombre_ref")
        .exclude(modalidad_id_ref__isnull=True)
        .distinct()
        .order_by("modalidad_nombre_ref")
    )
    cursos = (
        inscripciones_scope.values("unidad_formativa_id", "unidad_formativa_nombre")
        .exclude(unidad_formativa_id__isnull=True)
        .distinct()
        .order_by("unidad_formativa_nombre")
    )
    comisiones = (
        inscripciones_scope.values(
            "comision_id_ref",
            "comision_codigo_ref",
            "centro_nombre_ref",
        )
        .exclude(comision_id_ref__isnull=True)
        .distinct()
        .order_by("comision_codigo_ref")
    )

    return {
        "provincias": list(provincias),
        "municipios": list(municipios),
        "centros": list(centros),
        "programas": list(programas),
        "titulos": list(titulos),
        "modalidades": list(modalidades),
        "cursos": list(cursos),
        "comisiones": list(comisiones),
        "curso_estado_choices": list(Curso.ESTADO_CURSO_CHOICES),
        "comision_estado_choices": _unique_choice_tuples(
            ComisionCurso.ESTADO_COMISION_CURSO_CHOICES,
            Comision.ESTADO_COMISION_CHOICES,
        ),
    }


DETALLE_HEADERS = [
    "Documento",
    "Apellido",
    "Nombre",
    "Estado",
    "Fecha inscripción",
    "Centro",
    "Provincia",
    "Curso/Oferta",
    "Comisión",
]


def _detalle_export_queryset(user, filtros: ReporteFiltros):
    """Detalle nominal completo (sin tope de filas) para exportar."""
    queryset = _apply_filters(_base_queryset_for_user(user), filtros)
    return queryset.values(
        "id",
        "ciudadano__documento",
        "ciudadano__apellido",
        "ciudadano__nombre",
        "estado",
        "fecha_inscripcion",
        "centro_nombre_ref",
        "provincia_nombre_ref",
        "unidad_formativa_nombre",
        "comision_codigo_ref",
    ).order_by("centro_nombre_ref", "ciudadano__apellido", "ciudadano__nombre")


def _detalle_row_cells(row, estado_labels):
    fecha = row.get("fecha_inscripcion")
    estado = row.get("estado") or ""
    return [
        row.get("ciudadano__documento") or "",
        row.get("ciudadano__apellido") or "",
        row.get("ciudadano__nombre") or "",
        estado_labels.get(estado, estado),
        fecha.strftime("%Y-%m-%d %H:%M") if fecha else "",
        row.get("centro_nombre_ref") or "",
        row.get("provincia_nombre_ref") or "",
        row.get("unidad_formativa_nombre") or "",
        row.get("comision_codigo_ref") or "",
    ]


def export_detalle_to_csv(user, filtros: ReporteFiltros) -> HttpResponse:
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = (
        "attachment; filename=vat_reporte_detalle_inscripciones.csv"
    )
    response.write("﻿")  # BOM: Excel respeta los acentos en UTF-8
    estado_labels = dict(Inscripcion.ESTADO_INSCRIPCION_CHOICES)
    writer = csv.writer(response)
    writer.writerow(DETALLE_HEADERS)
    for row in _detalle_export_queryset(user, filtros).iterator():
        writer.writerow(_detalle_row_cells(row, estado_labels))
    return response


def export_detalle_to_excel(user, filtros: ReporteFiltros) -> HttpResponse:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Detalle inscripciones"
    worksheet.freeze_panes = "A2"
    worksheet.append(DETALLE_HEADERS)
    for cell in worksheet[1]:
        cell.font = Font(bold=True)

    estado_labels = dict(Inscripcion.ESTADO_INSCRIPCION_CHOICES)
    for row in _detalle_export_queryset(user, filtros).iterator():
        worksheet.append(_detalle_row_cells(row, estado_labels))

    output = BytesIO()
    workbook.save(output)
    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        "attachment; filename=vat_reporte_detalle_inscripciones.xlsx"
    )
    return response


def export_rows_to_csv(rows, group_by: str) -> HttpResponse:
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        "attachment; filename=vat_reporte_inscripciones_asistencias.csv"
    )

    writer = csv.writer(response)
    writer.writerow(
        [
            "Agrupador",
            "Inscriptos totales",
            "Preinscriptos",
            "En espera",
            "Inscriptos",
            "Validados presencial",
            "Completados",
            "Abandonados",
            "Registros asistencia",
            "Presentes",
            "Ausentes",
            "% Asistencia",
            "Sesiones programadas",
            "Sesiones realizadas",
        ]
    )

    for row in rows:
        writer.writerow(
            [
                row.get("grupo") or "",
                row.get("inscripciones_total") or 0,
                row.get("preinscriptos") or 0,
                row.get("en_espera") or 0,
                row.get("inscriptos") or 0,
                row.get("validados_presencial") or 0,
                row.get("completados") or 0,
                row.get("abandonados") or 0,
                row.get("registros_asistencia") or 0,
                row.get("presentes") or 0,
                row.get("ausentes") or 0,
                row.get("porcentaje_asistencia") or 0,
                row.get("sesiones_programadas") or 0,
                row.get("sesiones_realizadas") or 0,
            ]
        )

    return response


def export_rows_to_excel(rows) -> HttpResponse:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Reporte VAT"
    worksheet.freeze_panes = "A2"

    headers = [
        "Agrupador",
        "Inscriptos totales",
        "Preinscriptos",
        "En espera",
        "Inscriptos",
        "Validados presencial",
        "Completados",
        "Abandonados",
        "Registros asistencia",
        "Presentes",
        "Ausentes",
        "% Asistencia",
        "Sesiones programadas",
        "Sesiones realizadas",
    ]
    worksheet.append(headers)
    for cell in worksheet[1]:
        cell.font = Font(bold=True)

    for row in rows:
        worksheet.append(
            [
                row.get("grupo") or "",
                row.get("inscripciones_total") or 0,
                row.get("preinscriptos") or 0,
                row.get("en_espera") or 0,
                row.get("inscriptos") or 0,
                row.get("validados_presencial") or 0,
                row.get("completados") or 0,
                row.get("abandonados") or 0,
                row.get("registros_asistencia") or 0,
                row.get("presentes") or 0,
                row.get("ausentes") or 0,
                row.get("porcentaje_asistencia") or 0,
                row.get("sesiones_programadas") or 0,
                row.get("sesiones_realizadas") or 0,
            ]
        )

    output = BytesIO()
    workbook.save(output)

    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        "attachment; filename=vat_reporte_inscripciones_asistencias.xlsx"
    )
    return response
