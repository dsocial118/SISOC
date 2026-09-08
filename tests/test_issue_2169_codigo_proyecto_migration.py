"""Contrato de la limpieza de Código de Proyecto para issue #2169."""

import importlib
from types import SimpleNamespace

import pytest

from comedores.models import Comedor, Programas


MIGRATION = importlib.import_module(
    "comedores.migrations.0052_issue_2169_codigo_proyecto"
)


@pytest.mark.django_db
def test_limpieza_codigo_proyecto_afecta_solo_alimentar_comunidad():
    alimentar = Programas.objects.create(nombre="Alimentar Comunidad")
    secos = Programas.objects.create(nombre="Abordaje Comunitario - Línea Secos")
    tradicional = Programas.objects.create(
        nombre="Abordaje Comunitario - Línea Tradicional"
    )
    otro = Programas.objects.create(nombre="Otro programa")

    comedor_alimentar = Comedor.objects.create(
        nombre="PAC", programa=alimentar, codigo_de_proyecto="PAC1234"
    )
    comedor_secos = Comedor.objects.create(
        nombre="Secos", programa=secos, codigo_de_proyecto="SEC1234"
    )
    comedor_tradicional = Comedor.objects.create(
        nombre="Tradicional", programa=tradicional, codigo_de_proyecto="TRA1234"
    )
    comedor_otro = Comedor.objects.create(
        nombre="Otro", programa=otro, codigo_de_proyecto="OTR1234"
    )

    apps = SimpleNamespace(
        get_model=lambda app_label, model_name: {
            ("comedores", "Comedor"): Comedor,
            ("comedores", "Programas"): Programas,
        }[(app_label, model_name)]
    )
    MIGRATION.limpiar_codigos_alimentar_comunidad(apps, schema_editor=None)

    comedor_alimentar.refresh_from_db()
    comedor_secos.refresh_from_db()
    comedor_tradicional.refresh_from_db()
    comedor_otro.refresh_from_db()

    assert comedor_alimentar.codigo_de_proyecto is None
    assert comedor_secos.codigo_de_proyecto == "SEC1234"
    assert comedor_tradicional.codigo_de_proyecto == "TRA1234"
    assert comedor_otro.codigo_de_proyecto == "OTR1234"
