import pytest
from django.contrib.auth.models import Group, User

from core.constants import UserGroups
from centrodefamilia.forms import CentroForm

GRUPO_ACTUAL = UserGroups.CDF_REFERENTE_CENTRO
GRUPO_LEGACY = "ReferenteCentro"


def _usuario_en_grupo(username, grupo_nombre=None):
    user = User.objects.create_user(username=username, password="test1234")
    if grupo_nombre:
        grupo, _ = Group.objects.get_or_create(name=grupo_nombre)
        user.groups.add(grupo)
    return user


@pytest.mark.django_db
def test_referente_incluye_usuarios_del_grupo_cdf_referente_centro():
    """Regresión: el form filtraba solo por el grupo legacy "ReferenteCentro" y
    los usuarios generados con el grupo actual no aparecían en el campo."""
    referente = _usuario_en_grupo("ref-cdf", GRUPO_ACTUAL)

    queryset = CentroForm().fields["referente"].queryset

    assert referente in queryset


@pytest.mark.django_db
def test_referente_conserva_usuarios_del_grupo_legacy():
    referente_legacy = _usuario_en_grupo("ref-legacy", GRUPO_LEGACY)

    queryset = CentroForm().fields["referente"].queryset

    assert referente_legacy in queryset


@pytest.mark.django_db
def test_referente_excluye_usuarios_sin_grupo_de_referente():
    otro = _usuario_en_grupo("sin-grupo")

    queryset = CentroForm().fields["referente"].queryset

    assert otro not in queryset


@pytest.mark.django_db
def test_referente_en_ambos_grupos_aparece_una_sola_vez():
    referente = _usuario_en_grupo("ref-doble", GRUPO_ACTUAL)
    grupo_legacy, _ = Group.objects.get_or_create(name=GRUPO_LEGACY)
    referente.groups.add(grupo_legacy)

    queryset = CentroForm().fields["referente"].queryset

    assert list(queryset.filter(pk=referente.pk)) == [referente]
