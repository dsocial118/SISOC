"""Pruebas del comando controlado de corrección del issue #2272."""

from __future__ import annotations

import pytest
from django.core.management.base import CommandError
from django.core.management import call_command
from django.utils import timezone

from admisiones.management.commands.corregir_expedientes_issue_2272 import Command
from admisiones.models.admisiones import Admision, AdmisionHistorial


pytestmark = pytest.mark.django_db


def _configurar_manifiesto(command, tmp_path, contenido):
    manifest_path = tmp_path / "correcciones.csv"
    manifest_path.write_text(contenido, encoding="utf-8")
    command.manifest_sha256 = command._calcular_checksum(manifest_path.read_bytes())
    command.get_manifest_path = lambda: manifest_path


def test_manifiesto_versionado_tiene_correcciones_validas_y_unicas():
    command = Command()

    resultado = command._cargar_y_validar_manifiesto()

    assert len(resultado.correcciones) == 470
    assert not resultado.advertencias
    assert not resultado.errores


def test_preflight_rechaza_colision_con_admision_fuera_del_manifiesto(tmp_path):
    Admision.objects.create(
        pk=100,
        num_expediente="EX-2026-123456789- -APN-DDNAYF#MCH",
    )
    Admision.objects.create(
        pk=200,
        num_expediente="EX-2026-987654321- -APN-DDNAYF#MCH",
    )
    command = Command()
    _configurar_manifiesto(
        command,
        tmp_path,
        "ID ADMISION,Expediente Correcto\n" "100,EX-2026-987654321- -APN-DDNAYF#MCH\n",
    )

    resultado = command._preflight(database="default", bloquear_filas=False)

    assert any(
        "ya está asociado a otra admisión" in error for error in resultado.errores
    )


def test_apply_libera_un_conflicto_autorizado_del_csv(tmp_path):
    numero_corregido = "EX-2026-987654321- -APN-DDNAYF#MCH"
    origen = Admision.objects.create(
        pk=1627,
        num_expediente=numero_corregido,
        legales_num_if="EX-2025-111111111- -APN-DDNAYF#MCH",
    )
    destino = Admision.objects.create(
        pk=2072,
        num_expediente="EX-2025-222222222- -APN-DDNAYF#MCH",
        legales_num_if="EX-2025-333333333- -APN-DDNAYF#MCH",
    )
    command = Command()
    _configurar_manifiesto(
        command,
        tmp_path,
        "ID ADMISION,Expediente Correcto\n" f"2072,{numero_corregido}\n",
    )

    command.handle(apply=True, database="default")

    origen.refresh_from_db()
    destino.refresh_from_db()
    assert (origen.num_expediente, origen.legales_num_if) == (None, None)
    assert (destino.num_expediente, destino.legales_num_if) == (
        numero_corregido,
        numero_corregido,
    )
    assert AdmisionHistorial.objects.filter(admision=origen).count() == 2
    command.handle(apply=False, database="default", verify=True)


def test_preflight_rechaza_un_conflicto_distinto_al_autorizado(tmp_path):
    numero_corregido = "EX-2026-987654321- -APN-DDNAYF#MCH"
    Admision.objects.create(pk=999, num_expediente=numero_corregido)
    Admision.objects.create(pk=2072)
    command = Command()
    _configurar_manifiesto(
        command,
        tmp_path,
        "ID ADMISION,Expediente Correcto\n" f"2072,{numero_corregido}\n",
    )

    with pytest.raises(CommandError):
        command.handle(apply=False, database="default")


def test_preflight_conserva_todos_los_propietarios_de_un_expediente(tmp_path):
    numero_compartido = "EX-2026-987654321- -APN-DDNAYF#MCH"
    Admision.objects.create(pk=100, num_expediente=numero_compartido)
    Admision.objects.create(pk=200, num_expediente=numero_compartido)
    command = Command()
    _configurar_manifiesto(
        command,
        tmp_path,
        "ID ADMISION,Expediente Correcto\n" f"200,{numero_compartido}\n",
    )

    with pytest.raises(CommandError):
        command.handle(apply=False, database="default")


def test_preflight_admite_permutacion_de_expedientes_del_manifiesto(tmp_path):
    numero_a = "EX-2026-111111111- -APN-DDNAYF#MCH"
    numero_b = "EX-2026-222222222- -APN-DDNAYF#MCH"
    Admision.objects.create(pk=100, num_expediente=numero_a)
    Admision.objects.create(pk=200, num_expediente=numero_b)
    command = Command()
    _configurar_manifiesto(
        command,
        tmp_path,
        "ID ADMISION,Expediente Correcto\n" f"100,{numero_b}\n" f"200,{numero_a}\n",
    )

    command.handle(apply=True, database="default")

    assert Admision.objects.get(pk=100).num_expediente == numero_b
    assert Admision.objects.get(pk=200).num_expediente == numero_a


def test_preflight_admite_ciclo_de_tres_expedientes_del_manifiesto(tmp_path):
    numeros = [
        "EX-2026-111111111- -APN-DDNAYF#MCH",
        "EX-2026-222222222- -APN-DDNAYF#MCH",
        "EX-2026-333333333- -APN-DDNAYF#MCH",
    ]
    for admision_id, numero in zip((100, 200, 300), numeros):
        Admision.objects.create(pk=admision_id, num_expediente=numero)
    command = Command()
    _configurar_manifiesto(
        command,
        tmp_path,
        "ID ADMISION,Expediente Correcto\n"
        f"100,{numeros[1]}\n"
        f"200,{numeros[2]}\n"
        f"300,{numeros[0]}\n",
    )

    command.handle(apply=False, database="default")


def test_apply_sobrescribe_tecnicos_legales_y_registra_historial(tmp_path):
    admision = Admision.objects.create(
        pk=100,
        num_expediente="EX-2025-111111111- -APN-DDNAYF#MCH",
        legales_num_if="EX-2025-222222222- -APN-DDNAYF#MCH",
    )
    command = Command()
    numero_corregido = "EX-2026-987654321- -APN-DDNAYF#MCH"
    _configurar_manifiesto(
        command,
        tmp_path,
        "ID ADMISION,Expediente Correcto\n" f"{admision.pk},{numero_corregido}\n",
    )

    command.handle(apply=True, database="default")

    admision.refresh_from_db()
    assert admision.num_expediente == numero_corregido
    assert admision.legales_num_if == numero_corregido
    assert admision.modificado == timezone.localdate()
    historial = AdmisionHistorial.objects.filter(admision=admision)
    assert historial.count() == 2
    assert set(historial.values_list("campo", flat=True)) == {
        "Número de expediente",
        "Expediente en Legales",
    }


def test_verify_rechaza_si_legales_no_coincide_con_el_manifiesto(tmp_path):
    numero_corregido = "EX-2026-987654321- -APN-DDNAYF#MCH"
    Admision.objects.create(
        pk=100,
        num_expediente=numero_corregido,
        legales_num_if="EX-2025-222222222- -APN-DDNAYF#MCH",
    )
    command = Command()
    _configurar_manifiesto(
        command,
        tmp_path,
        "ID ADMISION,Expediente Correcto\n" f"100,{numero_corregido}\n",
    )

    with pytest.raises(CommandError):
        command.handle(apply=False, database="default", verify=True)


def test_verify_confirma_campos_tecnicos_y_legales(tmp_path):
    numero_corregido = "EX-2026-987654321- -APN-DDNAYF#MCH"
    Admision.objects.create(
        pk=100,
        num_expediente=numero_corregido,
        legales_num_if=numero_corregido,
    )
    command_instance = Command()
    _configurar_manifiesto(
        command_instance,
        tmp_path,
        "ID ADMISION,Expediente Correcto\n" f"100,{numero_corregido}\n",
    )

    call_command(command_instance, "--verify", "--database", "default")


def test_parser_rechaza_apply_y_verify_juntos():
    parser = Command().create_parser("manage.py", "corregir_expedientes_issue_2272")

    with pytest.raises(CommandError):
        parser.parse_args(["--apply", "--verify"])


def test_apply_no_modifica_datos_si_el_preflight_falla(tmp_path):
    admision = Admision.objects.create(
        pk=100,
        num_expediente="EX-2025-111111111- -APN-DDNAYF#MCH",
        legales_num_if="EX-2025-111111111- -APN-DDNAYF#MCH",
    )
    command = Command()
    _configurar_manifiesto(
        command,
        tmp_path,
        "ID ADMISION,Expediente Correcto\n" "100,EX-2026-123- -APN-DDNAYF#MCH\n",
    )

    with pytest.raises(CommandError):
        command.handle(apply=True, database="default")

    admision.refresh_from_db()
    assert admision.num_expediente == "EX-2025-111111111- -APN-DDNAYF#MCH"
    assert admision.legales_num_if == "EX-2025-111111111- -APN-DDNAYF#MCH"
    assert not AdmisionHistorial.objects.filter(admision=admision).exists()
