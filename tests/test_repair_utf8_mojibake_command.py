from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from ciudadanos.models import Ciudadano
from centrodeinfancia.models import CentroDeInfancia, NominaCentroInfancia
from core.models import Provincia


@pytest.mark.django_db
def test_command_es_dry_run_por_defecto_y_no_expone_valores():
    ciudadano = Ciudadano.objects.create(
        apellido="Mu\u00c3\u00b1oz",
        nombre="Ángel Jos\u00c3\u00a9",
        documento=45000001,
    )
    output = StringIO()

    call_command(
        "repair_utf8_mojibake",
        "--target",
        "ciudadano",
        stdout=output,
    )

    ciudadano.refresh_from_db()
    assert ciudadano.apellido == "Mu\u00c3\u00b1oz"
    assert ciudadano.nombre == "Ángel Jos\u00c3\u00a9"
    assert "DRY-RUN" in output.getvalue()
    assert "1 filas con cambios reversibles" in output.getvalue()
    assert "Mu\u00c3\u00b1oz" not in output.getvalue()
    assert "Ángel Jos\u00c3\u00a9" not in output.getvalue()


@pytest.mark.django_db
def test_command_apply_repara_por_lotes_y_es_idempotente():
    ciudadano = Ciudadano.objects.create(
        apellido="Dell \u00c3\u201clio",
        nombre="Jos\u00c3\u0192\u00c2\u00a9",
        documento=45000002,
    )

    call_command(
        "repair_utf8_mojibake",
        "--apply",
        "--target",
        "ciudadano",
        "--batch-size",
        "1",
        stdout=StringIO(),
    )

    ciudadano.refresh_from_db()
    assert ciudadano.apellido == "Dell Ólio"
    assert ciudadano.nombre == "José"

    second_run = StringIO()
    call_command(
        "repair_utf8_mojibake",
        "--apply",
        "--target",
        "ciudadano",
        stdout=second_run,
    )
    assert "0 filas con cambios reversibles" in second_run.getvalue()


@pytest.mark.django_db
def test_command_puede_limitarse_a_nomina_y_campo():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    centro = CentroDeInfancia.objects.create(nombre="CDI Encoding", provincia=provincia)
    ciudadano = Ciudadano.objects.create(
        apellido="Ciudadano correcto",
        nombre="Nombre correcto",
        documento=45000003,
    )
    nomina = NominaCentroInfancia.objects.create(
        centro=centro,
        ciudadano=ciudadano,
        apellido="Mu\u00c3\u00b1oz",
        nombre="Nombre \u00c3",
    )

    call_command(
        "repair_utf8_mojibake",
        "--apply",
        "--target",
        "nomina_cdi",
        "--field",
        "apellido",
        stdout=StringIO(),
    )

    nomina.refresh_from_db()
    ciudadano.refresh_from_db()
    assert nomina.apellido == "Muñoz"
    assert nomina.nombre == "Nombre \u00c3"
    assert ciudadano.apellido == "Ciudadano correcto"


@pytest.mark.django_db
def test_audit_command_acepta_campo_explicito_y_no_expone_valores():
    Ciudadano.objects.create(
        apellido="Mu\u00c3\u00b1oz",
        nombre="Nombre correcto",
        documento=45000004,
    )
    output = StringIO()

    call_command(
        "audit_utf8_mojibake",
        "--field",
        "ciudadanos.Ciudadano.apellido",
        stdout=output,
    )

    assert "1 reparables" in output.getvalue()
    assert "Mu\u00c3\u00b1oz" not in output.getvalue()


def test_audit_command_rechaza_campos_no_textuales():
    with pytest.raises(CommandError, match="no es CharField ni TextField"):
        call_command(
            "audit_utf8_mojibake",
            "--field",
            "ciudadanos.Ciudadano.documento",
            stdout=StringIO(),
        )
