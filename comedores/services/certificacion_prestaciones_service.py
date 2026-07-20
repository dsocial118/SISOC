import subprocess
import tempfile
import zipfile
from pathlib import Path

from django.conf import settings
from lxml import etree


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
DIAS = ("lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo")
TIPOS = ("desayuno", "almuerzo", "merienda", "cena")


def _agregar_texto(paragraph, value):
    texts = paragraph.xpath(".//w:t", namespaces=NS)
    if texts:
        texts[-1].text = f"{texts[-1].text or ''}{value}"
        return
    run = etree.SubElement(paragraph, f"{{{W_NS}}}r")
    etree.SubElement(run, f"{{{W_NS}}}t").text = str(value)


def _completar_plantilla(
    template_path, output_path, *, comedor, periodo, usuario, source
):
    with zipfile.ZipFile(template_path, "r") as source_zip:
        document_xml = source_zip.read("word/document.xml")
        root = etree.fromstring(document_xml)
        body = root.find("w:body", NS)
        paragraphs = body.findall("w:p", NS)

        direccion = " ".join(
            part for part in (comedor.calle, str(comedor.numero or "")) if part
        )
        _agregar_texto(paragraphs[2], f" {comedor.nombre or ''}")
        _agregar_texto(paragraphs[3], direccion)
        _agregar_texto(
            paragraphs[4], getattr(getattr(comedor, "localidad", None), "nombre", "")
        )
        _agregar_texto(
            paragraphs[5], getattr(getattr(comedor, "provincia", None), "nombre", "")
        )
        _agregar_texto(paragraphs[6], str(periodo.month))
        _agregar_texto(paragraphs[7], str(periodo.year))
        _agregar_texto(paragraphs[12], f" {usuario.username}")
        _agregar_texto(
            paragraphs[13], f" {usuario.get_full_name() or usuario.username}"
        )
        _agregar_texto(paragraphs[14], f" {usuario.username}")

        table = body.find(".//w:tbl", NS)
        rows = table.findall("w:tr", NS)
        total_general = 0
        for row_index, tipo in enumerate(TIPOS, start=2):
            cells = rows[row_index].findall("w:tc", NS)
            total_tipo = 0
            for column_index, dia in enumerate(DIAS, start=1):
                value = int(getattr(source, f"aprobadas_{tipo}_{dia}", 0) or 0)
                total_tipo += value
                paragraph = cells[column_index].find("w:p", NS)
                _agregar_texto(paragraph, str(value))
            total_general += total_tipo
            _agregar_texto(cells[8].find("w:p", NS), str(total_tipo))
        _agregar_texto(
            rows[6].findall("w:tc", NS)[1].find("w:p", NS), str(total_general)
        )

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


def generar_certificacion_prestaciones_pdf(*, comedor, periodo, usuario, source):
    template_path = (
        Path(settings.BASE_DIR)
        / "pwa"
        / "files"
        / "varios"
        / "PROGRAMA.ALIMENTAR.COMUNIDAD.docx"
    )
    with tempfile.TemporaryDirectory(prefix="certificacion-prestaciones-") as temp_dir:
        temp_path = Path(temp_dir)
        docx_path = temp_path / "certificacion.docx"
        pdf_path = temp_path / "certificacion.pdf"
        profile_uri = (temp_path / "libreoffice-profile").resolve().as_uri()
        _completar_plantilla(
            template_path,
            docx_path,
            comedor=comedor,
            periodo=periodo,
            usuario=usuario,
            source=source,
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
            raise RuntimeError(detail or "No se pudo generar la certificación PDF.")
        return pdf_path.read_bytes()
