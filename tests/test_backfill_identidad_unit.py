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


def _ciudadanos_legacy_sin_normalizar(*items):
    ciudadanos = []
    for item in items:
        defaults = {
            "nombre": "Test",
            "apellido": "Ciudadano",
            "fecha_nacimiento": date(1990, 1, 1),
        }
        defaults.update(item)
        ciudadanos.append(Ciudadano(**defaults))
    Ciudadano.objects.bulk_create(ciudadanos)
    return list(Ciudadano.objects.order_by("pk"))


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
    c1, c2 = _ciudadanos_legacy_sin_normalizar(
        {"nombre": "Ana", "documento": 22222222},
        {"nombre": "Beto", "documento": 22222222},
    )

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

    call_command(
        "backfill_identidad", "--dry-run", stdout=StringIO(), stderr=StringIO()
    )

    c.refresh_from_db()
    assert c.identificador_interno is None
    assert c.tipo_registro_identidad == Ciudadano.TIPO_REGISTRO_ESTANDAR  # default


@pytest.mark.django_db
def test_pasaporte_no_se_clasifica_como_sin_dni():
    """Un pasaporte cargado desde VAT queda con documento=NULL. Antes caía en
    la rama "sin documento", que lo marcaba SIN_DNI y le borraba
    documento_unico_key: eso degradaba en silencio la unicidad del pasaporte."""
    c = _ciudadano(
        tipo_documento=Ciudadano.DOCUMENTO_PASAPORTE,
        documento=None,
        documento_pasaporte="AB123456",
    )
    assert c.documento_unico_key == "PASAPORTE_AB123456"

    _run_backfill()

    c.refresh_from_db()
    assert c.tipo_registro_identidad == Ciudadano.TIPO_REGISTRO_ESTANDAR
    assert c.documento_unico_key == "PASAPORTE_AB123456"
    assert c.requiere_revision_manual is False
    assert c.identificador_interno == f"CIU-{c.pk}"


@pytest.mark.django_db
def test_pasaporte_duplicado_clasifica_como_no_validado():
    """Los pasaportes comparten documento=NULL: agruparlos por esa columna los
    daría a todos como un único grupo duplicado. Se agrupan por
    documento_pasaporte."""
    c1, c2 = _ciudadanos_legacy_sin_normalizar(
        {
            "nombre": "Ana",
            "tipo_documento": Ciudadano.DOCUMENTO_PASAPORTE,
            "documento_pasaporte": "XY999888",
        },
        {
            "nombre": "Beto",
            "tipo_documento": Ciudadano.DOCUMENTO_PASAPORTE,
            "documento_pasaporte": "XY999888",
        },
    )

    _run_backfill()

    for c in (c1, c2):
        c.refresh_from_db()
        assert c.tipo_registro_identidad == Ciudadano.TIPO_REGISTRO_DNI_NO_VALIDADO
        assert c.documento_unico_key is None
        assert c.requiere_revision_manual is True


@pytest.mark.django_db
def test_pasaportes_distintos_no_se_toman_como_duplicados():
    c1, c2 = _ciudadanos_legacy_sin_normalizar(
        {
            "nombre": "Ana",
            "tipo_documento": Ciudadano.DOCUMENTO_PASAPORTE,
            "documento_pasaporte": "AA111111",
        },
        {
            "nombre": "Beto",
            "tipo_documento": Ciudadano.DOCUMENTO_PASAPORTE,
            "documento_pasaporte": "BB222222",
        },
    )

    _run_backfill()

    for c, esperado in ((c1, "PASAPORTE_AA111111"), (c2, "PASAPORTE_BB222222")):
        c.refresh_from_db()
        assert c.tipo_registro_identidad == Ciudadano.TIPO_REGISTRO_ESTANDAR
        assert c.documento_unico_key == esperado


@pytest.mark.django_db
def test_pasaporte_historico_en_documento_sigue_tratandose_como_numerico():
    """Los pasaportes previos a documento_pasaporte guardaron su número en
    `documento`. Deben conservar su clave, no pasar por la rama nueva."""
    c = _ciudadano(
        tipo_documento=Ciudadano.DOCUMENTO_PASAPORTE,
        documento=44555666,
    )

    _run_backfill()

    c.refresh_from_db()
    assert c.tipo_registro_identidad == Ciudadano.TIPO_REGISTRO_ESTANDAR
    assert c.documento_unico_key == "PASAPORTE_44555666"
