"""Separación de permisos entre Dashboard de Cupos y Reporte (tk #2254)."""

import importlib

import pytest
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from core.models import Provincia
from users.models import Profile


def _permiso(codename, app_label="celiaquia", model="expediente"):
    """Siembra el permiso si la base de tests no corrió el `post_migrate` que
    crea los declarados en `Meta.permissions` ni las data migrations de roles."""
    try:
        return Permission.objects.get(
            content_type__app_label=app_label,
            codename=codename,
        )
    except Permission.DoesNotExist:
        content_type = ContentType.objects.get_or_create(
            app_label=app_label, model=model
        )[0]
        return Permission.objects.create(
            content_type=content_type,
            codename=codename,
            name=codename,
        )


def _rol(codename):
    return _permiso(codename, app_label="auth", model="user")


def _usuario(username, *codenames):
    user = User.objects.create_user(username=username, password="pass")
    for codename in codenames:
        user.user_permissions.add(_permiso(codename))
    Profile.objects.get_or_create(user=user)
    return user


@pytest.mark.django_db
def test_solo_reporte_no_habilita_el_dashboard(client):
    """El caso del ticket: la provincia ve el Reporte pero no el Dashboard."""
    user = _usuario("solo_reporte", "view_expediente", "view_reporte_provincias")

    client.force_login(user)
    assert client.get(reverse("reporter_provincias")).status_code == 200
    assert client.get(reverse("cupo_dashboard")).status_code == 403


@pytest.mark.django_db
def test_solo_dashboard_no_habilita_el_reporte(client):
    """La separación funciona en las dos direcciones."""
    user = _usuario("solo_dashboard", "view_expediente", "view_cupo_dashboard")

    client.force_login(user)
    assert client.get(reverse("cupo_dashboard")).status_code == 200
    assert client.get(reverse("reporter_provincias")).status_code == 403


@pytest.mark.django_db
def test_view_expediente_ya_no_abre_ninguno_de_los_dos(client):
    """Antes `view_expediente` habilitaba ambos módulos; ahora ninguno."""
    user = _usuario("solo_expedientes", "view_expediente")

    client.force_login(user)
    assert client.get(reverse("cupo_dashboard")).status_code == 403
    assert client.get(reverse("reporter_provincias")).status_code == 403
    # El listado de expedientes no se ve afectado.
    assert client.get(reverse("expediente_list")).status_code == 200


@pytest.mark.django_db
def test_subrutas_de_cupo_exigen_el_permiso_de_dashboard(client):
    """El detalle por provincia y las acciones de cupo son parte del Dashboard:
    no deben quedar accesibles por deep link."""
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    user = _usuario("solo_reporte_2", "view_expediente", "view_reporte_provincias")

    client.force_login(user)
    rutas = [
        reverse("cupo_provincia_detail", args=[provincia.pk]),
        reverse("cupo_legajo_baja", args=[provincia.pk, 1]),
        reverse("cupo_legajo_suspender", args=[provincia.pk, 1]),
        reverse("cupo_legajo_reactivar", args=[provincia.pk, 1]),
    ]
    for ruta in rutas:
        assert client.get(ruta).status_code == 403, ruta


@pytest.mark.django_db
def test_superusuario_conserva_acceso_a_ambos(client):
    user = User.objects.create_user(
        username="admin", password="pass", is_superuser=True
    )
    Profile.objects.get_or_create(user=user)

    client.force_login(user)
    assert client.get(reverse("cupo_dashboard")).status_code == 200
    assert client.get(reverse("reporter_provincias")).status_code == 200


@pytest.mark.django_db
def test_regla_de_siembra_por_tipo_de_grupo():
    """Regla que aplica la data migration 0006: sólo el grupo estrictamente
    provincial pierde el Dashboard. El mixto (provincial + rol de Nación) y el
    que no declara rol provincial lo conservan."""
    migracion = importlib.import_module(
        "celiaquia.migrations.0006_seed_permisos_dashboard_reporte"
    )
    es_provincial_puro = migracion._es_estrictamente_provincial

    provincial = Group.objects.create(name="ProvinciaCeliaquia")
    provincial.permissions.add(_rol("role_provinciaceliaquia"))

    mixto = Group.objects.create(name="Celiaquia Total")
    mixto.permissions.add(_rol("role_provinciaceliaquia"))
    mixto.permissions.add(_rol("role_coordinadorceliaquia"))

    nacion = Group.objects.create(name="TecnicoCeliaquia")
    nacion.permissions.add(_rol("role_tecnicoceliaquia"))

    visualizacion = Group.objects.create(name="Celiaquia Visualizacion")
    visualizacion.permissions.add(_permiso("view_expediente"))

    assert es_provincial_puro(provincial, "permissions") is True
    assert es_provincial_puro(mixto, "permissions") is False
    assert es_provincial_puro(nacion, "permissions") is False
    assert es_provincial_puro(visualizacion, "permissions") is False


@pytest.mark.django_db
def test_grupo_con_solo_reporte_ve_el_menu_de_celiaquia(client):
    """El menú lateral debe mostrarse aunque el grupo no tenga `view_expediente`,
    o el módulo quedaría inalcanzable desde la navegación."""
    grupo = Group.objects.create(name="Reporte")
    grupo.permissions.add(_permiso("view_reporte_provincias"))
    user = User.objects.create_user(username="reporte_puro", password="pass")
    user.groups.add(grupo)
    Profile.objects.get_or_create(user=user)

    client.force_login(user)
    html = client.get(reverse("reporter_provincias")).content.decode()

    assert reverse("reporter_provincias") in html
    assert reverse("cupo_dashboard") not in html
