# celiaquia/services/cruce_service.py
"""
Breve descripción del cambio:
- Servicio para el cruce por CUIT que ejecuta el técnico:
  * Lee un Excel con encabezado 'cuit' (sin guiones).
  * Normaliza y compara contra la nómina del expediente (ExpedienteCiudadano/Ciudadano).
  * Marca cada legajo con cruce_ok=True/False y observacion_cruce.
  * Genera un PRD (PDF si hay reportlab; si no, CSV fallback) y lo guarda en Expediente.documento.
  * Cambia el estado del expediente: ASIGNADO -> PROCESO_DE_CRUCE -> CRUCE_FINALIZADO.

Estados y flujos impactados:
- Flujo técnico: al subir + procesar, se actualizan legajos y el expediente queda con PRD adjunto.

Dependencias con otros archivos:
- celiaquia/models.py (campos: Expediente.cruce_excel, Expediente.documento, ExpedienteCiudadano.cruce_ok/observacion_cruce)
- Puede ser invocado desde views/expediente.py (endpoints de upload/procesamiento).
"""

import logging
from io import BytesIO
from datetime import datetime

import pandas as pd
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.text import slugify

from celiaquia.models import (
    Expediente,
    ExpedienteCiudadano,
    EstadoExpediente,
)

logger = logging.getLogger(__name__)


class CruceService:
    @staticmethod
    def _normalize_cuit_str(val) -> str:
        """
        Devuelve sólo dígitos de un CUIT. Si no es interpretable, devuelve ''.
        """
        if val is None:
            return ""
        s = str(val).strip()
        digits = "".join(ch for ch in s if ch.isdigit())
        return digits

    @staticmethod
    def _extraer_dni_de_cuit(cuit: str) -> str:
        """
        Dado un CUIT (11 dígitos), devuelve el DNI (8 dígitos centrales).
        Si no cumple longitud 11, devuelve ''.
        """
        if len(cuit) == 11:
            return cuit[2:10]
        return ""

    @staticmethod
    def _resolver_cuit_ciudadano(ciudadano) -> str:
        """
        Intenta obtener un CUIT explícito de la entidad Ciudadano.
        Busca atributos comunes: 'cuit', 'cuil', 'cuil_cuit'.
        Devuelve solo dígitos si lo encuentra; si no, ''.
        """
        for attr in ("cuit", "cuil", "cuil_cuit"):
            if hasattr(ciudadano, attr):
                val = getattr(ciudadano, attr) or ""
                val = CruceService._normalize_cuit_str(val)
                if len(val) == 11:
                    return val
        return ""

    @staticmethod
    def _leer_excel_cuits(archivo_excel) -> list[str]:
        """
        Lee el archivo Excel (File o FieldFile) y devuelve lista de CUITs normalizados (11 dígitos).
        Valida existencia de encabezado 'cuit'.
        """
        archivo_excel.open()
        archivo_excel.seek(0)
        data = archivo_excel.read()
        try:
            df = pd.read_excel(BytesIO(data), engine="openpyxl")
        except Exception as e:
            raise ValidationError(f"No se pudo leer el Excel del cruce: {e}")

        # normalizar encabezados
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
        if "cuit" not in df.columns:
            raise ValidationError("El Excel del cruce debe tener una columna 'cuit' con encabezado.")

        # normalizar cuits
        cuits = []
        for raw in df["cuit"].fillna("").tolist():
            norm = CruceService._normalize_cuit_str(raw)
            if norm:
                cuits.append(norm)

        if not cuits:
            raise ValidationError("El Excel no contiene CUITs válidos.")

        return cuits

    @staticmethod
    def _generar_prd_pdf(expediente: Expediente, resumen: dict) -> bytes:
        """
        Genera un PDF simple con el resumen del cruce.
        Requiere reportlab. Si no está disponible, lanzará ImportError y el caller hará fallback.
        """
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 50

        # Título
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "PRD - Resultado de Cruce por CUIT")
        y -= 20

        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Expediente: {expediente.codigo}")
        y -= 15
        c.drawString(50, y, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        y -= 25

        # Resumen
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Resumen:")
        y -= 18
        c.setFont("Helvetica", 10)
        for k in ("total_legajos", "total_cuits_archivo", "matcheados", "no_matcheados"):
            c.drawString(60, y, f"- {k.replace('_',' ').capitalize()}: {resumen.get(k, 0)}")
            y -= 14

        y -= 10
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Detalle no matcheados (primeros 30):")
        y -= 18
        c.setFont("Helvetica", 9)

        # Listado simple
        for i, fila in enumerate(resumen.get("detalle_no_match", [])[:30], start=1):
            text = f"{i}. {fila}"
            if y < 60:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 9)
            c.drawString(60, y, text)
            y -= 12

        c.showPage()
        c.save()
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    @staticmethod
    def _generar_prd_csv(expediente: Expediente, resumen: dict) -> bytes:
        """
        Fallback cuando no hay reportlab. Genera un CSV con el resumen.
        """
        import csv

        buffer = BytesIO()
        writer = csv.writer(buffer)
        writer.writerow(["PRD - Resultado de Cruce por CUIT"])
        writer.writerow(["Expediente", expediente.codigo])
        writer.writerow(["Fecha", datetime.now().strftime("%d/%m/%Y %H:%M")])
        writer.writerow([])
        writer.writerow(["Resumen"])
        writer.writerow(["total_legajos", resumen.get("total_legajos", 0)])
        writer.writerow(["total_cuits_archivo", resumen.get("total_cuits_archivo", 0)])
        writer.writerow(["matcheados", resumen.get("matcheados", 0)])
        writer.writerow(["no_matcheados", resumen.get("no_matcheados", 0)])
        writer.writerow([])
        writer.writerow(["Detalle_no_matcheados"])
        for fila in resumen.get("detalle_no_match", []):
            writer.writerow([fila])

        return buffer.getvalue()

    @staticmethod
    @transaction.atomic
    def procesar_cruce_por_cuit(expediente: Expediente, archivo_excel, usuario) -> dict:
        """
        Guarda el Excel, cruza CUITs contra la nómina y genera un PRD en el expediente.
        Cambia estados: ASIGNADO -> PROCESO_DE_CRUCE -> CRUCE_FINALIZADO.

        Devuelve dict con totales y métricas del cruce.
        """
        if not expediente:
            raise ValidationError("Expediente inválido.")

        # Validación de estado actual
        estado_actual = expediente.estado.nombre
        if estado_actual not in ("ASIGNADO", "PROCESO_DE_CRUCE"):
            raise ValidationError("El expediente no está en un estado válido para realizar el cruce.")

        # 1) Guardar el Excel de cruce en el expediente
        expediente.cruce_excel = archivo_excel
        expediente.usuario_modificador = usuario

        estado_proc, _ = EstadoExpediente.objects.get_or_create(nombre="PROCESO_DE_CRUCE")
        expediente.estado = estado_proc
        expediente.save(update_fields=["cruce_excel", "usuario_modificador", "estado"])

        # 2) Leer CUITs desde el Excel
        cuits_archivo = CruceService._leer_excel_cuits(expediente.cruce_excel)
        set_cuits = set(cuits_archivo)

        # 3) Iterar legajos y resolver match
        legajos = (
            ExpedienteCiudadano.objects
            .select_related("ciudadano")
            .filter(expediente=expediente)
        )

        total_legajos = legajos.count()
        matcheados = 0
        no_matcheados = 0
        detalle_no_match = []

        # Preconstruimos map por DNI (los 8 del medio del CUIT)
        cuits_por_dni = {}
        for c in set_cuits:
            dni = CruceService._extraer_dni_de_cuit(c)
            if dni:
                cuits_por_dni.setdefault(dni, set()).add(c)

        # Procesamiento
        for leg in legajos:
            ciudadano = leg.ciudadano

            # 3.a) Intentar CUIT del ciudadano (atributos comunes)
            cuit_ciud = CruceService._resolver_cuit_ciudadano(ciudadano)

            match = False
            motivo = None

            if cuit_ciud and cuit_ciud in set_cuits:
                match = True
            else:
                # 3.b) Fallback por DNI medio en CUIT
                dni_ciud = str(getattr(ciudadano, "documento", "") or "").strip()
                if dni_ciud and dni_ciud in cuits_por_dni:
                    match = True
                else:
                    match = False
                    motivo = "CUIT no coincide con la nómina (por CUIT directo ni por DNI)."

            # Guardamos resultado
            leg.cruce_ok = True if match else False
            leg.observacion_cruce = None if match else motivo
            leg.save(update_fields=["cruce_ok", "observacion_cruce", "modificado_en"])

            if match:
                matcheados += 1
            else:
                no_matcheados += 1
                etiqueta = f"DNI:{getattr(ciudadano, 'documento', '')}"
                if cuit_ciud:
                    etiqueta += f" / CUIT esperado:{cuit_ciud}"
                detalle_no_match.append(etiqueta)

        # 4) Resumen
        resumen = {
            "total_legajos": total_legajos,
            "total_cuits_archivo": len(set_cuits),
            "matcheados": matcheados,
            "no_matcheados": no_matcheados,
            "detalle_no_match": detalle_no_match,
        }

        # 5) Generar PRD y adjuntar a expediente
        nombre_base = slugify(f"{expediente.codigo}-prd-cruce-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        try:
            pdf_bytes = CruceService._generar_prd_pdf(expediente, resumen)
            expediente.documento.save(f"{nombre_base}.pdf", ContentFile(pdf_bytes), save=False)
        except Exception as e:
            logger.warning("No fue posible generar PDF (se usará CSV fallback): %s", e)
            csv_bytes = CruceService._generar_prd_csv(expediente, resumen)
            expediente.documento.save(f"{nombre_base}.csv", ContentFile(csv_bytes), save=False)

        # 6) Estado final
        estado_final, _ = EstadoExpediente.objects.get_or_create(nombre="CRUCE_FINALIZADO")
        expediente.estado = estado_final
        expediente.usuario_modificador = usuario
        expediente.save(update_fields=["documento", "estado", "usuario_modificador"])

        logger.info(
            "Cruce finalizado para expediente %s: %s matcheados / %s no matcheados.",
            expediente.codigo, matcheados, no_matcheados
        )
        return resumen
