import json
from io import BytesIO

from django.utils import timezone
from django.utils.text import slugify
from openpyxl import Workbook
from openpyxl.styles import Font


NOMINA_HEADERS = [
    "Apellido",
    "Nombre",
    "DNI / CUIL",
    "Fecha de Nacimiento",
    "Género",
    "Comisión",
    "Curso",
    "Centro de Formación",
    "Estado de Inscripción",
    "Fecha de Inscripción",
    "Canal de Inscripción",
    "Email",
    "Teléfono",
]


def _format_date(value):
    if not value:
        return ""
    return value.strftime("%d/%m/%Y")


def _format_datetime(value):
    if not value:
        return ""
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    return value.strftime("%d/%m/%Y %H:%M")


def _parse_observaciones_json(inscripcion):
    observaciones = getattr(inscripcion, "observaciones", "")
    if not isinstance(observaciones, str):
        return {}

    observaciones = observaciones.strip()
    if not observaciones:
        return {}

    try:
        parsed = json.loads(observaciones)
    except (TypeError, ValueError):
        return {}

    return parsed if isinstance(parsed, dict) else {}


def _first_non_empty(*values):
    for value in values:
        if value is None:
            continue
        value = str(value).strip()
        if value:
            return value
    return ""


def _resolve_document(ciudadano, observaciones):
    return _first_non_empty(
        ciudadano.cuil_cuit,
        ciudadano.documento,
        observaciones.get("cuil"),
        observaciones.get("documento"),
    )


def _resolve_phone(ciudadano, observaciones):
    return _first_non_empty(ciudadano.telefono, observaciones.get("telefono"))


def build_comision_curso_nomina_excel(comision, inscripciones):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Nomina"
    worksheet.freeze_panes = "A2"
    worksheet.append(NOMINA_HEADERS)

    for cell in worksheet[1]:
        cell.font = Font(bold=True)

    for inscripcion in inscripciones:
        ciudadano = inscripcion.ciudadano
        observaciones = _parse_observaciones_json(inscripcion)
        worksheet.append(
            [
                ciudadano.apellido or "",
                ciudadano.nombre or "",
                _resolve_document(ciudadano, observaciones),
                _format_date(ciudadano.fecha_nacimiento),
                ciudadano.sexo.sexo if ciudadano.sexo_id and ciudadano.sexo else "",
                str(comision),
                comision.curso.nombre,
                comision.curso.centro.nombre,
                inscripcion.get_estado_display(),
                _format_datetime(inscripcion.fecha_inscripcion),
                inscripcion.get_origen_canal_display(),
                ciudadano.email or "",
                _resolve_phone(ciudadano, observaciones),
            ]
        )

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def build_nomina_filename(prefix, comision):
    slug = slugify(comision.codigo_comision) or f"comision-{comision.pk}"
    return f"{prefix}_{slug}.xlsx"
