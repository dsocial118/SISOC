"""Regresiones de permisos por scope en vistas de nómina."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http import Http404

from admisiones.models.admisiones import Admision
from comedores.models import Comedor
from comedores.views import nomina as nomina_views
from core.constants import UserGroups
from core.models import Provincia
from duplas.models import Dupla

pytestmark = pytest.mark.django_db


def _create_user(username):
    return get_user_model().objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="testpass123",
    )


def _ensure_group(user, group_name):
    group, _ = Group.objects.get_or_create(name=group_name)
    user.groups.add(group)
    return group


def test_get_admision_del_comedor_or_404_bloquea_fuera_de_scope():
    provincia = Provincia.objects.create(nombre="Scope Nomina")
    abogado = _create_user("abogado_nomina_scope")
    tecnico_dupla = _create_user("tecnico_nomina_scope")
    tecnico_ajeno = _create_user("tecnico_nomina_ajeno")
    _ensure_group(tecnico_dupla, UserGroups.TECNICO_COMEDOR)
    _ensure_group(tecnico_ajeno, UserGroups.TECNICO_COMEDOR)

    dupla = Dupla.objects.create(
        nombre="Dupla Scope Nomina",
        estado="Activo",
        abogado=abogado,
    )
    dupla.tecnico.add(tecnico_dupla)

    comedor = Comedor.objects.create(
        nombre="Comedor Scope Nomina",
        provincia=provincia,
        dupla=dupla,
    )
    admision = Admision.objects.create(comedor=comedor)

    with pytest.raises(Http404):
        nomina_views._get_admision_del_comedor_or_404(
            comedor.id, admision.id, tecnico_ajeno
        )

    obj = nomina_views._get_admision_del_comedor_or_404(
        comedor.id, admision.id, tecnico_dupla
    )
    assert obj.id == admision.id
