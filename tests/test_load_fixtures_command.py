"""Tests de regresión para el comando load_fixtures."""

import json

import pytest
from django.apps import apps
from unittest.mock import patch

from core.management.commands.load_fixtures import Command

pytestmark = pytest.mark.django_db


def test_upsert_fixture_reintenta_fk_hijo_antes_de_padre(tmp_path):
    """Debe guardar ambos registros aunque el hijo aparezca antes que el padre."""
    tipo_pk = 99001
    sub_pk = 99002
    fixture_path = tmp_path / "intervenciones_desordenadas.json"
    fixture_data = [
        {
            "model": "intervenciones.subintervencion",
            "pk": sub_pk,
            "fields": {
                "nombre": "Sub intervención de prueba",
                "tipo_intervencion": tipo_pk,
            },
        },
        {
            "model": "intervenciones.tipointervencion",
            "pk": tipo_pk,
            "fields": {"nombre": "Tipo intervención de prueba", "programa": "cdi"},
        },
    ]

    fixture_path.write_text(
        json.dumps(fixture_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    Command().upsert_fixture(str(fixture_path))

    tipo_model = apps.get_model("intervenciones", "TipoIntervencion")
    sub_model = apps.get_model("intervenciones", "SubIntervencion")
    tipo = tipo_model.objects.get(pk=tipo_pk)
    sub = sub_model.objects.get(pk=sub_pk)

    assert sub.tipo_intervencion_id == tipo.pk


def test_handle_sincroniza_catalogo_cdi_despues_de_cargar():
    command = Command()

    with patch.object(command, "load_fixtures") as load_mock, patch(
        "core.management.commands.load_fixtures.sync_catalogo_intervenciones",
        return_value={
            "tipos_sincronizados": 1,
            "subtipos_sincronizados": 2,
            "subtipos_vacios_eliminados": 3,
        },
    ) as sync_mock:
        command.handle(force=False)

    load_mock.assert_called_once_with()
    sync_mock.assert_called_once_with()
