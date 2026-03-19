import json

import pytest

from intervenciones.models.intervenciones import SubIntervencion, TipoIntervencion
from intervenciones.services_catalogo import sync_catalogo_intervenciones


@pytest.mark.django_db
def test_sync_catalogo_intervenciones_crea_tipos_y_subtipos_desde_fixture(tmp_path):
    fixture_path = tmp_path / "catalogo.json"
    fixture_path.write_text(
        json.dumps(
            [
                {
                    "model": "intervenciones.tipointervencion",
                    "pk": 1,
                    "fields": {"nombre": "Tipo Comedores", "programa": "comedores"},
                },
                {
                    "model": "intervenciones.subintervencion",
                    "pk": 2,
                    "fields": {"nombre": "Subtipo Comedores", "tipo_intervencion": 1},
                },
            ]
        )
    )

    resumen = sync_catalogo_intervenciones(fixture_path)

    assert TipoIntervencion.objects.filter(
        nombre="Tipo Comedores",
        programa="comedores",
    ).exists()
    assert SubIntervencion.objects.filter(
        nombre="Subtipo Comedores",
        tipo_intervencion__nombre="Tipo Comedores",
    ).exists()
    assert resumen["subtipos_sincronizados"] >= 1


@pytest.mark.django_db
def test_sync_catalogo_intervenciones_reasigna_subtipos_y_elimina_vacios(tmp_path):
    fixture_path = tmp_path / "catalogo.json"
    fixture_path.write_text(
        json.dumps(
            [
                {
                    "model": "intervenciones.tipointervencion",
                    "pk": 10,
                    "fields": {"nombre": "Entrevista inicial", "programa": "cdi"},
                },
                {
                    "model": "intervenciones.subintervencion",
                    "pk": 11,
                    "fields": {"nombre": "Ingreso", "tipo_intervencion": 10},
                },
            ]
        )
    )
    tipo = TipoIntervencion.objects.create(nombre="Entrevista inicial", programa=None)
    subtipo_huerfano = SubIntervencion.objects.create(nombre="Ingreso")
    SubIntervencion.objects.create(nombre="", tipo_intervencion=None)

    resumen = sync_catalogo_intervenciones(fixture_path)

    tipo.refresh_from_db()
    subtipo_huerfano.refresh_from_db()

    assert tipo.programa == "cdi"
    assert subtipo_huerfano.tipo_intervencion == tipo
    assert not SubIntervencion.objects.filter(nombre="").exists()
    assert resumen["subtipos_vacios_eliminados"] >= 1
