from io import BytesIO
import copy
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Iterable

from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Max, Q
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from lxml import etree

from comedores.models import Nomina
from pwa.models import NominaDestinatariosDocumentoPWA


DDJJ_TEXTO_PROVISORIO = (
    "Declaro que los datos consignados en la presente nomina son veridicos "
    "y se corresponden con los destinatarios activos de la prestacion alimentaria."
)


def _display_value(value):
    value = str(value or "").strip()
    return value if value else "-"


def _format_date(value):
    if not value:
        return "-"
    return value.strftime("%d/%m/%Y")


def _format_period(periodo):
    return periodo.strftime("%m/%Y")


def _format_address(comedor):
    parts = [
        comedor.calle,
        str(comedor.numero) if comedor.numero else "",
        f"Barrio {comedor.barrio}" if comedor.barrio else "",
        f"CP {comedor.codigo_postal}" if comedor.codigo_postal else "",
    ]
    return ", ".join(part for part in parts if part) or "-"


def _gender_label(ciudadano):
    sexo = getattr(ciudadano, "sexo", None)
    return _display_value(getattr(sexo, "sexo", None))


def _full_name(user):
    if not user or not getattr(user, "is_authenticated", False):
        return "-"
    full_name = " ".join(
        part
        for part in [getattr(user, "first_name", ""), getattr(user, "last_name", "")]
        if part
    ).strip()
    return full_name or getattr(user, "username", "-")


def _nomina_alimentaria_activa_queryset(comedor_id):
    queryset = (
        Nomina.objects.filter(
            (
                Q(admision__comedor_id=comedor_id)
                | Q(comedor_id=comedor_id, admision__isnull=True)
            ),
            deleted_at__isnull=True,
            estado=Nomina.ESTADO_ACTIVO,
        )
        .select_related("ciudadano", "ciudadano__sexo")
        .order_by("ciudadano__apellido", "ciudadano__nombre", "id")
    )
    return queryset


def _build_pdf(*, comedor, periodo_referencia, nominas, actor):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    small = ParagraphStyle("Small", parent=normal, fontSize=8, leading=10)
    title = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontSize=13,
        leading=16,
        alignment=1,
        spaceAfter=8,
    )
    subtitle = ParagraphStyle(
        "Subtitle",
        parent=normal,
        fontSize=9,
        leading=12,
        alignment=1,
        spaceAfter=8,
    )

    elements = [
        Paragraph("NOMINA MENSUAL DE DESTINATARIOS", title),
        Paragraph("DOCUMENTOS DE GESTION SOCIAL II", subtitle),
        Paragraph(f"Periodo: {_format_period(periodo_referencia)}", normal),
        Spacer(1, 0.15 * cm),
    ]

    header_data = [
        [
            "Programa:",
            _display_value(getattr(getattr(comedor, "programa", None), "nombre", None)),
        ],
        ["Nombre del comedor/merendero:", _display_value(comedor.nombre)],
        ["Direccion:", _format_address(comedor)],
        [
            "Localidad:",
            _display_value(
                getattr(getattr(comedor, "localidad", None), "nombre", None)
            ),
        ],
        [
            "Provincia:",
            _display_value(
                getattr(getattr(comedor, "provincia", None), "nombre", None)
            ),
        ],
    ]
    header_table = Table(header_data, colWidths=[5.0 * cm, 12.0 * cm])
    header_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.extend([header_table, Spacer(1, 0.25 * cm)])

    table_data = [
        ["Orden", "Apellido", "Nombre", "DNI", "Fecha de nacimiento", "Genero"]
    ]
    for index, nomina in enumerate(nominas, start=1):
        ciudadano = nomina.ciudadano
        table_data.append(
            [
                str(index),
                _display_value(getattr(ciudadano, "apellido", None)),
                _display_value(getattr(ciudadano, "nombre", None)),
                _display_value(getattr(ciudadano, "documento", None)),
                _format_date(getattr(ciudadano, "fecha_nacimiento", None)),
                _gender_label(ciudadano),
            ]
        )

    rows_table = Table(
        table_data,
        colWidths=[1.6 * cm, 3.4 * cm, 3.4 * cm, 2.5 * cm, 3.0 * cm, 3.0 * cm],
        repeatRows=1,
    )
    rows_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E6E6E6")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 1), (0, -1), "CENTER"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.extend([rows_table, Spacer(1, 0.35 * cm)])

    generated_at = timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M")
    elements.extend(
        [
            Paragraph(f"[X] {DDJJ_TEXTO_PROVISORIO}", small),
            Spacer(1, 0.15 * cm),
            Paragraph(f"Generado por: {_full_name(actor)}", small),
            Paragraph(f"Fecha de generacion: {generated_at}", small),
        ]
    )

    doc.build(elements)
    return buffer.getvalue()


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W_XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
DOCX_NS = {"w": W_NS}


def _set_paragraph_text(paragraph, value):
    texts = paragraph.xpath(".//w:t", namespaces=DOCX_NS)
    if texts:
        texts[0].text = str(value)
        texts[0].set(W_XML_SPACE, "preserve")
        for extra in texts[1:]:
            extra.text = ""
        return
    run = etree.SubElement(paragraph, f"{{{W_NS}}}r")
    text = etree.SubElement(run, f"{{{W_NS}}}t")
    text.text = str(value)


def _set_cell_text(cell, value):
    paragraph = cell.find("w:p", DOCX_NS)
    _set_paragraph_text(paragraph, value)


def _gender_columns(ciudadano):
    label = _gender_label(ciudadano).lower()
    return (
        "X" if "fem" in label else "",
        "X" if "mas" in label else "",
        "X" if "fem" not in label and "mas" not in label else "",
    )


def _render_nomina_docx(
    template_path, output_path, *, comedor, periodo, nominas, actor
):
    with zipfile.ZipFile(template_path, "r") as source_zip:
        root = etree.fromstring(source_zip.read("word/document.xml"))
        body = root.find("w:body", DOCX_NS)
        paragraphs = body.findall("w:p", DOCX_NS)
        direccion = _format_address(comedor)
        localidad = _display_value(
            getattr(getattr(comedor, "localidad", None), "nombre", None)
        )
        provincia = _display_value(
            getattr(getattr(comedor, "provincia", None), "nombre", None)
        )
        _set_paragraph_text(
            paragraphs[4], f"NOMBRE DEL ESPACIO: {_display_value(comedor.nombre)}"
        )
        _set_paragraph_text(
            paragraphs[5],
            f"DIRECCIÓN: {direccion}     LOCALIDAD: {localidad}     PROVINCIA: {provincia}",
        )
        _set_paragraph_text(
            paragraphs[6],
            f"MES: {periodo.month:02d}                         AÑO: {periodo.year}",
        )
        _set_paragraph_text(
            paragraphs[14], f"Usuario: {getattr(actor, 'username', '-')}"
        )
        _set_paragraph_text(paragraphs[15], f"Apellido y nombre: {_full_name(actor)}")
        _set_paragraph_text(paragraphs[16], f"DNI: {getattr(actor, 'username', '-')}")

        table = body.find(".//w:tbl", DOCX_NS)
        rows = table.findall("w:tr", DOCX_NS)
        template_row = rows[2]
        while len(rows) < max(3, len(nominas)) + 2:
            new_row = copy.deepcopy(template_row)
            table.append(new_row)
            rows.append(new_row)
        for index, row in enumerate(rows[2:], start=1):
            cells = row.findall("w:tc", DOCX_NS)
            if index <= len(nominas):
                ciudadano = nominas[index - 1].ciudadano
                femenino, masculino, otro = _gender_columns(ciudadano)
                values = (
                    index,
                    _display_value(getattr(ciudadano, "apellido", None)),
                    _display_value(getattr(ciudadano, "nombre", None)),
                    _display_value(getattr(ciudadano, "documento", None)),
                    _format_date(getattr(ciudadano, "fecha_nacimiento", None)),
                    femenino,
                    masculino,
                    otro,
                )
            else:
                values = (index, "", "", "", "", "", "", "")
            for cell, value in zip(cells, values):
                _set_cell_text(cell, value)

        rendered_xml = etree.tostring(
            root, xml_declaration=True, encoding="UTF-8", standalone=True
        )
        with zipfile.ZipFile(output_path, "w") as output_zip:
            for item in source_zip.infolist():
                content = (
                    rendered_xml
                    if item.filename == "word/document.xml"
                    else source_zip.read(item.filename)
                )
                output_zip.writestr(item, content)


def _build_pdf_from_template(*, comedor, periodo_referencia, nominas, actor):
    template_path = (
        Path(settings.BASE_DIR)
        / "pwa"
        / "files"
        / "varios"
        / "NOMINA.DE.DESTINATARIOS.docx"
    )
    with tempfile.TemporaryDirectory(prefix="nomina-destinatarios-") as temp_dir:
        temp_path = Path(temp_dir)
        docx_path = temp_path / "nomina-destinatarios.docx"
        pdf_path = temp_path / "nomina-destinatarios.pdf"
        profile_uri = (temp_path / "libreoffice-profile").resolve().as_uri()
        _render_nomina_docx(
            template_path,
            docx_path,
            comedor=comedor,
            periodo=periodo_referencia,
            nominas=nominas,
            actor=actor,
        )
        result = subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--nologo",
                "--nodefault",
                "--nofirststartwizard",
                f"-env:UserInstallation={profile_uri}",
                "--convert-to",
                "pdf",
                "--outdir",
                str(temp_path),
                str(docx_path),
            ],
            capture_output=True,
            check=False,
            timeout=120,
        )
        if result.returncode != 0 or not pdf_path.exists():
            detail = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(detail or "No se pudo generar el PDF de nómina.")
        return pdf_path.read_bytes()


def serialize_nomina_destinatarios_documento(documento, request=None):
    if not documento or not documento.archivo:
        return None
    url = documento.archivo.url
    return {
        "id": documento.id,
        "periodo_referencia": documento.periodo_referencia,
        "periodo_label": _format_period(documento.periodo_referencia),
        "version": documento.version,
        "cantidad_destinatarios": documento.cantidad_destinatarios,
        "fecha_generacion": documento.fecha_generacion,
        "archivo_url": request.build_absolute_uri(url) if request else url,
        "archivo_nombre": documento.archivo.name.split("/")[-1],
    }


def generar_nomina_destinatarios_pdf(
    *,
    comedor,
    periodo_referencia,
    actor=None,
    nomina_ids: Iterable[int] | None = None,
):
    nominas_queryset = _nomina_alimentaria_activa_queryset(comedor.id)
    if nomina_ids is not None:
        nominas_queryset = nominas_queryset.filter(id__in=list(nomina_ids))
    programa_nombre = str(
        getattr(getattr(comedor, "programa", None), "nombre", "") or ""
    )
    if programa_nombre.strip().lower() != "alimentar comunidad":
        nominas_queryset = nominas_queryset.filter(
            Q(perfil_pwa__asistencia_alimentaria=True) | Q(perfil_pwa__isnull=True)
        )
    nominas = list(nominas_queryset)
    next_version = (
        NominaDestinatariosDocumentoPWA.objects.filter(
            comedor=comedor,
            periodo_referencia=periodo_referencia,
        ).aggregate(max_version=Max("version"))["max_version"]
        or 0
    ) + 1
    pdf_bytes = _build_pdf_from_template(
        comedor=comedor,
        periodo_referencia=periodo_referencia,
        nominas=nominas,
        actor=actor,
    )
    filename = (
        f"nomina-destinatarios-{comedor.id}-"
        f"{periodo_referencia:%Y-%m}-v{next_version}.pdf"
    )
    documento = NominaDestinatariosDocumentoPWA.objects.create(
        comedor=comedor,
        periodo_referencia=periodo_referencia,
        version=next_version,
        cantidad_destinatarios=len(nominas),
        generado_por=actor if getattr(actor, "is_authenticated", False) else None,
        metadata={
            "origen": "pwa_nomina_alimentaria_mensual",
            "nomina_ids": [nomina.id for nomina in nominas],
        },
    )
    documento.archivo.save(filename, ContentFile(pdf_bytes), save=True)
    return documento
