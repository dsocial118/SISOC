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
    "G\u00e9nero",
    "Comisi\u00f3n",
    "Curso",
    "Centro de Formaci\u00f3n",
    "Estado de Inscripci\u00f3n",
    "Fecha de Inscripci\u00f3n",
    "Canal de Inscripci\u00f3n",
    "Email",
    "Tel\u00e9fono",
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


def _resolve_document(ciudadano):
    if ciudadano.cuil_cuit:
        return ciudadano.cuil_cuit
    if ciudadano.documento is None:
        return ""
    return str(ciudadano.documento)


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
        worksheet.append(
            [
                ciudadano.apellido or "",
                ciudadano.nombre or "",
                _resolve_document(ciudadano),
                _format_date(ciudadano.fecha_nacimiento),
                ciudadano.sexo.sexo if ciudadano.sexo_id and ciudadano.sexo else "",
                str(comision),
                comision.curso.nombre,
                comision.curso.centro.nombre,
                inscripcion.get_estado_display(),
                _format_datetime(inscripcion.fecha_inscripcion),
                inscripcion.get_origen_canal_display(),
                ciudadano.email or "",
                ciudadano.telefono or "",
            ]
        )

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def build_nomina_filename(prefix, comision):
    slug = slugify(comision.codigo_comision) or f"comision-{comision.pk}"
    return f"{prefix}_{slug}.xlsx"
