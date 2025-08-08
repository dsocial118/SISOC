# centrodefamilia/services/informe_cabal_service.py
"""
[Informe Cabal - Service]
- Lee Excel (.xlsx) con columnas fijas y fecha dd/mm/aaaa.
- Previsualiza con paginación (25 por página) y detecta no-coincidentes por NroComercio→Centro.codigo.
- Persiste CabalArchivo + InformeCabalRegistro (sin bloquear por no-coincidentes).
- Si nombre de archivo ya existe, marca advertencia para preguntar “¿desea proseguir?”.
"""
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.core.paginator import Paginator
from openpyxl import load_workbook
from datetime import datetime

from centrodefamilia.models import Centro, CabalArchivo, InformeCabalRegistro

logger = logging.getLogger(__name__)

# Layout esperado (en este orden)
EXPECTED_HEADERS = [
    "NroTarjeta", "NroAuto", "MTI", "NroComercio", "RazonSocial", "Importe",
    "FechaTRX", "MonedaOrigen", "ImporteMonOrigen", "ImportePesos",
    "CantCuotas", "MotivoRechazo", "Desc_MotivoRechazo", "Disponibles"
]

@dataclass
class PreviewRow:
    fila: int
    data: Dict[str, Any]
    no_coincidente: bool

def _parse_date_ddmmyyyy(value: Any) -> Optional[datetime.date]:
    if value in (None, "", 0):
        return None
    # Excel puede venir como fecha o como string
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        value = value.strip()
        try:
            return datetime.strptime(value, "%d/%m/%Y").date()
        except Exception:
            pass
    # último intento: excel serial? (no lo forzamos)
    return None

def _get_cell(row, col_index):
    val = row[col_index].value
    return "" if val is None else val

def read_excel_preview(file: UploadedFile, page: int = 1, per_page: int = 25) -> Tuple[List[PreviewRow], List[int], int]:
    """
    Lee el Excel y devuelve:
      - rows de la página solicitada (PreviewRow)
      - lista de índices de filas no coincidentes
      - total de filas útiles
    No persiste aún.
    """
    wb = load_workbook(filename=file, data_only=True)
    ws = wb.active

    # Validar headers exactos
    headers = [str(cell.value).strip() if cell.value is not None else "" for cell in ws[1]]
    if headers[:len(EXPECTED_HEADERS)] != EXPECTED_HEADERS:
        raise ValueError("El encabezado del Excel no coincide con el esperado.")

    # Construir filas
    all_rows: List[PreviewRow] = []
    not_matching: List[int] = []
    for i, row in enumerate(ws.iter_rows(min_row=2), start=2):
        data = {
            "NroTarjeta": _get_cell(row, 0),
            "NroAuto": _get_cell(row, 1),
            "MTI": _get_cell(row, 2),
            "NroComercio": _get_cell(row, 3),
            "RazonSocial": _get_cell(row, 4),
            "Importe": _get_cell(row, 5),
            "FechaTRX": _get_cell(row, 6),
            "MonedaOrigen": _get_cell(row, 7),
            "ImporteMonOrigen": _get_cell(row, 8),
            "ImportePesos": _get_cell(row, 9),
            "CantCuotas": _get_cell(row, 10),
            "MotivoRechazo": _get_cell(row, 11),
            "Desc_MotivoRechazo": _get_cell(row, 12),
            "Disponibles": _get_cell(row, 13),
        }
        codigo = str(data["NroComercio"]).strip()
        match = Centro.objects.filter(codigo=codigo).only("id").exists()
        no_coincidente = not match
        if no_coincidente:
            not_matching.append(i - 1)  # “registro (1,2,3...)” respecto a min_row=2
        all_rows.append(PreviewRow(fila=i - 1, data=data, no_coincidente=no_coincidente))

    paginator = Paginator(all_rows, per_page)
    page_obj = paginator.get_page(page)
    return list(page_obj.object_list), not_matching, paginator.count

@transaction.atomic
def persist_file_and_rows(
    file: UploadedFile,
    user,
    force_proceed: bool = False,
) -> Tuple[CabalArchivo, int, int, List[int]]:
    """
    Persiste CabalArchivo + InformeCabalRegistro.
    - Si nombre ya existe, marca advertencia y requiere confirmación (force_proceed True).
    - No bloquea por no-coincidentes: los persiste con centro=None y no_coincidente=True.
    Devuelve: (archivo, total, total_validas, no_coincidentes_indices)
    """
    nombre = file.name
    nombre_duplicado = CabalArchivo.objects.filter(nombre_original=nombre).exists()
    advert = nombre_duplicado and not force_proceed
    if advert:
        # solo registramos log y abortamos; la vista devuelve alerta “¿desea proseguir?”
        logger.info("Nombre de archivo duplicado detectado: %s", nombre)
        raise FileExistsError("DUPLICATE_NAME")

    # Re-parseo completo para persistir todo
    preview_rows, not_matching, total_rows = read_excel_preview(file, page=1, per_page=10**9)

    cabal_archivo = CabalArchivo.objects.create(
        archivo=file,
        nombre_original=nombre,
        usuario=user,
        advertencia_nombre_duplicado=nombre_duplicado,
        total_filas=total_rows,
        total_validas=0,      # actualizamos luego
        total_invalidas=0,    # actualizamos luego
    )

    total_validas = 0
    total_invalidas = 0
    registros_bulk = []
    for pr in preview_rows:
        d = pr.data
        # parseos numéricos/fecha
        def _to_decimal(v):
            if v in ("", None):
                return None
            try:
                return float(str(v).replace(",", "."))
            except Exception:
                return None

        reg = InformeCabalRegistro(
            archivo=cabal_archivo,
            centro=Centro.objects.filter(codigo=str(d["NroComercio"]).strip()).first(),
            nro_tarjeta=str(d["NroTarjeta"]),
            nro_auto=str(d["NroAuto"]),
            mti=str(d["MTI"]),
            nro_comercio=str(d["NroComercio"]),
            razon_social=str(d["RazonSocial"]),
            importe=_to_decimal(d["Importe"]),
            fecha_trx=_parse_date_ddmmyyyy(d["FechaTRX"]),
            moneda_origen=str(d["MonedaOrigen"]),
            importe_mon_origen=_to_decimal(d["ImporteMonOrigen"]),
            importe_pesos=_to_decimal(d["ImportePesos"]),
            cant_cuotas=int(d["CantCuotas"]) if str(d["CantCuotas"]).strip().isdigit() else None,
            motivo_rechazo=str(d["MotivoRechazo"]),
            desc_motivo_rechazo=str(d["Desc_MotivoRechazo"]),
            disponibles=str(d["Disponibles"]),
            no_coincidente=pr.no_coincidente,
            fila_numero=pr.fila,
        )
        if pr.no_coincidente:
            total_invalidas += 1
        else:
            total_validas += 1
        registros_bulk.append(reg)

    InformeCabalRegistro.objects.bulk_create(registros_bulk, batch_size=2000)

    cabal_archivo.total_validas = total_validas
    cabal_archivo.total_invalidas = total_invalidas
    cabal_archivo.save(update_fields=["total_validas", "total_invalidas"])

    return cabal_archivo, total_rows, total_validas, not_matching
