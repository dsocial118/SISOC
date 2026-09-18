"""Tests de los tres roles de DataCalle (decisión 2026-09-18)."""

import pytest
from django.contrib.auth import get_user_model

from core.models import Provincia
from users.models import Profile


@pytest.fixture
def provincia(db):
    return Provincia.objects.create(nombre="Córdoba")


def test_existen_los_tres_roles_del_documento_funcional():
    codigos = [codigo for codigo, _ in Profile.DataCalleRol.choices]
    assert codigos == ["administrador", "coordinador", "entrevistador"]


def test_las_etiquetas_son_las_del_documento_funcional():
    etiquetas = dict(Profile.DataCalleRol.choices)
    assert etiquetas["administrador"] == "Administrador Nacional"
    assert etiquetas["coordinador"] == "Coordinador Provincial"
    assert etiquetas["entrevistador"] == "Relevador"
