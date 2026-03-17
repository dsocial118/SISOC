import pytest
from django.contrib.auth.models import Permission, User
from django.urls import reverse

from centrodeinfancia.models import CentroDeInfancia, Trabajador
from core.models import Provincia
from users.models import Profile


def _crear_usuario(username, provincia=None, *, superuser=False, permisos=None):
    permisos = permisos or []
    if superuser:
        user = User.objects.create_superuser(
            username=username,
            email=f"{username}@example.com",
            password="test1234",
        )
    else:
        user = User.objects.create_user(username=username, password="test1234")
        if permisos:
            user.user_permissions.add(*Permission.objects.filter(codename__in=permisos))

    profile, _ = Profile.objects.get_or_create(user=user)
    profile.provincia = provincia
    profile.save()
    return user


@pytest.mark.django_db
def test_detalle_cdi_muestra_trabajadores_y_oculta_acciones_sin_permiso_edicion(client):
    user = _crear_usuario(
        "user-trabajadores-view",
        permisos=["view_centrodeinfancia"],
    )
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Trabajadores")
    Trabajador.objects.create(
        centro=centro,
        nombre="Ana",
        apellido="Lopez",
        rol=Trabajador.Rol.PROFESOR,
    )

    response = client.get(reverse("centrodeinfancia_detalle", kwargs={"pk": centro.pk}))

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Trabajadores" in content
    assert "Lopez, Ana" in content
    assert "Profesor" in content
    assert "Agregar trabajador" not in content
    assert "trabajador-editar-btn" not in content
    assert "trabajador-eliminar-btn" not in content


@pytest.mark.django_db
def test_trabajador_create_post_crea_y_redirige(client):
    user = _crear_usuario("super-trabajador-create", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Alta")

    response = client.post(
        reverse("centrodeinfancia_trabajador_crear", kwargs={"pk": centro.pk}),
        data={
            "nombre": "Julia",
            "apellido": "Mendez",
            "telefono": "11-2345-6789",
            "rol": Trabajador.Rol.DIRECTOR,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("centrodeinfancia_detalle", kwargs={"pk": centro.pk})
    trabajador = Trabajador.objects.get(centro=centro)
    assert trabajador.nombre == "Julia"
    assert trabajador.apellido == "Mendez"
    assert trabajador.telefono == "11-2345-6789"
    assert trabajador.rol == Trabajador.Rol.DIRECTOR


@pytest.mark.django_db
def test_trabajador_edit_post_actualiza_y_redirige(client):
    user = _crear_usuario("super-trabajador-edit", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Edit")
    trabajador = Trabajador.objects.create(
        centro=centro,
        nombre="Mario",
        apellido="Suarez",
        telefono="",
        rol=Trabajador.Rol.ADMINISTRATIVO,
    )

    response = client.post(
        reverse(
            "centrodeinfancia_trabajador_editar",
            kwargs={"pk": centro.pk, "trabajador_id": trabajador.pk},
        ),
        data={
            "nombre": "Maria",
            "apellido": "Suarez",
            "telefono": "011-4444-5555",
            "rol": Trabajador.Rol.PROFESOR,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("centrodeinfancia_detalle", kwargs={"pk": centro.pk})
    trabajador.refresh_from_db()
    assert trabajador.nombre == "Maria"
    assert trabajador.telefono == "011-4444-5555"
    assert trabajador.rol == Trabajador.Rol.PROFESOR


@pytest.mark.django_db
def test_trabajador_delete_post_hace_baja_logica_y_redirige(client):
    user = _crear_usuario("super-trabajador-delete", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Delete")
    trabajador = Trabajador.objects.create(
        centro=centro,
        nombre="Laura",
        apellido="Perez",
        rol=Trabajador.Rol.ADMINISTRATIVO,
    )

    response = client.post(
        reverse(
            "centrodeinfancia_trabajador_eliminar",
            kwargs={"pk": centro.pk, "trabajador_id": trabajador.pk},
        )
    )

    assert response.status_code == 302
    assert response.url == reverse("centrodeinfancia_detalle", kwargs={"pk": centro.pk})
    assert not Trabajador.objects.filter(pk=trabajador.pk).exists()
    trabajador = Trabajador.all_objects.get(pk=trabajador.pk)
    assert trabajador.deleted_at is not None


@pytest.mark.django_db
def test_trabajador_editar_no_permite_centro_fuera_de_scope(client):
    provincia_a = Provincia.objects.create(nombre="Buenos Aires")
    provincia_b = Provincia.objects.create(nombre="Cordoba")
    user = _crear_usuario(
        "user-trabajador-scope",
        provincia=provincia_a,
        permisos=["change_centrodeinfancia"],
    )
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Scope", provincia=provincia_b)
    trabajador = Trabajador.objects.create(
        centro=centro,
        nombre="Paula",
        apellido="Diaz",
        rol=Trabajador.Rol.PROFESOR,
    )

    response = client.post(
        reverse(
            "centrodeinfancia_trabajador_editar",
            kwargs={"pk": centro.pk, "trabajador_id": trabajador.pk},
        ),
        data={
            "nombre": "Paula",
            "apellido": "Diaz",
            "telefono": "",
            "rol": Trabajador.Rol.DIRECTOR,
        },
    )

    assert response.status_code == 404
