"""Regresiones del seed QA para etapas de rendiciones."""

from io import StringIO

import pytest
from django.core.management import call_command

from comedores.models import Comedor, Programas
from core.models import Provincia
from rendicioncuentasmensual.management.commands import (
    seed_rendicion_stage_examples as command_module,
)
from rendicioncuentasmensual.models import DocumentacionAdjunta, RendicionCuentaMensual


@pytest.fixture
def comedores_qa():
    provincia = Provincia.objects.create(nombre="Provincia QA")
    programa = Programas.objects.create(nombre="Programa QA")
    return (
        Comedor.objects.create(
            nombre="Comedor QA uno", provincia=provincia, programa=programa
        ),
        Comedor.objects.create(
            nombre="Comedor QA dos", provincia=provincia, programa=programa
        ),
    )


def _ejecutar_seed(comedor, monkeypatch):
    monkeypatch.setattr(
        command_module,
        "getpass",
        lambda _prompt: "contrasena-qa-segura",
        raising=False,
    )
    call_command(
        "seed_rendicion_stage_examples",
        "--comedor-id",
        comedor.pk,
        stdout=StringIO(),
    )


@pytest.mark.django_db
def test_seed_solicita_contrasena_sin_recibirla_por_argumento(
    comedores_qa, monkeypatch
):
    comedor, _ = comedores_qa

    _ejecutar_seed(comedor, monkeypatch)

    assert RendicionCuentaMensual.objects.filter(comedor=comedor).count() == 4


@pytest.mark.django_db
def test_seed_mantiene_las_rendiciones_qa_en_cada_comedor(comedores_qa, monkeypatch):
    comedor_uno, comedor_dos = comedores_qa

    _ejecutar_seed(comedor_uno, monkeypatch)
    _ejecutar_seed(comedor_dos, monkeypatch)

    assert RendicionCuentaMensual.objects.filter(comedor=comedor_uno).count() == 4
    assert RendicionCuentaMensual.objects.filter(comedor=comedor_dos).count() == 4


@pytest.mark.django_db
def test_seed_reutiliza_el_documento_qa_en_repetidas_ejecuciones(
    comedores_qa, monkeypatch
):
    comedor, _ = comedores_qa

    _ejecutar_seed(comedor, monkeypatch)
    documento = DocumentacionAdjunta.objects.get(
        rendicion_cuenta_mensual__comedor=comedor,
        rendicion_cuenta_mensual__etapa_proceso="revision_documentacion",
        nombre="[QA ETAPAS] Documento presentado",
    )

    _ejecutar_seed(comedor, monkeypatch)

    documentos = DocumentacionAdjunta.all_objects.filter(
        rendicion_cuenta_mensual__comedor=comedor,
        rendicion_cuenta_mensual__etapa_proceso="revision_documentacion",
        nombre="[QA ETAPAS] Documento presentado",
    )
    assert list(documentos.values_list("pk", flat=True)) == [documento.pk]
