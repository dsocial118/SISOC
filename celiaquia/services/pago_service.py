# -*- coding: utf-8 -*-
from __future__ import annotations

import io
import logging
from datetime import datetime

import pandas as pd
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction

from core.models import Provincia
from celiaquia.models import (
    ExpedienteCiudadano,
    PagoExpediente,
    PagoNomina,
    PagoEstado,
    PagoNominaEstado,
    EstadoCupo,
)
from celiaquia.services.cupo_service import CupoService

logger = logging.getLogger("django")


def _norm_digits(s: str) -> str:
    return "".join(ch for ch in str(s or "").strip() if ch.isdigit())


def _leer_tabla(fileobj) -> pd.DataFrame:
    if hasattr(fileobj, "open"):
        fileobj.open()
    raw = fileobj.read()
    try:
        fileobj.seek(0)
    except Exception:
        pass
    bio = io.BytesIO(raw if isinstance(raw, (bytes, bytearray)) else bytes(raw or b""))
    try:
        df = pd.read_excel(bio, dtype=str)
    except Exception:
        bio.seek(0)
        try:
            df = pd.read_csv(bio, dtype=str)
        except Exception:
            bio.seek(0)
            df = pd.read_csv(bio, dtype=str, sep=";")
    df.columns = [
        str(c).strip().lower().replace("  ", " ").replace(" ", "_") for c in df.columns
    ]
    return df


class PagoService:
    @staticmethod
    def _qs_consolidado_activo(provincia: Provincia):
        """
        Nómina consolidada 'activa' para pago:
        - DENTRO de cupo
        - es_titular_activo = True
        - Aprobado por técnico y MATCH en Sintys
        """
        return ExpedienteCiudadano.objects.select_related(
            "ciudadano", "expediente", "expediente__usuario_provincia"
        ).filter(
            expediente__usuario_provincia__profile__provincia=provincia,
            estado_cupo=EstadoCupo.DENTRO,
            es_titular_activo=True,
            revision_tecnico="APROBADO",
            resultado_sintys="MATCH",
        )

    @staticmethod
    @transaction.atomic
    def crear_expediente_pago(
        *, provincia: Provincia, usuario, periodo: str | None = None
    ) -> PagoExpediente:
        """
        Crea el expediente de pago en BORRADOR y adjunta Excel de envío con la nómina actual activa.
        """
        periodo = periodo or datetime.now().strftime("%Y-%m")
        pago = PagoExpediente.objects.create(
            provincia=provincia,
            periodo=periodo,
            estado=PagoEstado.BORRADOR,
            creado_por=usuario,
        )

        # Generar Excel de envío (DNI, CUIT/CUIL, nombre, apellido, expediente)
        df_rows = []
        qs = PagoService._qs_consolidado_activo(provincia)
        for leg in qs:
            ciu = leg.ciudadano
            df_rows.append(
                {
                    "dni": _norm_digits(getattr(ciu, "documento", "")),
                    "cuit": _norm_digits(
                        getattr(ciu, "cuil", "") or getattr(ciu, "cuit", "")
                    ),
                    "nombre": getattr(ciu, "nombre", "") or "",
                    "apellido": getattr(ciu, "apellido", "") or "",
                    # FIX: usar str() en lugar de getattr con ""
                    "expediente": str(leg.expediente_id),
                }
            )

        pago.total_candidatos = len(df_rows)

        if df_rows:
            df = pd.DataFrame(
                df_rows, columns=["dni", "cuit", "nombre", "apellido", "expediente"]
            )
            out = io.BytesIO()
            with pd.ExcelWriter(out, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="nomina_pago")
            out.seek(0)
            nombre = f"pago_{provincia.id}_{periodo}.xlsx"
            pago.archivo_envio.save(nombre, ContentFile(out.getvalue()), save=False)

        pago.estado = PagoEstado.ENVIADO  # queda marcado como enviado (generado)
        pago.save(update_fields=["archivo_envio", "estado", "total_candidatos"])
        logger.info(
            "PagoExpediente creado %s - candidatos=%s", pago.pk, pago.total_candidatos
        )
        return pago

    @staticmethod
    @transaction.atomic
    def procesar_respuesta(*, pago: PagoExpediente, archivo_respuesta, usuario) -> dict:
        """
        Cruza la respuesta de Sintys con la nómina consolidada:
          - Si el DNI aparece en el archivo: crea entrada en PagoNomina (VALIDADO).
          - Si NO aparece: se SUSPENDE el legajo (sin liberar cupo) + observación.
        """
        if pago.estado not in (PagoEstado.ENVIADO, PagoEstado.PROCESADO):
            raise ValidationError(
                "El expediente de pago no está en un estado válido para procesar respuesta."
            )

        df = _leer_tabla(archivo_respuesta)
        cols = set(df.columns)
        col_dni = (
            "dni" if "dni" in cols else ("documento" if "documento" in cols else None)
        )
        if not col_dni:
            raise ValidationError(
                "El archivo de respuesta debe tener columna 'dni' o 'documento'."
            )

        dnis_presentes = {
            _norm_digits(v) for v in df[col_dni].fillna("").tolist() if _norm_digits(v)
        }
        if not dnis_presentes:
            raise ValidationError("El archivo de respuesta no contiene DNIs válidos.")

        qs = PagoService._qs_consolidado_activo(pago.provincia)

        total_validados = 0
        total_excluidos = 0

        for leg in qs:
            dni = _norm_digits(getattr(leg.ciudadano, "documento", ""))

            if dni in dnis_presentes:
                # crear registro de nómina si no existe
                _, created = PagoNomina.objects.get_or_create(
                    pago=pago,
                    legajo=leg,
                    defaults={
                        "documento": dni,
                        "nombre": getattr(leg.ciudadano, "nombre", "") or "",
                        "apellido": getattr(leg.ciudadano, "apellido", "") or "",
                        "estado": PagoNominaEstado.VALIDADO,
                        "observacion": "",
                    },
                )
                if created:
                    total_validados += 1
            else:
                # SUSPENDER en consolidado (no libera cupo) + observación
                try:
                    CupoService.suspender_slot(
                        legajo=leg,
                        usuario=usuario,
                        motivo="No está en el cruce Sintys para el pago",
                    )
                except Exception as e:
                    logger.warning("No se pudo suspender legajo %s: %s", leg.pk, e)

                # guardar observación visible en el legajo
                if (
                    getattr(leg, "observacion_cruce", None)
                    != "No está en el cruce Sintys para el pago"
                ):
                    leg.observacion_cruce = "No está en el cruce Sintys para el pago"
                    leg.save(update_fields=["observacion_cruce", "modificado_en"])

                total_excluidos += 1

        # Guardar archivo de respuesta y actualizar totales
        pago.archivo_respuesta = archivo_respuesta
        pago.total_validados = total_validados
        pago.total_excluidos = total_excluidos
        pago.estado = PagoEstado.PROCESADO
        pago.modificado_por = usuario
        pago.save(
            update_fields=[
                "archivo_respuesta",
                "total_validados",
                "total_excluidos",
                "estado",
                "modificado_por",
            ]
        )

        logger.info(
            "PagoExpediente %s procesado: validados=%s excluidos=%s",
            pago.pk,
            total_validados,
            total_excluidos,
        )
        return {
            "validados": total_validados,
            "excluidos": total_excluidos,
            "total_candidatos": pago.total_candidatos,
        }

    @staticmethod
    def exportar_nomina_actual_excel(*, provincia) -> bytes:
        """
        Exporta la nómina ACTUAL de la provincia con titulares que ocupan cupo:
        - estado_cupo = DENTRO
        - es_titular_activo = True
        - revision_tecnico = APROBADO
        - resultado_sintys = MATCH
        (No incluye suspendidos)
        """
        qs = PagoService._qs_consolidado_activo(provincia)

        rows = []
        for leg in qs:
            ciu = leg.ciudadano
            rows.append(
                {
                    "dni": _norm_digits(getattr(ciu, "documento", "")),
                    "cuit": _norm_digits(
                        getattr(ciu, "cuil", "") or getattr(ciu, "cuit", "")
                    ),
                    "nombre": getattr(ciu, "nombre", "") or "",
                    "apellido": getattr(ciu, "apellido", "") or "",
                    # FIX
                    "expediente": str(leg.expediente_id),
                }
            )

        import io as _io
        import pandas as _pd

        out = _io.BytesIO()
        df = _pd.DataFrame(
            rows, columns=["dni", "cuit", "nombre", "apellido", "expediente"]
        )
        with _pd.ExcelWriter(out, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="nomina_actual")
        out.seek(0)
        return out.getvalue()
