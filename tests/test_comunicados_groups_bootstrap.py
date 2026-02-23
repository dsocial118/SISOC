"""Tests de política de grupos para el módulo de comunicados."""

import importlib

import pytest
from django.apps import apps
from django.contrib.auth.models import Group

from core.constants import UserGroups

pytestmark = pytest.mark.django_db

migration_0002 = importlib.import_module(
    "comunicados.migrations.0002_crear_grupos_permisos"
)
migration_0004 = importlib.import_module("comunicados.migrations.0004_create_v2_groups")


def test_comunicados_permissions_are_in_bootstrap_seed():
    """Todos los permisos de comunicados deben crearse por bootstrap."""
    assert set(UserGroups.COMUNICADOS_TODOS_PERMISOS).issubset(
        set(UserGroups.CREATE_GROUPS_SEED)
    )


def test_comunicados_group_migrations_are_noop():
    """Las migraciones históricas no deben crear ni borrar grupos."""
    Group.objects.filter(name__in=UserGroups.COMUNICADOS_TODOS_PERMISOS).delete()

    migration_0002.crear_grupos(apps, None)
    migration_0004.create_groups(apps, None)
    assert not Group.objects.filter(
        name__in=UserGroups.COMUNICADOS_TODOS_PERMISOS
    ).exists()

    Group.objects.create(name=UserGroups.COMUNICADO_CREAR)
    Group.objects.create(name=UserGroups.COMUNICADO_INTERNO_CREAR)
    Group.objects.create(name=UserGroups.COMUNICADO_COMEDORES_CREAR)

    count_before = Group.objects.filter(
        name__in=UserGroups.COMUNICADOS_TODOS_PERMISOS
    ).count()
    migration_0002.eliminar_grupos(apps, None)
    migration_0004.remove_groups(apps, None)
    count_after = Group.objects.filter(
        name__in=UserGroups.COMUNICADOS_TODOS_PERMISOS
    ).count()

    assert count_after == count_before == 3
