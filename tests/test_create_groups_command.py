"""Tests para el comando create_groups y la limpieza de grupos huérfanos."""

import importlib

import pytest
from django.apps import apps
from django.contrib.auth.models import Group
from django.core.management import call_command

from core.constants import UserGroups

pytestmark = pytest.mark.django_db

migration_module = importlib.import_module("users.migrations.0012_cleanup_unused_groups")
UNUSED_GROUPS = set(migration_module.UNUSED_GROUPS)


def test_create_groups_creates_canonical_seed_only():
    """El comando debe crear exactamente la semilla canónica definida en constants."""
    Group.objects.all().delete()

    call_command("create_groups", verbosity=0)

    created_groups = set(Group.objects.values_list("name", flat=True))
    assert created_groups == set(UserGroups.CREATE_GROUPS_SEED)
    assert created_groups.isdisjoint(UNUSED_GROUPS)


def test_create_groups_is_idempotent():
    """Ejecutar create_groups dos veces no debe cambiar la cantidad de grupos."""
    Group.objects.all().delete()

    call_command("create_groups", verbosity=0)
    first_count = Group.objects.count()

    call_command("create_groups", verbosity=0)
    second_count = Group.objects.count()

    assert first_count == second_count == len(UserGroups.CREATE_GROUPS_SEED)


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
