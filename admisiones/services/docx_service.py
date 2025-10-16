from docxtpl import DocxTemplate
from django.conf import settings
from django.template.loader import get_template
from django.utils.html import strip_tags
from weasyprint import HTML
from docx import Document
import os
import io
import re
from xml.sax.saxutils import escape

from ..models.admisiones import (
    ArchivoAdmision,
    InformeTecnico,
    FormularioProyectoDeConvenio,
    FormularioProyectoDisposicion,
)


class DocumentTemplateService:

    @staticmethod
    def generar_docx(template_name, context, app_name="admisiones"):
        template_path = os.path.join(
            settings.BASE_DIR, app_name, "templates", app_name, "docx", template_name
        )

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template no encontrado: {template_path}")

        doc = DocxTemplate(template_path)
        clean_context = DocumentTemplateService._sanear_contexto(context)
        doc.render(clean_context)

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        return DocumentTemplateService._reparar_docx_para_office(buffer)

    @staticmethod
    def generar_pdf(template_name, context, app_name="admisiones"):
        template_path = f"{app_name}/pdf/{template_name}"
        template = get_template(template_path)

        clean_context = DocumentTemplateService._sanear_contexto(
            context, campos_sin_escape=["informe", "texto_comidas", "html_content"]
        )
        html_content = template.render(clean_context)

        pdf_buffer = io.BytesIO()
        HTML(string=html_content).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)

        return pdf_buffer

    @staticmethod
    def _sanear_contexto(context, campos_sin_escape=None):
        if campos_sin_escape is None:
            campos_sin_escape = ["informe", "texto_comidas"]

        clean_context = {}
        for k, v in context.items():
            if k in campos_sin_escape or isinstance(v, (list, dict)):
                clean_context[k] = v
            elif v is None:
                clean_context[k] = ""
            elif isinstance(v, str):
                clean_context[k] = escape(v)
            else:
                clean_context[k] = v
        return clean_context

    @staticmethod
    def _reparar_docx_para_office(buffer):
        try:
            buffer.seek(0)
            doc = Document(buffer)

            nuevo_buffer = io.BytesIO()
            doc.save(nuevo_buffer)
            nuevo_buffer.seek(0)

            return nuevo_buffer

        except Exception:
            buffer.seek(0)
            return buffer


class AdmisionesContextService:

    @staticmethod
    def preparar_contexto_informe_tecnico(informe):
        from ..utils import generar_texto_comidas

        prestaciones = AdmisionesContextService._generar_prestaciones_semanales(informe)
        texto_comidas_raw = generar_texto_comidas(informe)
        texto_comidas_clean = {}

        for key, value in texto_comidas_raw.items():
            if isinstance(value, str):
                texto_comidas_clean[key] = (
                    TextFormatterService.formatear_texto_comida_docx(value)
                )
            else:
                texto_comidas_clean[key] = value

        return {
            "informe": informe,
            "texto_comidas": texto_comidas_clean,
            "tipo": informe.tipo,
            "expediente_nro": informe.expediente_nro,
            "nombre_organizacion": informe.nombre_organizacion,
            "domicilio_organizacion": informe.domicilio_organizacion,
            "localidad_organizacion": informe.localidad_organizacion,
            "partido_organizacion": informe.partido_organizacion,
            "provincia_organizacion": informe.provincia_organizacion,
            "fecha_actual": informe.admision.creado.strftime("%d/%m/%Y"),
            "tipo_espacio": informe.tipo_espacio,
            "nombre_espacio": informe.nombre_espacio,
            "domicilio_espacio": informe.domicilio_espacio,
            "barrio_espacio": informe.barrio_espacio,
            "responsable_nombre": informe.responsable_tarjeta_nombre,
            "responsable_dni": informe.responsable_tarjeta_dni,
            "responsable_domicilio": informe.responsable_tarjeta_domicilio,
            "prestaciones": prestaciones,
            "total_desayunos": sum(p["desayuno"] for p in prestaciones),
            "total_almuerzos": sum(p["almuerzo"] for p in prestaciones),
            "total_meriendas": sum(p["merienda"] for p in prestaciones),
            "total_cenas": sum(p["cena"] for p in prestaciones),
            "conclusiones": getattr(informe, "conclusiones", ""),
        }

    @staticmethod
    def _generar_prestaciones_semanales(informe):
        return [
            {
                "dia": "Lunes",
                "desayuno": informe.solicitudes_desayuno_lunes,
                "almuerzo": informe.solicitudes_almuerzo_lunes,
                "merienda": informe.solicitudes_merienda_lunes,
                "cena": informe.solicitudes_cena_lunes,
            },
            {
                "dia": "Martes",
                "desayuno": informe.solicitudes_desayuno_martes,
                "almuerzo": informe.solicitudes_almuerzo_martes,
                "merienda": informe.solicitudes_merienda_martes,
                "cena": informe.solicitudes_cena_martes,
            },
            {
                "dia": "Miércoles",
                "desayuno": informe.solicitudes_desayuno_miercoles,
                "almuerzo": informe.solicitudes_almuerzo_miercoles,
                "merienda": informe.solicitudes_merienda_miercoles,
                "cena": informe.solicitudes_cena_miercoles,
            },
            {
                "dia": "Jueves",
                "desayuno": informe.solicitudes_desayuno_jueves,
                "almuerzo": informe.solicitudes_almuerzo_jueves,
                "merienda": informe.solicitudes_merienda_jueves,
                "cena": informe.solicitudes_cena_jueves,
            },
            {
                "dia": "Viernes",
                "desayuno": informe.solicitudes_desayuno_viernes,
                "almuerzo": informe.solicitudes_almuerzo_viernes,
                "merienda": informe.solicitudes_merienda_viernes,
                "cena": informe.solicitudes_cena_viernes,
            },
            {
                "dia": "Sábado",
                "desayuno": informe.solicitudes_desayuno_sabado,
                "almuerzo": informe.solicitudes_almuerzo_sabado,
                "merienda": informe.solicitudes_merienda_sabado,
                "cena": informe.solicitudes_cena_sabado,
            },
            {
                "dia": "Domingo",
                "desayuno": informe.solicitudes_desayuno_domingo,
                "almuerzo": informe.solicitudes_almuerzo_domingo,
                "merienda": informe.solicitudes_merienda_domingo,
                "cena": informe.solicitudes_cena_domingo,
            },
        ]


class TextFormatterService:

    NUMEROS_PALABRAS = {
        "1": "una",
        "2": "dos",
        "3": "tres",
        "4": "cuatro",
        "5": "cinco",
        "6": "seis",
        "7": "siete",
        "8": "ocho",
        "9": "nueve",
        "10": "diez",
        "11": "once",
        "12": "doce",
        "13": "trece",
        "14": "catorce",
        "15": "quince",
        "16": "dieciséis",
        "17": "diecisiete",
        "18": "dieciocho",
        "19": "diecinueve",
        "20": "veinte",
        "30": "treinta",
        "40": "cuarenta",
        "50": "cincuenta",
        "60": "sesenta",
        "70": "setenta",
        "80": "ochenta",
        "90": "noventa",
        "100": "cien",
    }

    @staticmethod
    def formatear_texto_comida_docx(texto_html):
        texto = strip_tags(texto_html)
        texto = texto.replace("&lt;", "").replace("&gt;", "")
        texto = texto.replace("&amp;", "y").replace("&quot;", "")

        if "No se solicitan" in texto:
            return texto.strip()

        patron = r"Por la cantidad de (\d+) (\w+) prestaciones, (\w+) (\d+) veces? por semana"
        matches = re.findall(patron, texto)

        oraciones_formateadas = []
        for match in matches:
            cantidad_num = match[0]
            veces_num = match[3]

            cantidad_palabra = TextFormatterService.NUMEROS_PALABRAS.get(
                cantidad_num, cantidad_num
            )
            veces_palabra = TextFormatterService.NUMEROS_PALABRAS.get(
                veces_num, veces_num
            )

            vez_veces = "vez" if veces_num == "1" else "veces"

            oracion_formateada = f"Por la cantidad de {cantidad_num} ({cantidad_palabra}) prestaciones, {veces_num} ({veces_palabra}) {vez_veces} por semana"
            oraciones_formateadas.append(oracion_formateada)

        if oraciones_formateadas:
            return ". ".join(oraciones_formateadas) + "."
        else:
            return re.sub(r"\s+", " ", texto).strip()

    @staticmethod
    def preparar_contexto_admision(admision):
        documentos = []
        archivos = ArchivoAdmision.objects.filter(admision=admision)
        for archivo in archivos:
            documentos.append(
                {
                    "nombre": (
                        archivo.documentacion.nombre
                        if archivo.documentacion
                        else archivo.nombre_personalizado
                    ),
                    "estado": archivo.estado,
                    "observaciones": archivo.observaciones,
                }
            )

        informe_tecnico = InformeTecnico.objects.filter(admision=admision).first()
        historial = admision.historial.all().order_by("-fecha")[:10]

        return {
            "admision": admision,
            "comedor": admision.comedor,
            "documentos": documentos,
            "informe_tecnico": informe_tecnico,
            "historial": historial,
            "fecha_actual": admision.creado.strftime("%d/%m/%Y"),
            "fecha_generacion": admision.creado.strftime("%d/%m/%Y %H:%M"),
        }

    @staticmethod
    def preparar_contexto_proyecto_convenio(admision):
        formulario = FormularioProyectoDeConvenio.objects.filter(
            admision=admision
        ).first()
        informe = InformeTecnico.objects.filter(admision=admision).first()

        return {
            "admision": admision,
            "comedor": admision.comedor,
            "formulario": formulario,
            "informe": informe,
            "fecha_actual": admision.creado.strftime("%d/%m/%Y"),
            "fecha_generacion": admision.creado.strftime("%d/%m/%Y %H:%M"),
        }

    @staticmethod
    def preparar_contexto_proyecto_disposicion(admision):
        formulario = FormularioProyectoDisposicion.objects.filter(
            admision=admision
        ).first()
        proyecto_convenio = FormularioProyectoDeConvenio.objects.filter(
            admision=admision
        ).first()
        informe = InformeTecnico.objects.filter(admision=admision).first()

        return {
            "admision": admision,
            "comedor": admision.comedor,
            "formulario": formulario,
            "proyecto_convenio": proyecto_convenio,
            "informe": informe,
            "fecha_actual": admision.creado.strftime("%d/%m/%Y"),
            "fecha_generacion": admision.creado.strftime("%d/%m/%Y %H:%M"),
        }
