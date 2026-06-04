"""Tests de política de grupos para el módulo de comunicados."""

import pytest
from django.contrib.auth.models import Group

from core.constants import UserGroups
from users.bootstrap.groups_seed import bootstrap_group_names

pytestmark = pytest.mark.django_db


def test_comunicados_permissions_are_in_bootstrap_seed():
    """Todos los permisos de comunicados deben crearse por bootstrap."""
    assert set(UserGroups.COMUNICADOS_TODOS_PERMISOS).issubset(
        set(bootstrap_group_names())
    )


def test_comunicados_groups_not_created_by_migration_schema():
    """El squash de migraciones no crea grupos; la siembra es responsabilidad del bootstrap."""
    Group.objects.filter(name__in=UserGroups.COMUNICADOS_TODOS_PERMISOS).delete()
    assert not Group.objects.filter(
        name__in=UserGroups.COMUNICADOS_TODOS_PERMISOS
    ).exists()
