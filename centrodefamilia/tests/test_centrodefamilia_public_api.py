import pytest

from centrodefamilia.api import (
    MetricasDashboardCentroFamilia,
    obtener_metricas_dashboard,
)
from centrodefamilia.models import ActividadCentro, Centro, ParticipanteActividad


@pytest.mark.django_db
def test_obtener_metricas_dashboard_expone_valores_agregados(mocker):
    mocker.patch.object(
        ParticipanteActividad.objects,
        "filter",
        return_value=mocker.Mock(count=mocker.Mock(return_value=7)),
    )
    mocker.patch.object(
        Centro.objects,
        "filter",
        side_effect=[
            mocker.Mock(count=mocker.Mock(return_value=3)),
            mocker.Mock(count=mocker.Mock(return_value=2)),
        ],
    )
    mocker.patch.object(
        ActividadCentro.objects,
        "count",
        return_value=11,
    )

    metricas = obtener_metricas_dashboard()

    assert metricas == MetricasDashboardCentroFamilia(
        participantes_total=7,
        centros_adheridos_totales=3,
        centros_faro_totales=2,
        actividades_totales=11,
    )
