import csv
import io
import logging
import re
from datetime import datetime
from io import BytesIO

import pandas as pd
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.template.loader import render_to_string
from django.utils.text import slugify

try:
    from weasyprint import HTML as WPHTML  # type: ignore
    _WEASY_OK = True
except Exception:
    _WEASY_OK = False

from celiaquia.models import (
    EstadoExpediente,
    Expediente,
    ExpedienteCiudadano,
)
from celiaquia.services.cupo_service import (
    CupoService,
    CupoNoConfigurado,
)

logger = logging.getLogger(__name__)

CUIT_COL_CANDIDATAS = {
    "cuit",
    "c.u.i.t",
    "nro_cuit",
    "numero_cuit",
    "número_cuit",
    "cuit_nro",
    "cuit número",
}
DNI_COL_CANDIDATAS = {
    "dni",
    "documento",
    "nro_dni",
    "numero_dni",
    "número_dni",
    "doc",
    "nro_doc",
    "num_doc",
}


class CruceService:
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

    @staticmethod
    def _read_file_bytes(archivo_fileobj) -> bytes:
        if isinstance(archivo_fileobj, (bytes, bytearray, memoryview)):
            return bytes(archivo_fileobj)
        if isinstance(archivo_fileobj, str):
            with open(archivo_fileobj, "rb") as f:
                return f.read()
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
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        return raw

    @staticmethod
    def _leer_tabla(archivo_fileobj) -> pd.DataFrame:
        raw = CruceService._read_file_bytes(archivo_fileobj)
        bio = io.BytesIO(raw)
        try:
            df = pd.read_excel(bio, dtype=str)
        except Exception:
            bio.seek(0)
            try:
                df = pd.read_csv(bio, dtype=str)
            except Exception:
                bio.seek(0)
                try:
                    df = pd.read_csv(bio, dtype=str, sep=";")
                except Exception:
                    raise ValidationError(
                        "No se pudo leer el archivo. Formato no soportado (XLSX/XLS/CSV)."
                    )
        df.columns = [
            str(c).strip().lower().replace("  ", " ").replace(" ", "_") for c in df.columns
        ]
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

    @staticmethod
    def _generar_prd_pdf_html(expediente: Expediente, resumen: dict) -> bytes:
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

        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin_x, y, "PRD - Resultado de Cruce por CUIT/DNI")
        y -= 20

        c.setFont("Helvetica", 10)
        c.drawString(margin_x, y, f"Expediente: ")
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

        cupo_total = resumen.get("cupo_total")
        cupo_usados = resumen.get("cupo_usados")
        cupo_disponibles = resumen.get("cupo_disponibles")
        fuera_cupo = resumen.get("fuera_cupo")
        if (cupo_total is None or cupo_usados is None or cupo_disponibles is None) and resumen.get("cupo"):
            cupo_total = resumen["cupo"].get("total_asignado")
            cupo_usados = resumen["cupo"].get("usados")
            cupo_disponibles = resumen["cupo"].get("disponibles")
        if fuera_cupo is None:
            fuera_cupo = resumen.get("cupo_fuera_count")

        pct_match = (matcheados * 100.0 / total_legajos) if total_legajos else 0.0
        pct_no_match = (no_matcheados * 100.0 / total_legajos) if total_legajos else 0.0

        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin_x, y, "Resumen:")
        y -= 18

        c.setFont("Helvetica", 10)
        for label, value in [
            ("Total legajos (aprobados)", total_legajos),
            ("Total CUITs (archivo)", total_cuits),
            ("Total DNIs (archivo)", total_dnis),
            (f"Matcheados ({pct_match:.1f}%)", matcheados),
            (f"No matcheados ({pct_no_match:.1f}%)", no_matcheados),
        ]:
            ensure_space()
            c.drawString(margin_x + 10, y, f"- {label}: {value}")
            y -= 14

        if cupo_total is not None:
            ensure_space()
            c.setFont("Helvetica-Bold", 12)
            c.drawString(margin_x, y, "Cupo:")
            y -= 16
            c.setFont("Helvetica", 10)
            for label, value in [
                ("Total asignado", cupo_total),
                ("Usados", cupo_usados),
                ("Disponibles", cupo_disponibles),
                ("Fuera de cupo (lista de espera)", int(fuera_cupo or 0)),
            ]:
                ensure_space()
                c.drawString(margin_x + 10, y, f"- {label}: {value}")
                y -= 14

        detalle_ok = resumen.get("detalle_match", []) or []
        ensure_space(90)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin_x, y, "Detalle de aprobados:")
        y -= 16

        c.setFont("Helvetica", 9)
        if not detalle_ok:
            c.drawString(margin_x + 10, y, "— Sin registros —")
            y -= 12
        else:
            c.drawString(margin_x + 10, y, "#")
            c.drawString(margin_x + 30, y, "DNI")
            c.drawString(margin_x + 120, y, "CUIT")
            c.drawString(margin_x + 220, y, "Nombre")
            c.drawString(margin_x + 340, y, "Apellido")
            c.drawString(margin_x + 460, y, "Por")
            y -= 12

            for i, fila in enumerate(detalle_ok, start=1):
                ensure_space()
                dni = str(fila.get("dni") or "")
                cuit = str(fila.get("cuit") or "")
                nom = str(fila.get("nombre") or "")
                ape = str(fila.get("apellido") or "")
                por = str(fila.get("por") or "")
                c.drawString(margin_x + 10, y, str(i))
                c.drawString(margin_x + 30, y, dni[:15])
                c.drawString(margin_x + 120, y, cuit[:20])
                c.drawString(margin_x + 220, y, nom[:18])
                c.drawString(margin_x + 340, y, ape[:18])
                c.drawString(margin_x + 460, y, por[:20])
                y -= 12

        detalle_bad = resumen.get("detalle_no_match", []) or []
        ensure_space(120)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin_x, y, "Detalle de no aprobados:")
        y -= 16

        c.setFont("Helvetica", 9)
        if not detalle_bad and no_matcheados > 0:
            c.drawString(margin_x + 10, y, f"— Hay {no_matcheados} sin match, pero no se generó el detalle. —")
            y -= 12
        elif not detalle_bad:
            c.drawString(margin_x + 10, y, "— Sin registros —")
            y -= 12
        else:
            c.drawString(margin_x + 10, y, "#")
            c.drawString(margin_x + 30, y, "DNI")
            c.drawString(margin_x + 120, y, "CUIT esperado")
            c.drawString(margin_x + 260, y, "Observación")
            y -= 12

            for i, fila in enumerate(detalle_bad, start=1):
                ensure_space()
                dni = str(fila.get("dni") or "")
                cuit = str(fila.get("cuit") or "")
                obs = str(fila.get("observacion") or "No coincide por CUIT ni por DNI.")
                c.drawString(margin_x + 10, y, str(i))
                c.drawString(margin_x + 30, y, dni[:15])
                c.drawString(margin_x + 120, y, cuit[:20])
                c.drawString(margin_x + 260, y, obs[:90])
                y -= 12

        detalle_fuera = resumen.get("detalle_fuera_cupo", []) or []
        if detalle_fuera:
            ensure_space(120)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(margin_x, y, "Lista de espera (Fuera de cupo):")
            y -= 16
            c.setFont("Helvetica", 9)
            c.drawString(margin_x + 10, y, "#")
            c.drawString(margin_x + 30, y, "DNI")
            c.drawString(margin_x + 120, y, "CUIT")
            c.drawString(margin_x + 260, y, "Nombre")
            c.drawString(margin_x + 380, y, "Apellido")
            y -= 12
            for i, fila in enumerate(detalle_fuera, start=1):
                ensure_space()
                c.drawString(margin_x + 10, y, str(i))
                c.drawString(margin_x + 30, y, str(fila.get("dni", ""))[:15])
                c.drawString(margin_x + 120, y, str(fila.get("cuit", ""))[:20])
                c.drawString(margin_x + 260, y, str(fila.get("nombre", ""))[:18])
                c.drawString(margin_x + 380, y, str(fila.get("apellido", ""))[:18])
                y -= 12

        c.showPage()
        c.save()
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    @staticmethod
    def _generar_prd_pdf(expediente: Expediente, resumen: dict) -> bytes:
        if _WEASY_OK:
            try:
                return CruceService._generar_prd_pdf_html(expediente, resumen)
            except Exception as e:
                logger.warning("WeasyPrint falló; se usa ReportLab. Detalle: %s", e)
        return CruceService._generar_prd_pdf_reportlab(expediente, resumen)

    @staticmethod
    def _generar_prd_csv(expediente: Expediente, resumen: dict) -> bytes:
        buffer = BytesIO()
        writer = csv.writer(buffer)
        writer.writerow(["PRD - Resultado de Cruce por CUIT/DNI"])

        writer.writerow(["Fecha", datetime.now().strftime("%d/%m/%Y %H:%M")])
        writer.writerow([])
        writer.writerow(["Resumen"])
        writer.writerow(["total_legajos", resumen.get("total_legajos", 0)])
        writer.writerow(["total_cuits_archivo", resumen.get("total_cuits_archivo", 0)])
        writer.writerow(["total_dnis_archivo", resumen.get("total_dnis_archivo", 0)])
        writer.writerow(["matcheados", resumen.get("matcheados", 0)])
        writer.writerow(["no_matcheados", resumen.get("no_matcheados", 0)])

        writer.writerow([])
        writer.writerow(["Cupo"])
        if resumen.get("cupo"):
            writer.writerow(["total_asignado", resumen["cupo"].get("total_asignado", "")])
            writer.writerow(["usados", resumen["cupo"].get("usados", "")])
            writer.writerow(["disponibles", resumen["cupo"].get("disponibles", "")])
            writer.writerow(["fuera_de_cupo", resumen.get("cupo_fuera_count", 0)])
        else:
            writer.writerow(["total_asignado", resumen.get("cupo_total", "")])
            writer.writerow(["usados", resumen.get("cupo_usados", "")])
            writer.writerow(["disponibles", resumen.get("cupo_disponibles", "")])
            writer.writerow(["fuera_de_cupo", resumen.get("fuera_cupo", 0)])

        writer.writerow([])
        writer.writerow(["Detalle_no_matcheados"])
        for fila in resumen.get("detalle_no_match", []):
            writer.writerow([fila])

        writer.writerow([])
        writer.writerow(["Detalle_fuera_de_cupo"])
        for fila in resumen.get("detalle_fuera_cupo", []):
            writer.writerow([fila])

        return buffer.getvalue()

    @staticmethod
    @transaction.atomic
    def procesar_cruce_por_cuit(expediente: Expediente, archivo_excel, usuario) -> dict:
        if not expediente:
            raise ValidationError("Expediente inválido.")

        estado_actual = expediente.estado.nombre
        estados_permitidos = ("ASIGNADO", "PROCESO_DE_CRUCE", "CRUCE_FINALIZADO")
        if estado_actual not in estados_permitidos:
            raise ValidationError("El expediente no está en un estado válido para realizar el cruce.")

        try:
            metrics_iniciales = CupoService.metrics_por_provincia(expediente.provincia)
        except CupoNoConfigurado as e:
            raise ValidationError(
                f"No hay cupo configurado para la provincia del expediente. {e}"
            )

        expediente.cruce_excel = archivo_excel
        expediente.usuario_modificador = usuario
        estado_proc, _ = EstadoExpediente.objects.get_or_create(nombre="PROCESO_DE_CRUCE")
        expediente.estado = estado_proc
        expediente.save(update_fields=["cruce_excel", "usuario_modificador", "estado"])

        ids_archivo = CruceService._leer_identificadores(expediente.cruce_excel)
        set_cuits = ids_archivo["cuits"]
        set_dnis_norm = ids_archivo["dnis"]

        legajos_all = (
            ExpedienteCiudadano.objects
            .select_related("ciudadano")
            .filter(expediente_id=expediente.id)
        )

        legajos_aprobados = list(legajos_all.filter(revision_tecnico="APROBADO"))
        total_legajos_aprobados = len(legajos_aprobados)
        if total_legajos_aprobados == 0:
            raise ValidationError("No hay legajos APROBADOS por el técnico para cruzar con Syntys.")

        matched_ids = []
        unmatched_ids = []
        detalle_match = []
        detalle_no_match = []

        for leg in legajos_aprobados:
            ciu = leg.ciudadano
            cuit_ciud = CruceService._resolver_cuit_ciudadano(ciu)
            dni_ciud = CruceService._normalize_dni_str(getattr(ciu, "documento", ""))

            by = None
            if cuit_ciud and cuit_ciud in set_cuits:
                match = True
                by = "CUIT"
            elif dni_ciud and dni_ciud in set_dnis_norm:
                match = True
                by = "DNI"
            else:
                match = False

            if match:
                matched_ids.append(leg.pk)
                detalle_match.append({
                    "dni": getattr(ciu, "documento", "") or "",
                    "cuit": cuit_ciud or "",
                    "por": by or "",
                    "nombre": getattr(ciu, "nombre", "") or "",
                    "apellido": getattr(ciu, "apellido", "") or "",
                })
            else:
                unmatched_ids.append(leg.pk)
                detalle_no_match.append({
                    "dni": getattr(ciu, "documento", "") or "",
                    "cuit": cuit_ciud or "",
                    "observacion": "No está en archivo de Syntys",
                })

        if matched_ids:
            ExpedienteCiudadano.objects.filter(pk__in=matched_ids).update(
                cruce_ok=True, resultado_sintys="MATCH", observacion_cruce=None
            )
        if unmatched_ids:
            ExpedienteCiudadano.objects.filter(pk__in=unmatched_ids).update(
                cruce_ok=False, resultado_sintys="NO_MATCH", observacion_cruce="No está en archivo de Syntys"
            )

        for leg in legajos_aprobados:
            if leg.pk in matched_ids:
                try:
                    CupoService.reservar_slot(legajo=leg, usuario=usuario)
                except CupoNoConfigurado as e:
                    raise ValidationError(f"Error de cupo: {e}")

        legajos_rechazados = legajos_all.filter(revision_tecnico="RECHAZADO").select_related("ciudadano")
        for leg in legajos_rechazados:
            ciu = leg.ciudadano
            cuit_ciud = CruceService._resolver_cuit_ciudadano(ciu)
            dni_ciud = CruceService._normalize_dni_str(getattr(ciu, "documento", ""))

            presente_en_archivo = (
                (cuit_ciud and cuit_ciud in set_cuits) or
                (dni_ciud and dni_ciud in set_dnis_norm)
            )

            obs = "Rechazado por técnico — presente en archivo de Syntys" if presente_en_archivo \
                else "Rechazado por técnico — no está en archivo de Syntys"

            detalle_no_match.append({
                "dni": getattr(ciu, "documento", "") or "",
                "cuit": cuit_ciud or "",
                "observacion": obs,
            })

        legajos_subsanar = legajos_all.filter(revision_tecnico="SUBSANAR").select_related("ciudadano")
        for leg in legajos_subsanar:
            ciu = leg.ciudadano
            cuit_ciud = CruceService._resolver_cuit_ciudadano(ciu)
            motivo = getattr(leg, "subsanacion_motivo", "") or "Subsanar solicitado"
            detalle_no_match.append({
                "dni": getattr(ciu, "documento", "") or "",
                "cuit": cuit_ciud or "",
                "observacion": f"Subsanar: {motivo}",
            })

        try:
            metrics_finales = CupoService.metrics_por_provincia(expediente.provincia)
        except CupoNoConfigurado:
            metrics_finales = metrics_iniciales

        fuera_qs = CupoService.lista_fuera_de_cupo_por_expediente(expediente.id).select_related("ciudadano")
        detalle_fuera = [{
            "dni": getattr(l.ciudadano, "documento", "") or "",
            "cuit": CruceService._resolver_cuit_ciudadano(l.ciudadano) or "",
            "nombre": getattr(l.ciudadano, "nombre", "") or "",
            "apellido": getattr(l.ciudadano, "apellido", "") or "",
        } for l in fuera_qs]
        fuera_count = len(detalle_fuera)

        aceptados = len(matched_ids)
        rechazados_tecnico = legajos_all.filter(revision_tecnico="RECHAZADO").count()
        rechazados_sintys = len(unmatched_ids)
        rechazados_subsanar = legajos_all.filter(revision_tecnico="SUBSANAR").count()

        resumen = {
            "total_cuits_archivo": len(set_cuits),
            "total_dnis_archivo": len(set_dnis_norm),
            "total_legajos": total_legajos_aprobados,
            "matcheados": aceptados,
            "no_matcheados": rechazados_sintys,
            "detalle_match": detalle_match,
            "detalle_no_match": detalle_no_match,
            "aceptados": aceptados,
            "rechazados_tecnico": rechazados_tecnico,
            "rechazados_sintys": rechazados_sintys,
            "rechazados_subsanar": rechazados_subsanar,
            "cupo": {
                "total_asignado": metrics_finales.get("total_asignado"),
                "usados": metrics_finales.get("usados"),
                "disponibles": metrics_finales.get("disponibles"),
            },
            "cupo_fuera_count": fuera_count,
            "detalle_fuera_cupo": detalle_fuera,
        }

        nombre_base = slugify(f"prd-cruce-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        try:
            pdf_bytes = CruceService._generar_prd_pdf(expediente, resumen)
            expediente.documento.save(f"{nombre_base}.pdf", ContentFile(pdf_bytes), save=False)
        except Exception as e:
            logger.warning("No fue posible generar PDF (se usará CSV fallback): %s", e)
            csv_bytes = CruceService._generar_prd_csv(expediente, resumen)
            expediente.documento.save(f"{nombre_base}.csv", ContentFile(csv_bytes), save=False)

        estado_final, _ = EstadoExpediente.objects.get_or_create(nombre="CRUCE_FINALIZADO")
        expediente.estado = estado_final
        expediente.usuario_modificador = usuario
        expediente.save(update_fields=["documento", "estado", "usuario_modificador"])

        logger.info(
            "Cruce finalizado para expediente: %s  %s match / %s no-match (sobre %s aprobados). Rechazados en detalle_no_match: %s. Fuera de cupo: %s.",
            expediente.id, aceptados, rechazados_sintys, total_legajos_aprobados,
            len(detalle_no_match), fuera_count
        )
        return resumen
