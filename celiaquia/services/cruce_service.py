# celiaquia/services/cruce_service.py
"""
Breve descripción del cambio:
- Servicio para el cruce por CUIT/DNI que ejecuta el técnico:
  * Lee un Excel/CSV con encabezado 'cuit' o 'dni' (tolerante a variantes, mayúsculas/espacios).
  * Normaliza y compara contra la nómina del expediente (ExpedienteCiudadano/Ciudadano).
  * Marca cada legajo con cruce_ok=True/False y observacion_cruce.
  * Genera un PRD (PDF vía WeasyPrint a partir de template HTML; si falla, ReportLab; si no, CSV fallback)
    y lo guarda en Expediente.documento.
  * Cambia el estado del expediente: ASIGNADO -> PROCESO_DE_CRUCE -> CRUCE_FINALIZADO.
"""

import logging
import io
import csv
import re
from io import BytesIO
from datetime import datetime

import pandas as pd
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.text import slugify
from django.template.loader import render_to_string

# WeasyPrint opcional
try:
    from weasyprint import HTML as WPHTML  # type: ignore
    _WEASY_OK = True
except Exception:
    _WEASY_OK = False

from celiaquia.models import (
    Expediente,
    ExpedienteCiudadano,
    EstadoExpediente,
)

logger = logging.getLogger(__name__)

# Columnas candidatas alternativas a "cuit" y "dni"
CUIT_COL_CANDIDATAS = {
    "cuit", "c.u.i.t", "nro_cuit", "numero_cuit", "número_cuit", "cuit_nro", "cuit número"
}
DNI_COL_CANDIDATAS = {
    "dni", "documento", "nro_dni", "numero_dni", "número_dni", "doc", "nro_doc", "num_doc"
}


class CruceService:
    # ---------------------------
    # Utilidades de lectura/normalización
    # ---------------------------

    @staticmethod
    def _normalize_cuit_str(val) -> str:
        if val is None:
            return ""
        s = str(val).strip()
        digits = re.sub(r"\D", "", s)
        return digits

    @staticmethod
    def _normalize_dni_str(val) -> str:
        if val is None:
            return ""
        s = re.sub(r"\D", "", str(val).strip())
        return s.lstrip("0")

    @staticmethod
    def _extraer_dni_de_cuit(cuit: str) -> str:
        if len(cuit) == 11:
            return cuit[2:10]
        return ""

    @staticmethod
    def _resolver_cuit_ciudadano(ciudadano) -> str:
        for attr in ("cuit", "cuil", "cuil_cuit"):
            if hasattr(ciudadano, attr):
                val = getattr(ciudadano, attr) or ""
                val = CruceService._normalize_cuit_str(val)
                if len(val) == 11:
                    return val
        return ""

    # --- FIX de robustez: leer bytes de múltiples tipos (UploadedFile, FieldFile, file-like, path str) ---
    @staticmethod
    def _read_file_bytes(archivo_fileobj) -> bytes:
        # Ya son bytes
        if isinstance(archivo_fileobj, (bytes, bytearray, memoryview)):
            return bytes(archivo_fileobj)

        # Si es ruta str -> abrir en binario
        if isinstance(archivo_fileobj, str):
            with open(archivo_fileobj, "rb") as f:
                return f.read()

        # Si es un objeto de Django File/FieldFile/UploadedFile o file-like
        # Intentar open/read
        try:
            archivo_fileobj.open()
        except Exception:
            pass
        try:
            raw = archivo_fileobj.read()
        finally:
            try:
                archivo_fileobj.seek(0)
            except Exception:
                pass

        # Si por alguna razón devolvió str (raro en binarios), lo convertimos a bytes
        if isinstance(raw, str):
            # Excel/CSV binarios deberían ser bytes; si llegó str, encode como utf-8
            raw = raw.encode("utf-8")

        return raw

    @staticmethod
    def _leer_tabla(archivo_fileobj) -> pd.DataFrame:
        """
        Lee XLSX/XLS/CSV en un DataFrame y normaliza encabezados.
        """
        raw = CruceService._read_file_bytes(archivo_fileobj)
        bio = io.BytesIO(raw)

        # 1) Intento como Excel
        try:
            df = pd.read_excel(bio, dtype=str)  # hoja por defecto
        except Exception:
            # 2) Reintento como CSV (coma)
            bio.seek(0)
            try:
                df = pd.read_csv(bio, dtype=str)
            except Exception:
                # 3) Reintento como CSV (punto y coma)
                bio.seek(0)
                try:
                    df = pd.read_csv(bio, dtype=str, sep=";")
                except Exception:
                    raise ValidationError("No se pudo leer el archivo. Formato no soportado (XLSX/XLS/CSV).")

        # Encabezados normalizados
        df.columns = [str(c).strip().lower().replace("  ", " ").replace(" ", "_") for c in df.columns]
        return df

    @staticmethod
    def _col_por_preferencias(df: pd.DataFrame, candidatas: set, palabra_clave: str) -> str | None:
        cols = set(df.columns)
        for cand in candidatas:
            if cand in cols:
                return cand
        for c in df.columns:
            if palabra_clave in c:
                return c
        return None

    @staticmethod
    def _leer_identificadores(archivo_excel) -> dict:
        """
        Devuelve {"cuits": set(...), "dnis": set(...)} a partir de XLSX/XLS/CSV.
        Acepta columna 'cuit' y/o 'dni'. Si en 'cuit' vienen DNIs (8 dígitos), se tratan como DNI.
        """
        df = CruceService._leer_tabla(archivo_excel)

        col_cuit = CruceService._col_por_preferencias(df, CUIT_COL_CANDIDATAS, "cuit")
        col_dni = CruceService._col_por_preferencias(df, DNI_COL_CANDIDATAS, "dni")

        cuits = set()
        dnis = set()

        if col_cuit:
            for raw in df[col_cuit].fillna(""):
                norm = CruceService._normalize_cuit_str(raw)
                if not norm:
                    continue
                if len(norm) == 11:
                    cuits.add(norm)
                    dni = CruceService._extraer_dni_de_cuit(norm)
                    if dni:
                        dnis.add(CruceService._normalize_dni_str(dni))
                else:
                    # muchas veces mandan DNI en columna "cuit"
                    dnis.add(CruceService._normalize_dni_str(norm))

        if col_dni:
            for raw in df[col_dni].fillna(""):
                dni = CruceService._normalize_dni_str(raw)
                if dni:
                    dnis.add(dni)

        if not cuits and not dnis:
            if not col_cuit and not col_dni:
                raise ValidationError("El archivo debe tener columna 'cuit' o 'dni'.")
            raise ValidationError("El archivo no contiene identificadores (CUIT/DNI) válidos.")

        return {"cuits": cuits, "dnis": dnis}

    # ---------------------------
    # Generación de PRD (PDF / CSV)
    # ---------------------------

    @staticmethod
    def _generar_prd_pdf_html(expediente: Expediente, resumen: dict) -> bytes:
        """
        Genera PDF con WeasyPrint a partir del template 'celiaquia/pdf_prd_cruce.html'.
        """
        # enriquecer contexto con porcentajes y técnico asignado
        total_legajos = int(resumen.get("total_legajos", 0) or 0)
        matcheados = int(resumen.get("matcheados", 0) or 0)
        no_matcheados = int(resumen.get("no_matcheados", 0) or 0)

        pct_match = (matcheados * 100.0 / total_legajos) if total_legajos else 0.0
        pct_no_match = (no_matcheados * 100.0 / total_legajos) if total_legajos else 0.0

        resumen_html = dict(resumen)
        resumen_html["pct_matcheados"] = pct_match
        resumen_html["pct_no_matcheados"] = pct_no_match

        tecnico_txt = None
        try:
            asig = getattr(expediente, "asignacion_tecnico", None)
            if asig and asig.tecnico:
                tecnico_txt = asig.tecnico.get_full_name() or asig.tecnico.username
        except Exception:
            tecnico_txt = None

        context = {
            "expediente": expediente,
            "tecnico": tecnico_txt,
            "resumen": resumen_html,
            "ahora": datetime.now().strftime("%d/%m/%Y %H:%M"),
        }

        html_string = render_to_string("celiaquia/pdf_prd_cruce.html", context)
        return WPHTML(string=html_string).write_pdf()

    @staticmethod
    def _generar_prd_pdf_reportlab(expediente: Expediente, resumen: dict) -> bytes:
        """
        Fallback en caso de no contar con WeasyPrint. Diseño sencillo con ReportLab.
        """
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        margin_x = 50
        y = height - 50

        def ensure_space(min_y=60):
            nonlocal y
            if y < min_y:
                c.showPage()
                y = height - 50

        # Encabezado
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin_x, y, "PRD - Resultado de Cruce por CUIT/DNI")
        y -= 20

        c.setFont("Helvetica", 10)
        c.drawString(margin_x, y, f"Expediente: {expediente.codigo}")
        y -= 15

        tecnico_txt = None
        try:
            asig = getattr(expediente, "asignacion_tecnico", None)
            if asig and asig.tecnico:
                tecnico_txt = asig.tecnico.get_full_name() or asig.tecnico.username
        except Exception:
            tecnico_txt = None
        if tecnico_txt:
            c.drawString(margin_x, y, f"Técnico asignado: {tecnico_txt}")
            y -= 15

        c.drawString(margin_x, y, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        y -= 25

        total_legajos = int(resumen.get("total_legajos", 0) or 0)
        matcheados = int(resumen.get("matcheados", 0) or 0)
        no_matcheados = int(resumen.get("no_matcheados", 0) or 0)
        total_cuits = int(resumen.get("total_cuits_archivo", 0) or 0)
        total_dnis = int(resumen.get("total_dnis_archivo", 0) or 0)

        pct_match = (matcheados * 100.0 / total_legajos) if total_legajos else 0.0
        pct_no_match = (no_matcheados * 100.0 / total_legajos) if total_legajos else 0.0

        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin_x, y, "Resumen:")
        y -= 18

        c.setFont("Helvetica", 10)
        items = [
            ("Total legajos", total_legajos),
            ("Total CUITs (archivo)", total_cuits),
            ("Total DNIs (archivo)", total_dnis),
            (f"Matcheados ({pct_match:.1f}%)", matcheados),
            (f"No matcheados ({pct_no_match:.1f}%)", no_matcheados),
        ]
        for label, value in items:
            ensure_space()
            c.drawString(margin_x + 10, y, f"- {label}: {value}")
            y -= 14

        y -= 10
        ensure_space()

        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin_x, y, "Detalle no matcheados (primeros 30):")
        y -= 18
        c.setFont("Helvetica", 9)

        detalle = resumen.get("detalle_no_match", []) or []
        for i, fila in enumerate(detalle[:30], start=1):
            ensure_space()
            c.drawString(margin_x + 10, y, f"{i}. {fila}")
            y -= 12

        c.showPage()
        c.save()
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    @staticmethod
    def _generar_prd_pdf(expediente: Expediente, resumen: dict) -> bytes:
        """
        Intenta WeasyPrint + template; si falla o no está, cae a ReportLab; si eso falla, CSV en caller.
        """
        if _WEASY_OK:
            try:
                return CruceService._generar_prd_pdf_html(expediente, resumen)
            except Exception as e:
                logger.warning("WeasyPrint falló; se usa ReportLab. Detalle: %s", e)
        # Fallback ReportLab
        return CruceService._generar_prd_pdf_reportlab(expediente, resumen)

    @staticmethod
    def _generar_prd_csv(expediente: Expediente, resumen: dict) -> bytes:
        buffer = BytesIO()
        writer = csv.writer(buffer)
        writer.writerow(["PRD - Resultado de Cruce por CUIT/DNI"])
        writer.writerow(["Expediente", expediente.codigo])
        writer.writerow(["Fecha", datetime.now().strftime("%d/%m/%Y %H:%M")])
        writer.writerow([])
        writer.writerow(["Resumen"])
        writer.writerow(["total_legajos", resumen.get("total_legajos", 0)])
        writer.writerow(["total_cuits_archivo", resumen.get("total_cuits_archivo", 0)])
        writer.writerow(["total_dnis_archivo", resumen.get("total_dnis_archivo", 0)])
        writer.writerow(["matcheados", resumen.get("matcheados", 0)])
        writer.writerow(["no_matcheados", resumen.get("no_matcheados", 0)])
        writer.writerow([])
        writer.writerow(["Detalle_no_matcheados"])
        for fila in resumen.get("detalle_no_match", []):
            writer.writerow([fila])
        return buffer.getvalue()

    # ---------------------------
    # Pipeline principal
    # ---------------------------

    @staticmethod
    @transaction.atomic
    def procesar_cruce_por_cuit(expediente: Expediente, archivo_excel, usuario) -> dict:
        """
        Guarda el Excel/CSV, cruza CUITs/DNIs contra la nómina y genera un PRD en el expediente.
        Cambia estados: ASIGNADO -> PROCESO_DE_CRUCE -> CRUCE_FINALIZADO.
        """
        if not expediente:
            raise ValidationError("Expediente inválido.")

        # Validación de estado actual (permite reprocesar si ya estaba finalizado)
        estado_actual = expediente.estado.nombre
        estados_permitidos = ("ASIGNADO", "PROCESO_DE_CRUCE", "CRUCE_FINALIZADO")
        if estado_actual not in estados_permitidos:
            raise ValidationError("El expediente no está en un estado válido para realizar el cruce.")


        # 1) Guardar el archivo de cruce en el expediente
        expediente.cruce_excel = archivo_excel
        expediente.usuario_modificador = usuario

        estado_proc, _ = EstadoExpediente.objects.get_or_create(nombre="PROCESO_DE_CRUCE")
        expediente.estado = estado_proc
        expediente.save(update_fields=["cruce_excel", "usuario_modificador", "estado"])

        # 2) Leer identificadores (robusto XLSX/XLS/CSV)
        ids_archivo = CruceService._leer_identificadores(expediente.cruce_excel)
        set_cuits = ids_archivo["cuits"]
        set_dnis_norm = ids_archivo["dnis"]

        # 3) Cruce sobre legajos
        legajos = (
            ExpedienteCiudadano.objects
            .select_related("ciudadano")
            .filter(expediente=expediente)
        )

        total_legajos = legajos.count()
        matcheados = 0
        no_matcheados = 0
        detalle_no_match = []
        detalle_match = []  

        for leg in legajos:
            ciudadano = leg.ciudadano

            cuit_ciud = CruceService._resolver_cuit_ciudadano(ciudadano)  # 11 dígitos o ''
            dni_ciud = CruceService._normalize_dni_str(getattr(ciudadano, "documento", ""))

            match = False
            motivo = None
            by = None  # 'CUIT' o 'DNI'

            # 1) match por CUIT exacto
            if cuit_ciud and cuit_ciud in set_cuits:
                match = True
                by = "CUIT"
            # 2) match por DNI (normalizado)
            elif dni_ciud and dni_ciud in set_dnis_norm:
                match = True
                by = "DNI"
            else:
                match = False
                motivo = "No coincide por CUIT ni por DNI."

            # Persistir resultado en el legajo
            leg.cruce_ok = True if match else False
            leg.observacion_cruce = None if match else motivo
            leg.save(update_fields=["cruce_ok", "observacion_cruce", "modificado_en"])

            if match:
                matcheados += 1
                # etiqueta amigable para el detalle de OK
                etiqueta_ok = f"DNI:{getattr(ciudadano,'documento','')}"
                if cuit_ciud:
                    etiqueta_ok += f" / CUIT:{cuit_ciud}"
                detalle_match.append(etiqueta_ok)

                # opcional: contadores por tipo
                if by == "CUIT":
                    matcheados_por_cuit += 1
            else:
                no_matcheados += 1
                etiqueta_bad = f"DNI:{getattr(ciudadano, 'documento', '')}"
                if cuit_ciud:
                    etiqueta_bad += f" / CUIT esperado:{cuit_ciud}"
                detalle_no_match.append(etiqueta_bad)

        resumen = {
            "total_legajos": total_legajos,
            "total_cuits_archivo": len(set_cuits),
            "total_dnis_archivo": len(set_dnis_norm),
            "matcheados": matcheados,
            "no_matcheados": no_matcheados,
            "detalle_match": detalle_match,          # <= NUEVO
            "detalle_no_match": detalle_no_match,            
        }

        # 5) Generar PRD y adjuntar a expediente (WeasyPrint -> ReportLab -> CSV)
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
