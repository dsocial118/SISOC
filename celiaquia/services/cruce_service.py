# celiaquia/services/cruce_service.py
"""
Breve descripción del cambio:
- Servicio para el cruce por CUIT/DNI que ejecuta el técnico:
  * Lee un Excel/CSV con encabezado 'cuit' o 'dni' (tolerante a variantes, mayúsculas/espacios).
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
        """
        Devuelve sólo dígitos de un CUIT. Si no es interpretable, devuelve ''.
        """
        if val is None:
            return ""
        s = str(val).strip()
        digits = re.sub(r"\D", "", s)
        return digits

    @staticmethod
    def _normalize_dni_str(val) -> str:
        """
        Devuelve sólo dígitos del DNI, sin ceros a la izquierda (para comparar robusto).
        """
        if val is None:
            return ""
        s = re.sub(r"\D", "", str(val).strip())
        return s.lstrip("0")

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
    def _leer_tabla(archivo_fileobj) -> pd.DataFrame:
        """
        Lee XLSX/XLS/CSV en un DataFrame y normaliza encabezados.
        Acepta:
          - UploadedFile / FieldFile de Django
          - File-like object
        """
        # Obtenemos los bytes
        try:
            archivo_fileobj.open()
        except Exception:
            pass  # puede ya estar abierto

        try:
            raw = archivo_fileobj.read()
        finally:
            try:
                archivo_fileobj.seek(0)
            except Exception:
                pass

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

        # Normalizamos encabezados a minúsculas, sin espacios extra y con '_' para espacios
        df.columns = [str(c).strip().lower().replace("  ", " ").replace(" ", "_") for c in df.columns]
        return df

    @staticmethod
    def _col_por_preferencias(df: pd.DataFrame, candidatas: set, palabra_clave: str) -> str | None:
        """
        Devuelve el nombre de columna si existe una candidata exacta, o cualquier columna
        que contenga la palabra_clave.
        """
        cols = set(df.columns)
        # match exacto
        for cand in candidatas:
            if cand in cols:
                return cand
        # heurística: cualquier columna que contenga la palabra clave
        for c in df.columns:
            if palabra_clave in c:
                return c
        return None

    @staticmethod
    def _leer_identificadores(archivo_excel) -> dict:
        """
        Lee el archivo (Excel/CSV) y devuelve:
          {
            "cuits": set(...)  # 11 dígitos
            "dnis":  set(...)  # DNI normalizados (sin ceros a la izquierda)
          }
        Acepta columna 'cuit' o 'dni' (encabezados normalizados) y variantes comunes.
        Si la columna 'cuit' trae valores de 8 dígitos, se interpretan como DNIs.
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
                    # también agregamos el DNI derivado del CUIT
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
            # Mensaje claro si no detectamos ninguna de las dos columnas útiles
            if not col_cuit and not col_dni:
                raise ValidationError("El archivo debe tener columna 'cuit' o 'dni'.")
            raise ValidationError("El archivo no contiene identificadores (CUIT/DNI) válidos.")

        return {"cuits": cuits, "dnis": dnis}

    # ---------------------------
    # Generación de PRD (PDF / CSV)
    # ---------------------------

    @staticmethod
    def _generar_prd_pdf(expediente: Expediente, resumen: dict) -> bytes:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        margin_x = 50
        y = height - 50

        def line(txt, font="Helvetica", size=10, dy=15):
            nonlocal y
            c.setFont(font, size)
            c.drawString(margin_x, y, txt)
            y -= dy

        def ensure_space(min_y=60):
            nonlocal y
            if y < min_y:
                c.showPage()
                y = height - 50

        # --------- Encabezado ---------
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin_x, y, "PRD - Resultado de Cruce por CUIT/DNI")
        y -= 20

        c.setFont("Helvetica", 10)
        c.drawString(margin_x, y, f"Expediente: {expediente.codigo}")
        y -= 15

        # Técnico asignado (si existe atributo/relación)
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

        # --------- Resumen con porcentajes ---------
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

        items = [
            ("Total legajos", total_legajos),
            ("Total CUITs (archivo)", total_cuits),
            ("Total DNIs (archivo)", total_dnis),
            (f"Matcheados ({pct_match:.1f}%)", matcheados),
            (f"No matcheados ({pct_no_match:.1f}%)", no_matcheados),
        ]

        # (Opcional) Desglose si viene en el resumen
        if "matcheados_por_cuit" in resumen or "matcheados_por_dni" in resumen:
            por_cuit = int(resumen.get("matcheados_por_cuit", 0) or 0)
            por_dni = int(resumen.get("matcheados_por_dni", 0) or 0)
            items.append((" - por CUIT", por_cuit))
            items.append((" - por DNI", por_dni))

        c.setFont("Helvetica", 10)
        for label, value in items:
            ensure_space()
            c.drawString(margin_x + 10, y, f"- {label}: {value}")
            y -= 14

        y -= 10
        ensure_space()

        # --------- Detalle de no matcheados ---------
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
    def _generar_prd_csv(expediente: Expediente, resumen: dict) -> bytes:
        """
        Fallback cuando no hay reportlab. Genera un CSV con el resumen.
        """
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

        Devuelve dict con totales y métricas del cruce.
        """
        if not expediente:
            raise ValidationError("Expediente inválido.")

        # Validación de estado actual
        estado_actual = expediente.estado.nombre
        if estado_actual not in ("ASIGNADO", "PROCESO_DE_CRUCE"):
            raise ValidationError("El expediente no está en un estado válido para realizar el cruce.")

        # 1) Guardar el archivo de cruce en el expediente
        expediente.cruce_excel = archivo_excel
        expediente.usuario_modificador = usuario

        estado_proc, _ = EstadoExpediente.objects.get_or_create(nombre="PROCESO_DE_CRUCE")
        expediente.estado = estado_proc
        expediente.save(update_fields=["cruce_excel", "usuario_modificador", "estado"])

        # 2) Leer identificadores desde el archivo (tolerante: XLSX/XLS/CSV + variantes de encabezado)
        ids_archivo = CruceService._leer_identificadores(expediente.cruce_excel)
        set_cuits = ids_archivo["cuits"]            # 11 dígitos
        set_dnis_norm = ids_archivo["dnis"]         # sin ceros a la izquierda

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

        for leg in legajos:
            ciudadano = leg.ciudadano

            # CUIT del ciudadano (si el modelo lo tuviera)
            cuit_ciud = CruceService._resolver_cuit_ciudadano(ciudadano)  # 11 dígitos o ''
            # DNI del ciudadano normalizado
            dni_ciud = CruceService._normalize_dni_str(getattr(ciudadano, "documento", ""))

            match = False
            motivo = None

            # 1) match por CUIT exacto
            if cuit_ciud and cuit_ciud in set_cuits:
                match = True
            # 2) match por DNI (normalizado)
            elif dni_ciud and dni_ciud in set_dnis_norm:
                match = True
            else:
                match = False
                motivo = "No coincide por CUIT ni por DNI."

            # Guardamos resultado del cruce en el legajo
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
            "total_dnis_archivo": len(set_dnis_norm),
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
