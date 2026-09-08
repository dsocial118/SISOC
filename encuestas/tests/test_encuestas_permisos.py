import pytest
from django.contrib.auth.models import Group, Permission, User

from core.permissions.registry import permission_codes_for_bootstrap_group


def _permisos(codenames):
    return Permission.objects.filter(
        content_type__app_label="encuestas", codename__in=codenames
    )


def test_gestor_de_encuestas_incluye_crud_completo():
    codigos = permission_codes_for_bootstrap_group("Gestor de Encuestas")
    assert "encuestas.add_encuesta" in codigos
    assert "encuestas.change_encuesta" in codigos
    assert "encuestas.delete_encuesta" in codigos
    assert "encuestas.view_encuesta" in codigos
    assert "encuestas.ver_resultados" not in codigos


def test_encuestas_resultados_no_incluye_gestion():
    codigos = permission_codes_for_bootstrap_group("Encuestas Resultados")
    assert codigos == ("encuestas.view_encuesta", "encuestas.ver_resultados")


@pytest.mark.django_db
def test_create_groups_deja_permiso_ver_resultados_asignado(django_user_model):
    from django.core.management import call_command

    call_command("create_groups")

    grupo = Group.objects.get(name="Encuestas Resultados")
    assert grupo.permissions.filter(
        content_type__app_label="encuestas", codename="ver_resultados"
    ).exists()

    usuario = django_user_model.objects.create_user(
        username="solo-resultados", password="test1234"
    )
    usuario.groups.add(grupo)
    assert usuario.has_perm("encuestas.ver_resultados")
    assert not usuario.has_perm("encuestas.add_encuesta")


@pytest.mark.django_db
def test_gestor_puede_todo_menos_ver_resultados_por_defecto(django_user_model):
    usuario = django_user_model.objects.create_user(
        username="gestor", password="test1234"
    )
    usuario.user_permissions.add(
        *_permisos(
            [
                "add_encuesta",
                "change_encuesta",
                "delete_encuesta",
                "view_encuesta",
            ]
        )
    )
    assert usuario.has_perm("encuestas.add_encuesta")
    assert not usuario.has_perm("encuestas.ver_resultados")
