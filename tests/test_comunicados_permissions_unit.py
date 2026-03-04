"""Tests unitarios de permisos para el módulo de comunicados."""

import pytest
from django.contrib.auth.models import Group, User

from comunicados.permissions import is_admin
from core.constants import UserGroups

pytestmark = pytest.mark.django_db


def test_is_admin_devuelve_true_para_superuser():
    user = User.objects.create_superuser("admin_root", "admin_root@test.com", "test")

    assert is_admin(user) is True


@pytest.mark.parametrize("group_name", [UserGroups.ADMIN, UserGroups.ADMINISTRADOR])
def test_is_admin_devuelve_true_para_grupo_admin(group_name):
    user = User.objects.create_user(
        username=f"user_{group_name.lower()}",
        email=f"user_{group_name.lower()}@test.com",
        password="testpass123",
    )
    group, _ = Group.objects.get_or_create(name=group_name)
    user.groups.add(group)

    assert is_admin(user) is True


def test_is_admin_devuelve_false_sin_grupo_admin():
    user = User.objects.create_user(
        username="user_no_admin",
        email="user_no_admin@test.com",
        password="testpass123",
    )

    assert is_admin(user) is False
