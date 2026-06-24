"""El proceso de cruce acepta la columna numero_cuil que exporta la nómina SINTyS.

Regresión: el archivo exportado por la nómina SINTyS usa la columna
`numero_cuil`; debe poder reutilizarse directamente en "Subir Excel de documentos
(Cruce)" sin modificaciones.
"""

import io

import openpyxl

from celiaquia.services.cruce_service import (
    CruceService,
    DOCUMENTO_COL_CANDIDATAS,
)


def _xlsx(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


def test_numero_cuil_es_columna_valida():
    assert "numero_cuil" in DOCUMENTO_COL_CANDIDATAS


def test_cruce_lee_identificadores_desde_numero_cuil():
    # Header igual al que genera la nómina SINTyS, con un CUIL (11 dígitos) y un
    # DNI (8 dígitos).
    contenido = _xlsx(
        [
            ["numero_cuil"],
            ["20123456784"],
            ["12345678"],
        ]
    )

    result = CruceService._leer_identificadores(contenido)

    # El CUIL de 11 dígitos se trata como CUIT y se extrae su DNI.
    assert "20123456784" in result["cuits"]
    assert "12345678" in result["dnis"]


def test_cruce_columna_invalida_sigue_fallando():
    import pytest
    from django.core.exceptions import ValidationError

    contenido = _xlsx([["columna_rara"], ["123"]])
    with pytest.raises(ValidationError):
        CruceService._leer_identificadores(contenido)
