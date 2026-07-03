"""
Servicio para generar padrón final del expediente de celiaquía.
"""

from datetime import date, datetime
from io import BytesIO
import logging
import re

from openpyxl import Workbook, load_workbook

from celiaquia.models import (
    EstadoCupo,
    ExpedienteCiudadano,
    ResultadoSintys,
    RevisionTecnico,
)

logger = logging.getLogger("django")

ESTADO_CUPO_HEADER = "Estado de cupo"


DOCUMENTO_COLUMN_CANDIDATES = {
    "documento",
    "numero_documento",
    "nro_documento",
    "número_documento",
    "dni",
    "cuit",
    "cuil",
}

FECHA_NACIMIENTO_COLUMN_CANDIDATES = {
    "fecha_nacimiento",
    "fecha_de_nacimiento_responsable",
}

FECHA_NUMBER_FORMAT = "DD/MM/YYYY"


class PadronFinalService:
    """Genera nomina final aprobada en Excel para expediente de celiaquia."""

    @staticmethod
    def generar_padron_final_excel(expediente) -> bytes:
        """
        Genera Excel con la nomina original filtrada por aprobados finales.

        Args:
            expediente: Expediente object

        Returns:
            bytes: Contenido del archivo Excel
        """
        headers, rows = PadronFinalService._leer_nomina_original(expediente)
        documento_index = PadronFinalService._documento_column_index(headers)
        fecha_indices = PadronFinalService._fecha_nacimiento_column_indices(headers)
        aprobados = PadronFinalService._aprobados_con_estado(expediente)

        # Mapa clave-de-documento -> estado de cupo legible, para etiquetar cada
        # fila del Excel original.
        estado_por_clave = {}
        for aprobado in aprobados:
            for clave in aprobado["claves"]:
                estado_por_clave[clave] = aprobado["estado"]

        ncols = len(headers)
        filtered_rows = []
        claves_en_excel = set()
        if documento_index is not None:
            for row in rows:
                clave = PadronFinalService._documento_match_key(
                    row[documento_index] if documento_index < len(row) else None
                )
                if not clave:
                    continue
                claves_en_excel.add(clave)
                estado = estado_por_clave.get(clave)
                if estado is None:
                    continue
                # El padrón incluye a TODOS los aprobados+match; la columna de
                # estado de cupo distingue titulares con cupo de lista de espera.
                fila = list(row)
                if len(fila) < ncols:
                    fila += [None] * (ncols - len(fila))
                fila.append(estado)
                filtered_rows.append(fila)

        # Observabilidad: si algún aprobado no tiene fila en el Excel original
        # (por ninguna de sus claves), queda registrado para no perderlo en
        # silencio.
        faltan = sum(1 for a in aprobados if not (a["claves"] & claves_en_excel))
        if faltan:
            logger.warning(
                "padron_final.aprobados_sin_fila_excel",
                extra={
                    "data": {
                        "expediente_id": getattr(expediente, "id", None),
                        "aprobados": len(aprobados),
                        "en_nomina": len(aprobados) - faltan,
                        "faltan": faltan,
                    }
                },
            )

        headers_out = list(headers) + [ESTADO_CUPO_HEADER] if headers else headers
        return PadronFinalService._build_excel(
            headers_out, filtered_rows, fecha_indices
        )

    @staticmethod
    def _leer_nomina_original(expediente):
        excel_masivo = getattr(expediente, "excel_masivo", None)
        if not excel_masivo:
            return [], []

        try:
            excel_masivo.open()
        except Exception:  # pragma: no cover - FileField local ya suele estar abierto.
            pass
        excel_masivo.seek(0)
        wb = load_workbook(BytesIO(excel_masivo.read()), data_only=True)
        ws = wb.worksheets[0]
        values = list(ws.iter_rows(values_only=True))
        if not values:
            return [], []

        headers = list(values[0])
        rows = [list(row) for row in values[1:]]
        return headers, rows

    @staticmethod
    def _estado_cupo_label(estado_cupo) -> str:
        """Etiqueta legible del estado de cupo para la columna del padrón."""
        if estado_cupo == EstadoCupo.DENTRO:
            return "Con cupo asignado"
        if estado_cupo == EstadoCupo.FUERA:
            return "Lista de espera"
        return "Sin evaluar"

    @staticmethod
    def _aprobados_con_estado(expediente) -> list[dict]:
        """Aprobados+MATCH (no responsables) con sus claves de emparejamiento y
        su estado de cupo legible.

        Se consideran documento Y cuil_cuit: el cruce SINTYS identifica a la
        persona por su CUIL/CUIT (resolver_cuit_ciudadano) y recién después por
        el documento. Si el export solo mirara documento, un aprobado matcheado
        por cuil_cuit (con documento vacío o en otro formato) quedaría fuera de
        la nómina en silencio. Ambas claves usan la misma tolerancia CUIL↔DNI
        para coincidir con la fila del Excel original.
        """
        filas = (
            ExpedienteCiudadano.objects.filter(
                expediente=expediente,
                revision_tecnico=RevisionTecnico.APROBADO,
                resultado_sintys=ResultadoSintys.MATCH,
            )
            .exclude(rol=ExpedienteCiudadano.ROLE_RESPONSABLE)
            .values_list("ciudadano__documento", "ciudadano__cuil_cuit", "estado_cupo")
        )
        aprobados = []
        for documento, cuil_cuit, estado_cupo in filas:
            claves = {
                PadronFinalService._documento_match_key(valor)
                for valor in (documento, cuil_cuit)
            }
            claves.discard("")
            if claves:
                aprobados.append(
                    {
                        "claves": claves,
                        "estado": PadronFinalService._estado_cupo_label(estado_cupo),
                    }
                )
        return aprobados

    @staticmethod
    def _normalize_header(value) -> str:
        normalized = str(value or "").strip().lower()
        normalized = normalized.replace(" ", "_").replace(".", "")
        return normalized

    @staticmethod
    def _documento_column_index(headers) -> int | None:
        for index, header in enumerate(headers):
            if (
                PadronFinalService._normalize_header(header)
                in DOCUMENTO_COLUMN_CANDIDATES
            ):
                return index
        return None

    @staticmethod
    def _fecha_nacimiento_column_indices(headers) -> set[int]:
        return {
            index
            for index, header in enumerate(headers)
            if PadronFinalService._normalize_header(header)
            in FECHA_NACIMIENTO_COLUMN_CANDIDATES
        }

    @staticmethod
    def _normalize_documento(value) -> str:
        if value is None:
            return ""
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        return re.sub(r"\D", "", str(value)).lstrip("0")

    @staticmethod
    def _documento_match_key(value) -> str:
        """Clave para emparejar el documento de la base con el del Excel original,
        tolerante a que uno esté como CUIL/CUIT (11 díg.) y el otro como DNI.

        Un CUIL/CUIT de persona física es prefijo(2) + DNI(8) + verificador(1); se
        reduce a su núcleo DNI para que, p. ej., ``20-39231798-9`` (base) y
        ``39231798`` (Excel) coincidan. Se aplica igual a ambos lados, así el
        emparejamiento es simétrico sin importar en qué formato venga cada uno.
        Antes se comparaba el número completo y los titulares con CUIL en la base
        y DNI en el Excel (o viceversa) quedaban fuera de la nómina.
        """
        digits = PadronFinalService._normalize_documento(value)
        if len(digits) == 11:
            return digits[2:10].lstrip("0")
        return digits

    @staticmethod
    def _build_excel(headers, rows, fecha_indices=None) -> bytes:
        fecha_indices = fecha_indices or set()
        wb = Workbook()
        ws = wb.active
        ws.title = "nomina_aprobados"
        if headers:
            ws.append(headers)
        for row in rows:
            ws.append(row)
            if fecha_indices:
                PadronFinalService._formatear_fechas_fila(ws[ws.max_row], fecha_indices)

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

    @staticmethod
    def _formatear_fechas_fila(cells, fecha_indices) -> None:
        """Muestra las fechas de nacimiento como fecha sin hora (DD/MM/AAAA)."""
        for index in fecha_indices:
            if index >= len(cells):
                continue
            cell = cells[index]
            value = cell.value
            if isinstance(value, datetime):
                cell.value = value.date()
            if isinstance(cell.value, date):
                cell.number_format = FECHA_NUMBER_FORMAT
