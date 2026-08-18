from __future__ import annotations

import logging
import os
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from tempfile import TemporaryDirectory

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from pdf2image import convert_from_bytes
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ciudadanos.models import Ciudadano
from centrodeinfancia.models import AccesoCDI, NominaCentroInfancia


logger = logging.getLogger(__name__)

PAGE_SIZE = landscape(A4)
PAGE_MARGIN = 18
TABLE_FONT_SIZE = 9
FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
AGE_MEASURE_LABELS = {"meses": "Meses", "anios": "Años"}


class NominaNinosPDFError(Exception):
    """Error controlado durante la construcción del descargable."""


@dataclass(frozen=True)
class NinoRow:
    centro_id: int
    apellido: str
    nombre: str
    dni: str
    fecha_nacimiento: str
    edad: str
    medida: str
    sexo: str
    renaper_nino: str
    adulto_apellido: str
    adulto_nombre: str
    adulto_cuit: str
    adulto_fecha_nacimiento: str
    adulto_renaper: str
    sort_key: tuple


@dataclass(frozen=True)
class CDIGroup:
    centro_id: int
    codigo: str
    nombre: str
    referente: str
    referente_cuil: str
    rows: tuple[NinoRow, ...]


@dataclass(frozen=True)
class ExportData:
    provincia: str
    usuario: str
    rol: str
    usuario_cuil: str
    generado_en: datetime
    centros: tuple[CDIGroup, ...]

    @property
    def total_ninos(self):
        return sum(len(centro.rows) for centro in self.centros)


def _value(primary, fallback=None):
    if primary not in (None, ""):
        return primary
    return fallback


def _text(value):
    if value in (None, ""):
        return "-"
    return str(value).strip() or "-"


def _date_text(value):
    if not value:
        return "-"
    return value.strftime("%d/%m/%Y")


def _normalize(value):
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    return " ".join(
        "".join(char for char in normalized if not unicodedata.combining(char)).split()
    ).casefold()


def _calculate_age(birth_date, unit, as_of):
    if not birth_date or unit not in {"meses", "anios"}:
        return None
    if birth_date > as_of:
        return None
    years = (
        as_of.year
        - birth_date.year
        - ((as_of.month, as_of.day) < (birth_date.month, birth_date.day))
    )
    if unit == "anios":
        return years
    return (
        (as_of.year - birth_date.year) * 12
        + as_of.month
        - birth_date.month
        - (as_of.day < birth_date.day)
    )


def _document_sort_key(value):
    digits = str(value or "").strip()
    if digits.isdigit():
        return 0, int(digits)
    return 1, digits


def _get_profile_cuil(user):
    try:
        return _text(user.profile.cuil)
    except (AttributeError, ObjectDoesNotExist):
        return "-"


def _build_adult_validation_map(documentos):
    matches = defaultdict(list)
    if not documentos:
        return {}
    for documento, estado in Ciudadano.objects.filter(
        documento__in=documentos
    ).values_list("documento", "estado_validacion_renaper"):
        matches[str(documento)].append(estado)
    return {
        documento: (
            "Sí"
            if len(estados) == 1 and estados[0] == Ciudadano.RENAPER_VALIDADO
            else "No"
        )
        for documento, estados in matches.items()
    }


def _build_referent_cuil_map(centros):
    center_by_id = {centro.pk: centro for centro in centros}
    matches = defaultdict(list)
    accesos = AccesoCDI.objects.filter(
        centro_id__in=center_by_id,
        activo=True,
    ).select_related("user", "user__profile")
    for acceso in accesos:
        centro = center_by_id[acceso.centro_id]
        expected_email = _normalize(centro.email_referente)
        if expected_email and _normalize(acceso.user.email) == expected_email:
            matches[centro.pk].append(_get_profile_cuil(acceso.user))
    return {
        centro_id: values[0] if len(values) == 1 else "-"
        for centro_id, values in matches.items()
    }


def _resolved_child_fields(registro):
    ciudadano = registro.ciudadano
    apellido = _value(registro.apellido, ciudadano.apellido)
    nombre = _value(registro.nombre, ciudadano.nombre)
    dni = _value(registro.dni, ciudadano.documento)
    birth_date = _value(registro.fecha_nacimiento, ciudadano.fecha_nacimiento)
    sexo = _value(registro.sexo, ciudadano.sexo if ciudadano.sexo_id else None)
    return apellido, nombre, dni, birth_date, sexo


def _deduplicate_registros(registros):
    selected = []
    seen_citizen_ids = set()
    seen_documents = set()
    seen_identity_keys = set()
    duplicate_count = 0
    for registro in registros:
        apellido, nombre, dni, birth_date, sexo = _resolved_child_fields(registro)
        document_key = str(dni).strip() if dni not in (None, "") else None
        identity_key = (
            _normalize(apellido),
            _normalize(nombre),
            document_key or "",
            birth_date.isoformat() if birth_date else "",
            _normalize(sexo),
        )
        if (
            registro.ciudadano_id in seen_citizen_ids
            or (document_key is not None and document_key in seen_documents)
            or identity_key in seen_identity_keys
        ):
            duplicate_count += 1
            continue
        seen_citizen_ids.add(registro.ciudadano_id)
        if document_key is not None:
            seen_documents.add(document_key)
        seen_identity_keys.add(identity_key)
        selected.append(registro)
    return selected, duplicate_count


def build_export_data(  # pylint: disable=too-many-locals
    *, user, provincia, generado_en=None
):
    generado_en = timezone.localtime(generado_en or timezone.now())
    registros = list(
        NominaCentroInfancia.objects.filter(
            centro__provincia=provincia,
            estado=NominaCentroInfancia.ESTADO_ACTIVO,
        )
        .select_related("centro", "ciudadano", "ciudadano__sexo")
        .order_by("-fecha", "-id")
    )
    registros, duplicate_count = _deduplicate_registros(registros)
    if duplicate_count:
        logger.warning(
            "Se omitieron filas duplicadas de la nómina provincial",
            extra={
                "data": {
                    "provincia_id": provincia.pk,
                    "duplicados": duplicate_count,
                }
            },
        )

    adult_documents = {
        str(registro.responsable_legal_1_dni)
        for registro in registros
        if registro.responsable_legal_1_dni
    }
    adult_validation = _build_adult_validation_map(adult_documents)
    centros = {registro.centro_id: registro.centro for registro in registros}
    referent_cuils = _build_referent_cuil_map(centros.values())
    rows_by_center = defaultdict(list)
    as_of = generado_en.date()

    for registro in registros:
        apellido, nombre, dni, birth_date, sexo = _resolved_child_fields(registro)
        age = _calculate_age(birth_date, registro.edad_unidad, as_of)
        medida = AGE_MEASURE_LABELS.get(registro.edad_unidad, "-")
        measure_rank = {"meses": 0, "anios": 1}.get(registro.edad_unidad, 2)
        age_rank = age if age is not None else 10**9
        dni_text = _text(dni)
        row = NinoRow(
            centro_id=registro.centro_id,
            apellido=_text(apellido),
            nombre=_text(nombre),
            dni=dni_text,
            fecha_nacimiento=_date_text(birth_date),
            edad=_text(age),
            medida=_text(medida),
            sexo=_text(sexo),
            renaper_nino=(
                "Sí"
                if registro.ciudadano.estado_validacion_renaper
                == Ciudadano.RENAPER_VALIDADO
                else "No"
            ),
            adulto_apellido=_text(registro.responsable_legal_1_apellido),
            adulto_nombre=_text(registro.responsable_legal_1_nombre),
            adulto_cuit=_text(registro.responsable_legal_1_cuit),
            adulto_fecha_nacimiento=_date_text(
                registro.responsable_legal_1_fecha_nacimiento
            ),
            adulto_renaper=adult_validation.get(
                str(registro.responsable_legal_1_dni),
                "No",
            ),
            sort_key=(
                measure_rank,
                age_rank,
                _normalize(apellido),
                _normalize(nombre),
                _document_sort_key(dni),
                registro.pk,
            ),
        )
        rows_by_center[registro.centro_id].append(row)

    cdi_groups = []
    for centro_id, centro in sorted(
        centros.items(),
        key=lambda item: (_normalize(item[1].nombre), item[0]),
    ):
        rows = tuple(sorted(rows_by_center[centro_id], key=lambda row: row.sort_key))
        referente = " ".join(
            part
            for part in (centro.apellido_referente, centro.nombre_referente)
            if part
        )
        cdi_groups.append(
            CDIGroup(
                centro_id=centro_id,
                codigo=_text(centro.codigo_cdi),
                nombre=_text(centro.nombre),
                referente=_text(referente),
                referente_cuil=referent_cuils.get(centro_id, "-"),
                rows=rows,
            )
        )

    return ExportData(
        provincia=_text(provincia.nombre),
        usuario=_text(user.get_username()),
        rol="SIMEPI - EGP",
        usuario_cuil=_get_profile_cuil(user),
        generado_en=generado_en,
        centros=tuple(cdi_groups),
    )


def _register_fonts():
    global FONT_REGULAR, FONT_BOLD  # pylint: disable=global-statement
    if "SISOCArial" in pdfmetrics.getRegisteredFontNames():
        FONT_REGULAR = "SISOCArial"
        FONT_BOLD = "SISOCArial-Bold"
        return
    candidates = (
        (
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ),
        (
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ),
        ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
    )
    for regular_path, bold_path in candidates:
        if os.path.exists(regular_path) and os.path.exists(bold_path):
            pdfmetrics.registerFont(TTFont("SISOCArial", regular_path))
            pdfmetrics.registerFont(TTFont("SISOCArial-Bold", bold_path))
            FONT_REGULAR = "SISOCArial"
            FONT_BOLD = "SISOCArial-Bold"
            return


def _escape_paragraph(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _paragraph(value, style):
    return Paragraph(_escape_paragraph(value), style)


def _header_footer(canvas_obj, _doc, export_data):
    canvas_obj.saveState()
    width, height = PAGE_SIZE
    canvas_obj.setFont(FONT_BOLD, 10)
    canvas_obj.drawString(PAGE_MARGIN, height - 22, "Nómina provincial de niños")
    canvas_obj.setFont(FONT_REGULAR, 10)
    actor = (
        f"Provincia: {export_data.provincia} | Rol: {export_data.rol} | "
        f"Usuario: {export_data.usuario} | CUIL: {export_data.usuario_cuil}"
    )
    canvas_obj.drawString(PAGE_MARGIN, height - 36, actor)
    canvas_obj.setStrokeColor(colors.HexColor("#808080"))
    canvas_obj.line(PAGE_MARGIN, height - 42, width - PAGE_MARGIN, height - 42)
    canvas_obj.restoreState()


class _NumberedCanvas(canvas.Canvas):  # pylint: disable=abstract-method
    def __init__(self, *args, export_data, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.export_data = export_data

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self._saved_page_states)
        for page_state in self._saved_page_states:
            self.__dict__.update(page_state)
            self._draw_page_details(page_count)
            super().showPage()
        super().save()

    def _draw_page_details(self, page_count):
        width, height = PAGE_SIZE
        generated = self.export_data.generado_en.strftime("%d/%m/%Y - %H:%M:%S")
        page_number = self._pageNumber
        self.saveState()
        self.setFillColor(colors.HexColor("#C7C7C7"))
        self.setFont(FONT_BOLD, 16)
        self.translate(width / 2, height / 2)
        self.rotate(28)
        watermark = (
            f"Provincia: {self.export_data.provincia} - "
            f"Usuario: {self.export_data.usuario} - {generated} - "
            f"Páginas: {page_number} de {page_count}."
        )
        self.drawCentredString(0, 0, watermark)
        self.restoreState()

        self.saveState()
        self.setFont(FONT_REGULAR, 9)
        self.setFillColor(colors.HexColor("#333333"))
        self.drawString(PAGE_MARGIN, 12, generated)
        self.drawRightString(
            width - PAGE_MARGIN,
            12,
            f"Página {page_number} de {page_count}",
        )
        self.restoreState()


def _table_styles():
    body = ParagraphStyle(
        "NominaBody",
        fontName=FONT_REGULAR,
        fontSize=TABLE_FONT_SIZE,
        leading=10,
        alignment=TA_LEFT,
        wordWrap="CJK",
    )
    header = ParagraphStyle(
        "NominaHeader",
        parent=body,
        fontName=FONT_BOLD,
        alignment=TA_CENTER,
    )
    cdi = ParagraphStyle(
        "NominaCDI",
        parent=body,
        fontName=FONT_BOLD,
        leading=11,
    )
    return body, header, cdi


def _build_cdi_table(group, available_width):
    body_style, header_style, cdi_style = _table_styles()
    headers = (
        "Apellido niño/a",
        "Nombre niño/a",
        "DNI niño/a",
        "Fecha nac. niño/a",
        "Edad",
        "Medida",
        "Sexo",
        "RENAPER niño/a",
        "Apellido adulto 1",
        "Nombre adulto 1",
        "CUIT adulto 1",
        "Fecha nac. adulto 1",
        "RENAPER adulto 1",
    )
    cdi_header = (
        f"CDI {group.codigo} - {group.nombre} | Referente: {group.referente} | "
        f"CUIL: {group.referente_cuil} | Niños activos únicos: {len(group.rows)}"
    )
    data = [
        [_paragraph(cdi_header, cdi_style)] + [""] * (len(headers) - 1),
        [_paragraph(header, header_style) for header in headers],
    ]
    for row in group.rows:
        data.append(
            [
                _paragraph(value, body_style)
                for value in (
                    row.apellido,
                    row.nombre,
                    row.dni,
                    row.fecha_nacimiento,
                    row.edad,
                    row.medida,
                    row.sexo,
                    row.renaper_nino,
                    row.adulto_apellido,
                    row.adulto_nombre,
                    row.adulto_cuit,
                    row.adulto_fecha_nacimiento,
                    row.adulto_renaper,
                )
            ]
        )
    base_widths = (66, 66, 47, 55, 31, 40, 45, 52, 62, 62, 60, 55, 52)
    scale = available_width / sum(base_widths)
    table = Table(
        data,
        colWidths=[width * scale for width in base_widths],
        repeatRows=2,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (-1, 0)),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9D9D9")),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#EFEFEF")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#777777")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def build_vector_pdf(export_data):
    _register_fonts()
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=PAGE_SIZE,
        leftMargin=PAGE_MARGIN,
        rightMargin=PAGE_MARGIN,
        topMargin=50,
        bottomMargin=26,
        title="Nómina provincial de niños",
        author="SISOC - SIMEPI",
    )
    styles = getSampleStyleSheet()
    summary_style = ParagraphStyle(
        "NominaSummary",
        parent=styles["Heading2"],
        fontName=FONT_BOLD,
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
    )
    story = []
    for group in export_data.centros:
        story.append(_build_cdi_table(group, document.width))
        story.append(Spacer(1, 10))
    if story:
        story.append(PageBreak())
    story.extend(
        [
            Spacer(1, 150),
            Paragraph(
                "Total de niños activos únicos de la provincia: "
                f"{export_data.total_ninos}",
                summary_style,
            ),
        ]
    )
    document.build(
        story,
        onFirstPage=lambda canvas_obj, doc: _header_footer(
            canvas_obj, doc, export_data
        ),
        onLaterPages=lambda canvas_obj, doc: _header_footer(
            canvas_obj, doc, export_data
        ),
        canvasmaker=lambda *args, **kwargs: _NumberedCanvas(
            *args,
            export_data=export_data,
            **kwargs,
        ),
    )
    return buffer.getvalue()


def rasterize_pdf(vector_pdf):
    with TemporaryDirectory(prefix="sisoc-nomina-ninos-") as temp_dir:
        image_paths = convert_from_bytes(
            vector_pdf,
            dpi=150,
            fmt="jpeg",
            jpegopt={"quality": 88, "optimize": True},
            output_folder=temp_dir,
            paths_only=True,
            thread_count=1,
            timeout=120,
        )
        if not image_paths:
            raise NominaNinosPDFError("La rasterización no generó páginas.")
        output = BytesIO()
        pdf = canvas.Canvas(output, pagesize=PAGE_SIZE, pageCompression=1)
        width, height = PAGE_SIZE
        for image_path in image_paths:
            pdf.drawImage(
                ImageReader(image_path),
                0,
                0,
                width=width,
                height=height,
            )
            pdf.showPage()
        pdf.save()
        return output.getvalue()


def generar_nomina_ninos_pdf(*, user, provincia, generado_en=None):
    try:
        export_data = build_export_data(
            user=user,
            provincia=provincia,
            generado_en=generado_en,
        )
        return rasterize_pdf(build_vector_pdf(export_data))
    except NominaNinosPDFError:
        raise
    except Exception as exc:  # pylint: disable=broad-exception-caught
        raise NominaNinosPDFError("No se pudo generar la nómina.") from exc
