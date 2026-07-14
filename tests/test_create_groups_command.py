"""Tests para el comando create_groups y la limpieza de grupos huérfanos."""

import importlib

import pytest
from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command

from users.bootstrap.groups_seed import bootstrap_group_names

pytestmark = pytest.mark.django_db

migration_module = importlib.import_module("users.migrations.0001_squashed_0028")
rename_vat_group_module = migration_module
rename_vat_secondary_groups_module = migration_module
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
        "view_comision",
        "view_comisioncurso",
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

    assert {
        "role_provincia_vat",
        "view_centro",
        "add_centro",
        "change_centro",
        "view_planversioncurricular",
        "add_planversioncurricular",
    }.issubset(set(cfp_juridicccion.permissions.values_list("codename", flat=True)))
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
    }.issubset(set(cfp.permissions.values_list("codename", flat=True)))


def test_create_groups_creates_inet_provincia_with_expected_permissions():
    """INET_PROVINCIA debe tener rol provincial INET y permisos VAT base."""
    Group.objects.all().delete()

    call_command("create_groups", verbosity=0)

    inet_provincia = Group.objects.get(name="INET_PROVINCIA")
    group_codes = set(inet_provincia.permissions.values_list("codename", flat=True))

    assert {
        "role_inet_provincia",
        "view_centro",
        "add_centro",
        "change_centro",
        "view_planversioncurricular",
        "add_planversioncurricular",
        "view_comision",
        "view_comisioncurso",
    }.issubset(group_codes)
    # Permisos removidos del perfil provincial INET.
    assert group_codes.isdisjoint(
        {
            "role_provincia_vat",
            "change_planversioncurricular",
            "view_ofertainstitucional",
            "change_ofertainstitucional",
            "change_comision",
        }
    )


def test_create_groups_creates_inet_admin_visualizador_readonly():
    """INET Admin Visualizador debe ser solo lectura sobre VAT."""
    Group.objects.all().delete()

    call_command("create_groups", verbosity=0)

    grupo = Group.objects.get(name="INET Admin Visualizador")
    group_codes = set(grupo.permissions.values_list("codename", flat=True))

    assert {
        "role_inet_admin_visualizador",
        "view_centro",
        "view_curso",
        "view_comision",
        "view_comisioncurso",
        "view_comisionhorario",
        "view_planversioncurricular",
    }.issubset(group_codes)
    assert not {"view_inscripcion", "view_inscripcionoferta"} & group_codes
    assert not any(
        code.startswith(("add_", "change_", "delete_")) for code in group_codes
    )


def test_create_groups_creates_inet_admin_general_with_full_vat_management():
    """INET Admin General debe tener rol SSE + gestion VAT completa."""
    Group.objects.all().delete()

    call_command("create_groups", verbosity=0)

    grupo = Group.objects.get(name="INET Admin General")
    group_codes = set(grupo.permissions.values_list("codename", flat=True))

    assert {
        "role_vat_sse",
        "role_admin_inet_general",
        "view_centro",
        "add_centro",
        "change_centro",
        "view_curso",
        "add_curso",
        "change_curso",
        "delete_curso",
        "view_comision",
        "change_comision",
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
        "view_planversioncurricular",
        "add_planversioncurricular",
    }.issubset(group_codes)


def test_reconcile_migration_removes_stale_inet_provincia_permissions():
    """La migración de reconciliación deja INET_PROVINCIA exacto, quitando
    permisos administrativos que ya no corresponden al perfil."""
    reconcile_module = importlib.import_module(
        "users.migrations.0039_reconcile_vat_admin_groups"
    )
    Group.objects.filter(name="INET_PROVINCIA").delete()
    inet_provincia = Group.objects.create(name="INET_PROVINCIA")
    stale = Permission.objects.get(
        content_type__app_label="VAT",
        codename="change_comision",
    )
    inet_provincia.permissions.add(stale)

    reconcile_module.reconcile_vat_admin_groups(apps, None)

    group_codes = set(inet_provincia.permissions.values_list("codename", flat=True))
    assert "change_comision" not in group_codes
    assert {"role_inet_provincia", "view_comisioncurso"}.issubset(group_codes)


def test_reconcile_migration_preserves_legacy_group_role_permission():
    """La migración conserva el permiso sintético legado creado por IAM."""
    reconcile_module = importlib.import_module(
        "users.migrations.0039_reconcile_vat_admin_groups"
    )
    Group.objects.filter(name="CFP").delete()
    cfp = Group.objects.create(name="CFP")
    group_ct = ContentType.objects.get(app_label="auth", model="group")
    legacy_permission, _ = Permission.objects.get_or_create(
        content_type=group_ct,
        codename="role_cfp",
        defaults={"name": "CFP"},
    )
    legacy_permission.name = "CFP"
    legacy_permission.save(update_fields=["name"])
    cfp.permissions.add(legacy_permission)

    reconcile_module.reconcile_vat_admin_groups(apps, None)

    cfp.refresh_from_db()
    assert cfp.permissions.filter(pk=legacy_permission.pk).exists()


def test_reconcile_migration_creates_admin_inet_general_role_permission():
    """El permiso de rol nuevo `role_admin_inet_general` se crea on-demand."""
    reconcile_module = importlib.import_module(
        "users.migrations.0039_reconcile_vat_admin_groups"
    )
    Permission.objects.filter(codename="role_admin_inet_general").delete()

    reconcile_module.reconcile_vat_admin_groups(apps, None)

    grupo = Group.objects.get(name="INET Admin General")
    assert grupo.permissions.filter(codename="role_admin_inet_general").exists()


def test_create_groups_creates_cfp_revisor_readonly_group():
    """CFPRevisor debe existir para visualizacion acotada sin permisos de gestion."""
    Group.objects.all().delete()

    call_command("create_groups", verbosity=0)

    cfp_revisor = Group.objects.get(name="CFPRevisor")
    group_codes = set(cfp_revisor.permissions.values_list("codename", flat=True))

    assert {"role_revisorcentrovat", "view_centro", "view_comisioncurso"}.issubset(
        group_codes
    )
    assert not any(
        code.startswith(("add_", "change_", "delete_")) for code in group_codes
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
