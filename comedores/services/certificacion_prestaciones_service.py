import copy
import subprocess
import tempfile
import zipfile
from pathlib import Path

from django.conf import settings
from lxml import etree

from comedores.utils import is_abordaje_comunitario_linea_tradicional_program


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


def _reemplazar_texto(paragraph, value):
    texts = paragraph.xpath(".//w:t", namespaces=NS)
    if texts:
        texts[0].text = str(value)
        for extra in texts[1:]:
            extra.text = ""
        return
    _agregar_texto(paragraph, value)


def _paragraph_by_label(paragraphs, label):
    for paragraph in paragraphs:
        text = "".join(paragraph.itertext()).strip()
        if text.startswith(label):
            return paragraph
    return None


def _completar_plantilla(
    template_path,
    output_path,
    *,
    comedor,
    periodo,
    usuario,
    usuario_principal=None,
    observaciones="",
    source,
):
    with zipfile.ZipFile(template_path, "r") as source_zip:
        document_xml = source_zip.read("word/document.xml")
        root = etree.fromstring(document_xml)
        body = root.find("w:body", NS)
        paragraphs = body.findall("w:p", NS)

        direccion = " ".join(
            part for part in (comedor.calle, str(comedor.numero or "")) if part
        )
        values = {
            "NOMBRE DEL ESPACIO:": comedor.nombre or "",
            "DIRECCIÓN:": direccion,
            "LOCALIDAD:": getattr(getattr(comedor, "localidad", None), "nombre", ""),
            "PROVINCIA:": getattr(getattr(comedor, "provincia", None), "nombre", ""),
            "MES:": str(periodo.month),
            "AÑO:": str(periodo.year),
        }
        for label, value in values.items():
            paragraph = _paragraph_by_label(paragraphs, label)
            if paragraph is not None:
                _agregar_texto(paragraph, f" {value}")

        signer_labels = ("Usuario autorizado:", "Apellido y nombre:", "DNI:")
        signer_values = (
            usuario.username,
            usuario.get_full_name() or usuario.username,
            usuario.username,
        )
        for label, value in zip(signer_labels, signer_values):
            paragraph = _paragraph_by_label(paragraphs, label)
            if paragraph is not None:
                _agregar_texto(paragraph, f" {value}")

        if usuario_principal:
            principal_labels = (
                "Usuario Presidente de la organización que autoriza:",
                "Apellido y nombre:",
                "DNI:",
            )
            start = next(
                (
                    index
                    for index, paragraph in enumerate(paragraphs)
                    if "Usuario Presidente" in "".join(paragraph.itertext())
                ),
                None,
            )
            principal_values = (
                usuario_principal.username,
                usuario_principal.get_full_name() or usuario_principal.username,
                usuario_principal.username,
            )
            if start is not None:
                for label, value in zip(principal_labels, principal_values):
                    paragraph = next(
                        (
                            item
                            for item in paragraphs[start:]
                            if "".join(item.itertext()).strip().startswith(label)
                        ),
                        None,
                    )
                    if paragraph is not None:
                        _agregar_texto(paragraph, f" {value}")

        if observaciones:
            motivo = _paragraph_by_label(
                paragraphs,
                "Se deja constancia que no se cumplieron las prestaciones",
            )
            if motivo is not None:
                _agregar_texto(motivo, f" {observaciones}")

        table = body.find(".//w:tbl", NS)
        rows = table.findall("w:tr", NS)
        tipos = list(TIPOS)
        if is_abordaje_comunitario_linea_tradicional_program(comedor):
            merienda_reforzada_row = copy.deepcopy(rows[4])
            table.insert(5, merienda_reforzada_row)
            _reemplazar_texto(
                merienda_reforzada_row.findall("w:tc", NS)[0].find("w:p", NS),
                "Merienda Reforzada",
            )
            tipos.insert(3, "merienda_reforzada")
            rows = table.findall("w:tr", NS)
        total_general = 0
        for row_index, tipo in enumerate(tipos, start=2):
            cells = rows[row_index].findall("w:tc", NS)
            total_tipo = 0
            for column_index, dia in enumerate(DIAS, start=1):
                value = int(getattr(source, f"aprobadas_{tipo}_{dia}", 0) or 0)
                total_tipo += value
                paragraph = cells[column_index].find("w:p", NS)
                _agregar_texto(paragraph, str(value))
            total_general += total_tipo
            _agregar_texto(cells[8].find("w:p", NS), str(total_tipo))
        total_row = rows[2 + len(tipos)]
        _agregar_texto(
            total_row.findall("w:tc", NS)[1].find("w:p", NS), str(total_general)
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


def generar_certificacion_prestaciones_pdf(
    *,
    comedor,
    periodo,
    usuario,
    source,
    conforme,
    observaciones="",
    usuario_principal=None,
):
    template_name = {
        (True, False): "PRESTACIONES.1.docx",
        (True, True): "PRESTACIONES.2.docx",
        (False, False): "PRESTACIONES.3.docx",
        (False, True): "PRESTACIONES.54.docx",
    }[(conforme, usuario_principal is not None)]
    template_path = Path(settings.BASE_DIR) / "pwa" / "files" / "varios" / template_name
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
            usuario_principal=usuario_principal,
            observaciones=observaciones,
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
