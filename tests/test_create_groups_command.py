"""Tests para el comando create_groups y la limpieza de grupos huérfanos."""

import importlib

import pytest
from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command

from users.bootstrap.groups_seed import bootstrap_group_names

pytestmark = pytest.mark.django_db

migration_module = importlib.import_module(
    "users.migrations.0012_cleanup_unused_groups"
)
rename_vat_group_module = importlib.import_module(
    "users.migrations.0023_rename_vat_sse_group_to_cfpinet"
)
rename_vat_secondary_groups_module = importlib.import_module(
    "users.migrations.0024_rename_vat_secondary_groups_to_cfp"
)
UNUSED_GROUPS = set(migration_module.UNUSED_GROUPS)


def test_create_groups_creates_canonical_seed_only():
    """El comando debe crear exactamente la semilla canónica declarativa."""
    Group.objects.all().delete()

    call_command("create_groups", verbosity=0)

    created_groups = set(Group.objects.values_list("name", flat=True))
    assert created_groups == set(bootstrap_group_names())
    assert created_groups.isdisjoint(UNUSED_GROUPS)


def test_create_groups_is_idempotent():
    """Ejecutar create_groups dos veces no debe cambiar la cantidad de grupos."""
    Group.objects.all().delete()

    call_command("create_groups", verbosity=0)
    first_count = Group.objects.count()

    call_command("create_groups", verbosity=0)
    second_count = Group.objects.count()

    assert first_count == second_count == len(bootstrap_group_names())


def test_create_groups_assigns_cross_group_role_permissions():
    """La siembra debe resolver permisos `auth.role_*` en una sola corrida."""
    Group.objects.all().delete()

    call_command("create_groups", verbosity=0)

    admin = Group.objects.get(name="Admin")
    export_permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="role_exportar_a_csv",
    )

    assert admin.permissions.filter(pk=export_permission.pk).exists()


def test_create_groups_creates_cfpinet_with_vat_permissions():
    """CFPINET debe conservar el rol VAT SSE y permisos VAT globales."""
    Group.objects.all().delete()

    call_command("create_groups", verbosity=0)

    cfpinet = Group.objects.get(name="CFPINET")

    expected_codes = {
        "role_vat_sse",
        "view_centro",
        "add_centro",
        "change_centro",
        "view_planversioncurricular",
        "add_planversioncurricular",
        "change_planversioncurricular",
        "delete_planversioncurricular",
    }
    group_codes = set(cfpinet.permissions.values_list("codename", flat=True))

    assert expected_codes.issubset(group_codes)


def test_create_groups_creates_cfp_secondary_groups_with_expected_permissions():
    """Los grupos renombrados de VAT deben existir con sus permisos canónicos."""
    Group.objects.all().delete()

    call_command("create_groups", verbosity=0)

    cfp_juridicccion = Group.objects.get(name="CFPJuridicccion")
    cfp = Group.objects.get(name="CFP")

    assert {"role_provincia_vat", "view_centro", "add_centro", "change_centro", "view_planversioncurricular", "add_planversioncurricular"}.issubset(
        set(cfp_juridicccion.permissions.values_list("codename", flat=True))
    )
    assert {
        "role_referentecentrovat",
        "view_centro",
        "add_curso",
        "change_curso",
        "delete_curso",
        "view_comisioncurso",
        "add_comisioncurso",
        "change_comisioncurso",
        "delete_comisioncurso",
        "view_comisionhorario",
        "add_comisionhorario",
        "change_comisionhorario",
        "delete_comisionhorario",
        "view_inscripcion",
        "add_inscripcion",
        "change_inscripcion",
        "add_asistenciasesion",
        "change_asistenciasesion",
    }.issubset(
        set(cfp.permissions.values_list("codename", flat=True))
    )


def test_rename_vat_sse_group_migration_forward_renames_existing_group():
    """La migración debe renombrar el grupo histórico VAT SSE a CFPINET."""
    Group.objects.filter(name__in=["VAT SSE", "CFPINET"]).delete()
    Group.objects.create(name="VAT SSE")

    rename_vat_group_module.rename_vat_sse_group_to_cfpinet(apps, None)

    assert not Group.objects.filter(name="VAT SSE").exists()
    assert Group.objects.filter(name="CFPINET").exists()


def test_rename_vat_secondary_groups_migration_forward_renames_existing_groups():
    """La migración debe renombrar Provincia VAT y ReferenteCentroVAT."""
    Group.objects.filter(
        name__in=["Provincia VAT", "ReferenteCentroVAT", "CFPJuridicccion", "CFP"]
    ).delete()
    Group.objects.create(name="Provincia VAT")
    Group.objects.create(name="ReferenteCentroVAT")

    rename_vat_secondary_groups_module.rename_vat_secondary_groups_to_cfp(apps, None)

    assert not Group.objects.filter(name="Provincia VAT").exists()
    assert not Group.objects.filter(name="ReferenteCentroVAT").exists()
    assert Group.objects.filter(name="CFPJuridicccion").exists()
    assert Group.objects.filter(name="CFP").exists()


def test_cleanup_unused_groups_migration_forward_and_reverse():
    """Forward elimina grupos huérfanos y reverse los recrea."""
    Group.objects.all().delete()
    Group.objects.create(name="Admin")

    for group_name in migration_module.UNUSED_GROUPS:
        Group.objects.get_or_create(name=group_name)

    migration_module.remove_unused_groups(apps, None)
    assert not Group.objects.filter(name__in=migration_module.UNUSED_GROUPS).exists()
    assert Group.objects.filter(name="Admin").exists()

    migration_module.restore_unused_groups(apps, None)
    restored = set(
        Group.objects.filter(name__in=migration_module.UNUSED_GROUPS).values_list(
            "name", flat=True
        )
    )
    assert restored == UNUSED_GROUPS
