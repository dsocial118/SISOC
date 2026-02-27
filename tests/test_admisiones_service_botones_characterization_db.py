"""Caracterización semi-integrada de botones disponibles en admisiones."""

from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from admisiones.services import admisiones_service as module
from comedores.models import Comedor
from core.constants import UserGroups
from core.models import Provincia
from duplas.models import Dupla

pytestmark = pytest.mark.django_db


def _create_user_with_group(username, group_name):
    user = get_user_model().objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="testpass123",
    )
    group, _ = Group.objects.get_or_create(name=group_name)
    user.groups.add(group)
    return user


def _create_user(username):
    return get_user_model().objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="testpass123",
    )


def _create_comedor_with_dupla(*, abogado, tecnico=None, estado_dupla="Activo"):
    provincia = Provincia.objects.create(
        nombre=f"Provincia {Provincia.objects.count()+1}"
    )
    dupla = Dupla.objects.create(
        nombre="Dupla Test", estado=estado_dupla, abogado=abogado
    )
    if tecnico is not None:
        dupla.tecnico.add(tecnico)
    comedor = Comedor.objects.create(
        nombre="Comedor Permisos", provincia=provincia, dupla=dupla
    )
    return comedor, dupla


def _admision(**overrides):
    base = {
        "numero_disposicion": None,
        "enviado_acompaniamiento": False,
        "estado_legales": "",
        "estado_admision": "",
        "num_expediente": None,
        "numero_if_tecnico": None,
        "enviado_legales": False,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _informe(**overrides):
    base = {
        "estado": "Iniciado",
        "estado_formulario": "borrador",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.mark.parametrize(
    ("admision", "informe_tecnico", "mostrar_complementario", "esperados"),
    [
        (
            _admision(estado_admision="documentacion_aprobada", num_expediente=None),
            None,
            False,
            ["caratular_expediente"],
        ),
        (
            _admision(estado_admision="expediente_cargado", num_expediente="EXP-1"),
            None,
            False,
            ["crear_informe_tecnico"],
        ),
        (
            _admision(
                estado_admision="informe_tecnico_finalizado", num_expediente="EXP-1"
            ),
            _informe(estado="Docx generado"),
            False,
            ["revisar_informe_tecnico"],
        ),
        (
            _admision(
                estado_admision="informe_tecnico_aprobado",
                num_expediente="EXP-1",
                numero_if_tecnico=None,
            ),
            _informe(estado="Validado"),
            False,
            ["if_informe_tecnico"],
        ),
        (
            _admision(
                estado_admision="if_informe_tecnico_cargado",
                num_expediente="EXP-1",
                enviado_legales=False,
            ),
            _informe(estado="Validado"),
            False,
            ["mandar_a_legales"],
        ),
        (
            _admision(
                estado_admision="informe_tecnico_en_proceso",
                num_expediente="EXP-1",
            ),
            _informe(estado="Iniciado", estado_formulario="borrador"),
            False,
            ["editar_informe_tecnico"],
        ),
        (
            _admision(
                estado_admision="cualquier_estado",
                num_expediente="EXP-1",
            ),
            _informe(estado="A subsanar", estado_formulario="final"),
            False,
            ["editar_informe_tecnico"],
        ),
    ],
)
def test_get_botones_disponibles_tecnico_matriz_estados(
    admision, informe_tecnico, mostrar_complementario, esperados
):
    tecnico = _create_user_with_group("tecnico_botones", UserGroups.TECNICO_COMEDOR)

    botones = module.AdmisionService._get_botones_disponibles(
        admision,
        informe_tecnico,
        mostrar_complementario,
        user=tecnico,
    )

    assert botones == esperados


def test_get_botones_disponibles_abogado_docx_editado_puede_ver_informe():
    abogado = _create_user_with_group("abogado_botones", UserGroups.ABOGADO_DUPLA)
    admision = _admision(
        estado_admision="informe_tecnico_docx_editado",
        num_expediente="EXP-22",
    )
    informe_tecnico = _informe(estado="Docx editado")

    botones = module.AdmisionService._get_botones_disponibles(
        admision,
        informe_tecnico,
        mostrar_informe_complementario=True,
        user=abogado,
    )

    assert botones == ["ver_informe_tecnico"]


def test_get_botones_disponibles_preserva_orden_en_combinacion_tecnica():
    tecnico = _create_user_with_group("tecnico_orden", UserGroups.TECNICO_COMEDOR)
    admision = _admision(
        numero_disposicion="DI-1",
        enviado_acompaniamiento=False,
        estado_legales="A Rectificar",
        estado_admision="if_informe_tecnico_cargado",
        num_expediente="EXP-33",
        enviado_legales=False,
    )
    informe_tecnico = _informe(estado="Validado")

    botones = module.AdmisionService._get_botones_disponibles(
        admision,
        informe_tecnico,
        mostrar_informe_complementario=True,
        user=tecnico,
    )

    assert botones == [
        "comenzar_acompaniamiento",
        "rectificar_documentacion",
        "mandar_a_legales",
        "informe_tecnico_complementario",
    ]


def test_get_botones_disponibles_sin_roles_no_expone_acciones_tecnicas_ni_abogado():
    user = get_user_model().objects.create_user(
        username="sin_roles_botones",
        email="sin_roles@example.com",
        password="testpass123",
    )
    admision = _admision(
        numero_disposicion="DI-2",
        estado_legales="A Rectificar",
        estado_admision="if_informe_tecnico_cargado",
        num_expediente="EXP-44",
    )
    informe_tecnico = _informe(estado="Validado")

    botones = module.AdmisionService._get_botones_disponibles(
        admision,
        informe_tecnico,
        mostrar_informe_complementario=True,
        user=user,
    )

    assert botones == [
        "comenzar_acompaniamiento",
        "rectificar_documentacion",
    ]


def test_permiso_helpers_dupla_con_datos_reales():
    tecnico = _create_user_with_group(
        "tecnico_permiso_real", UserGroups.TECNICO_COMEDOR
    )
    abogado = _create_user("abogado_permiso_real")
    otro = _create_user("otro_permiso_real")
    comedor, _dupla = _create_comedor_with_dupla(abogado=abogado, tecnico=tecnico)

    assert (
        module.AdmisionService._verificar_permiso_tecnico_dupla(tecnico, comedor)
        is True
    )
    assert module.AdmisionService._verificar_permiso_dupla(tecnico, comedor) is True
    assert module.AdmisionService._verificar_permiso_dupla(abogado, comedor) is True
    assert module.AdmisionService._verificar_permiso_dupla(otro, comedor) is False


def test_permiso_helpers_dupla_inactiva_y_sin_grupo_rechaza():
    tecnico_sin_grupo = _create_user("tecnico_sin_grupo")
    abogado = _create_user("abogado_inactivo")
    comedor_inactivo, _dupla = _create_comedor_with_dupla(
        abogado=abogado,
        tecnico=tecnico_sin_grupo,
        estado_dupla="Inactivo",
    )

    assert (
        module.AdmisionService._verificar_permiso_tecnico_dupla(
            tecnico_sin_grupo, comedor_inactivo
        )
        is False
    )
    assert (
        module.AdmisionService._verificar_permiso_dupla(abogado, comedor_inactivo)
        is False
    )
    assert (
        module.AdmisionService._verificar_permiso_dupla(tecnico_sin_grupo, None)
        is False
    )
