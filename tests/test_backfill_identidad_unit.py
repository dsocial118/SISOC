"""
Tests de integración para el comando backfill_identidad.
Fase 4 — identidad ciudadano.

Usan DB real (pytest.mark.django_db) porque el comando opera sobre
registros reales y usa update() por batch.
"""
from datetime import date
from io import StringIO

import pytest
from django.core.management import call_command

from ciudadanos.models import Ciudadano


def _ciudadano(**kwargs):
    defaults = {
        "nombre": "Test",
        "apellido": "Ciudadano",
        "fecha_nacimiento": date(1990, 1, 1),
    }
    defaults.update(kwargs)
    return Ciudadano.objects.create(**defaults)


def _run_backfill():
    call_command("backfill_identidad", stdout=StringIO(), stderr=StringIO())


@pytest.mark.django_db
def test_sin_documento_clasifica_como_sin_dni():
    c = _ciudadano(documento=None)

    _run_backfill()

    c.refresh_from_db()
    assert c.tipo_registro_identidad == Ciudadano.TIPO_REGISTRO_SIN_DNI
    assert c.identificador_interno == f"CIU-{c.pk}"
    assert c.requiere_revision_manual is True
    assert c.documento_unico_key is None


@pytest.mark.django_db
def test_dni_unico_clasifica_como_estandar():
    c = _ciudadano(documento=11111111)

    _run_backfill()

    c.refresh_from_db()
    assert c.tipo_registro_identidad == Ciudadano.TIPO_REGISTRO_ESTANDAR
    assert c.identificador_interno == f"CIU-{c.pk}"
    assert c.documento_unico_key == f"DNI_11111111"
    assert c.requiere_revision_manual is False


@pytest.mark.django_db
def test_dni_duplicado_clasifica_como_no_validado():
    c1 = _ciudadano(nombre="Ana", documento=22222222)
    c2 = _ciudadano(nombre="Beto", documento=22222222)

    _run_backfill()

    for c in (c1, c2):
        c.refresh_from_db()
        assert c.tipo_registro_identidad == Ciudadano.TIPO_REGISTRO_DNI_NO_VALIDADO
        assert c.identificador_interno == f"CIU-{c.pk}"
        assert c.requiere_revision_manual is True
        assert c.documento_unico_key is None


@pytest.mark.django_db
def test_idempotente_no_reprocesa_registro_ya_procesado():
    c = _ciudadano(documento=33333333)
    Ciudadano.all_objects.filter(pk=c.pk).update(
        identificador_interno="CIU-PREVIO",
        tipo_registro_identidad=Ciudadano.TIPO_REGISTRO_ESTANDAR,
    )

    _run_backfill()

    c.refresh_from_db()
    # El backfill omite registros que ya tienen identificador_interno
    assert c.identificador_interno == "CIU-PREVIO"


@pytest.mark.django_db
def test_dry_run_no_escribe_en_db():
    c = _ciudadano(documento=None)

    call_command("backfill_identidad", "--dry-run", stdout=StringIO(), stderr=StringIO())

    c.refresh_from_db()
    assert c.identificador_interno is None
    assert c.tipo_registro_identidad == Ciudadano.TIPO_REGISTRO_ESTANDAR  # default
