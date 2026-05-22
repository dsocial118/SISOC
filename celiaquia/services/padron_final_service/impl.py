"""
Servicio para generar padrón final del expediente de celiaquía.
"""

from io import BytesIO
import re

from openpyxl import Workbook, load_workbook

from celiaquia.models import ExpedienteCiudadano, ResultadoSintys, RevisionTecnico


DOCUMENTO_COLUMN_CANDIDATES = {
    "documento",
    "numero_documento",
    "nro_documento",
    "número_documento",
    "dni",
    "cuit",
    "cuil",
}


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
        documentos_aprobados = PadronFinalService._documentos_aprobados(expediente)

        filtered_rows = []
        if documento_index is not None and documentos_aprobados:
            for row in rows:
                documento = PadronFinalService._normalize_documento(
                    row[documento_index] if documento_index < len(row) else None
                )
                if documento in documentos_aprobados:
                    filtered_rows.append(row)

        return PadronFinalService._build_excel(headers, filtered_rows)

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
    def _documentos_aprobados(expediente) -> set[str]:
        aprobados = (
            ExpedienteCiudadano.objects.filter(
                expediente=expediente,
                revision_tecnico=RevisionTecnico.APROBADO,
                resultado_sintys=ResultadoSintys.MATCH,
            )
            .exclude(rol=ExpedienteCiudadano.ROLE_RESPONSABLE)
            .select_related("ciudadano")
            .values_list("ciudadano__documento", flat=True)
        )
        return {
            documento
            for documento in (
                PadronFinalService._normalize_documento(value) for value in aprobados
            )
            if documento
        }

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
    def _normalize_documento(value) -> str:
        if value is None:
            return ""
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        return re.sub(r"\D", "", str(value)).lstrip("0")

    @staticmethod
    def _build_excel(headers, rows) -> bytes:
        wb = Workbook()
        ws = wb.active
        ws.title = "nomina_aprobados"
        if headers:
            ws.append(headers)
        for row in rows:
            ws.append(row)

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()
