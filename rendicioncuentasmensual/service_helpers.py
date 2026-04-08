from io import BytesIO

from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def construir_documentacion_para_detalle(
    documentos, categorias, categorias_con_historial
):
    grouped = {item["codigo"]: [] for item in categorias}
    documentos_activos_por_id = {documento.id: documento for documento in documentos}

    for categoria in categorias:
        codigo = categoria["codigo"]
        documentos_categoria = _documentos_por_categoria(documentos, codigo)
        if codigo not in categorias_con_historial:
            grouped[codigo] = _ordenar_documentos_sin_historial(documentos_categoria)
            continue

        grouped[codigo] = _ordenar_documentos_con_historial(
            documentos_categoria,
            documentos_activos_por_id,
        )

    return grouped


def _documentos_por_categoria(documentos, codigo):
    return [documento for documento in documentos if documento.categoria == codigo]


def _ordenar_documentos_sin_historial(documentos_categoria):
    archivos = sorted(
        documentos_categoria,
        key=lambda item: (item.fecha_creacion, item.id),
    )
    for archivo in archivos:
        archivo.subsanaciones_historial = []
    return archivos


def _ordenar_documentos_con_historial(
    documentos_categoria, documentos_activos_por_id
):
    hijos_por_documento = {}
    for documento in documentos_categoria:
        parent_id = documento.documento_subsanado_id
        if parent_id and parent_id in documentos_activos_por_id:
            hijos_por_documento.setdefault(parent_id, []).append(documento)

    raices = [
        documento
        for documento in documentos_categoria
        if not documento.documento_subsanado_id
        or documento.documento_subsanado_id not in documentos_activos_por_id
    ]
    return [
        _principal_con_historial(raiz, hijos_por_documento)
        for raiz in sorted(raices, key=lambda item: (item.fecha_creacion, item.id))
    ]


def _principal_con_historial(raiz, hijos_por_documento):
    cadena = []
    pendientes = [raiz]
    while pendientes:
        actual = pendientes.pop(0)
        cadena.append(actual)
        pendientes.extend(
            sorted(
                hijos_por_documento.get(actual.id, []),
                key=lambda item: (item.fecha_creacion, item.id),
            )
        )

    principal = max(cadena, key=lambda item: (item.fecha_creacion, item.id))
    principal.estado_visual_override = principal.estado
    principal.estado_visual_display_override = principal.get_estado_display()
    principal.subsanaciones_historial = sorted(
        [item for item in cadena if item.id != principal.id],
        key=lambda item: (item.fecha_creacion, item.id),
        reverse=True,
    )
    for historico in principal.subsanaciones_historial:
        historico.estado_visual_override = "subsanado"
        historico.estado_visual_display_override = "Subsanado"
    return principal


def generar_pdf_desde_imagen(archivo, nombre):
    buffer = BytesIO()
    pdf_buffer = BytesIO()
    try:
        archivo.open("rb")
        buffer.write(archivo.read())
    finally:
        cerrar_archivo_seguro(archivo)

    image_reader = ImageReader(BytesIO(buffer.getvalue()))
    page_width, page_height = A4
    margin = 36
    draw_width, draw_height, draw_x, draw_y = _calcular_posicion_imagen(
        image_reader, page_width, page_height, margin
    )

    pdf = canvas.Canvas(pdf_buffer, pagesize=A4)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(margin, page_height - margin, nombre)
    pdf.drawImage(
        image_reader,
        draw_x,
        max(draw_y, margin),
        width=draw_width,
        height=draw_height,
        preserveAspectRatio=True,
        mask="auto",
    )
    pdf.showPage()
    pdf.save()
    return pdf_buffer.getvalue()


def _calcular_posicion_imagen(image_reader, page_width, page_height, margin):
    image_width, image_height = image_reader.getSize()
    available_width = page_width - (margin * 2)
    available_height = page_height - (margin * 2) - 24
    scale = min(available_width / image_width, available_height / image_height)
    draw_width = image_width * scale
    draw_height = image_height * scale
    draw_x = (page_width - draw_width) / 2
    draw_y = (page_height - draw_height) / 2 - 10
    return draw_width, draw_height, draw_x, draw_y


def generar_pdf_placeholder(nombre):
    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=A4)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(40, 800, nombre)
    pdf.setFont("Helvetica", 11)
    pdf.drawString(
        40,
        772,
        "No se pudo incrustar este archivo en el PDF consolidado.",
    )
    pdf.showPage()
    pdf.save()
    return pdf_buffer.getvalue()


def iterar_documentos_para_pdf(categorias):
    for categoria in categorias:
        for archivo in categoria["archivos"]:
            yield archivo
            yield from getattr(archivo, "subsanaciones_historial", [])


def cerrar_archivo_seguro(archivo):
    try:
        archivo.close()
    except Exception:
        pass


def leer_pdf_documento(archivo):
    archivo.open("rb")
    return PdfReader(archivo)
