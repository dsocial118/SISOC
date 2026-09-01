from types import SimpleNamespace

from core.services.csv_export import CSV_CONTENT_TYPE, UTF8_BOM
from pas.services.informe_service import csv_response_for_informe


def test_csv_informe_reutiliza_politica_central_con_bom():
    informe = SimpleNamespace(numero="PAS-INF-000001", resultado=[])

    response = csv_response_for_informe(informe)

    assert response["Content-Type"] == CSV_CONTENT_TYPE
    assert response["Content-Disposition"] == (
        'attachment; filename="pas-inf-000001.csv"'
    )
    assert response.content.decode("utf-8").startswith(UTF8_BOM)
