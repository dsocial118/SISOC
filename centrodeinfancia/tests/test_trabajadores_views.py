import pytest
from django.contrib.auth.models import Permission, User
from django.urls import reverse

from centrodeinfancia.models import (
    CentroDeInfancia,
    NominaNacionalidad,
    NominaPais,
    Trabajador,
)
from centrodeinfancia.tests.test_trabajador_form import datos_validos
from core.models import Provincia
from users.models import Profile


def datos_validos_trabajador(**overrides):
    """Payload completo del legajo; los catálogos no vienen de fixtures en tests."""

    NominaPais.objects.get_or_create(nombre="Argentina")
    NominaNacionalidad.objects.get_or_create(nombre="Argentino")
    return datos_validos(**overrides)


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
    assert "Agregar trabajador" not in content
    assert "trabajador-eliminar-btn" not in content


@pytest.mark.django_db
def test_trabajador_create_post_crea_y_redirige(client):
    user = _crear_usuario("super-trabajador-create", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Alta")

    response = client.post(
        reverse("centrodeinfancia_trabajador_crear", kwargs={"pk": centro.pk}),
        data=datos_validos_trabajador(
            nombre="Julia",
            apellido="Mendez",
            telefono="11-2345-6789",
            subcomponente="cdi",
        ),
    )

    assert response.status_code == 302
    assert response.url == reverse("centrodeinfancia_detalle", kwargs={"pk": centro.pk})
    trabajador = Trabajador.objects.get(centro=centro)
    assert trabajador.nombre == "Julia"
    assert trabajador.apellido == "Mendez"
    assert trabajador.telefono == "11-2345-6789"
    assert trabajador.subcomponente == "cdi"
    assert trabajador.campos_verificados_renaper == []


@pytest.mark.django_db
def test_trabajador_create_ignora_procedencia_renaper_falsificada(client):
    user = _crear_usuario("super-trabajador-renaper-falsificado", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI RENAPER falso")

    data = datos_validos_trabajador()
    data["origen_dato"] = "renaper"
    data["campos_renaper"] = "nombre,apellido,dni"

    response = client.post(
        reverse("centrodeinfancia_trabajador_crear", kwargs={"pk": centro.pk}),
        data=data,
    )

    assert response.status_code == 302
    trabajador = Trabajador.objects.get(centro=centro)
    assert trabajador.campos_verificados_renaper == []


@pytest.mark.django_db
def test_trabajador_create_no_relaja_obligatorios_por_campos_renaper_falsificados(
    client,
):
    user = _crear_usuario("super-trabajador-renaper-obligatorios", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI RENAPER obligatorios")

    data = datos_validos_trabajador(nombre="")
    data["origen_dato"] = "renaper"
    data["campos_renaper"] = "nombre"

    response = client.post(
        reverse("centrodeinfancia_trabajador_crear", kwargs={"pk": centro.pk}),
        data=data,
    )

    assert response.status_code == 200
    assert "nombre" in response.context["form"].errors
    assert not Trabajador.objects.filter(centro=centro).exists()


@pytest.mark.django_db
def test_trabajador_create_persiste_y_bloquea_solo_prefill_renaper_servidor(
    client, monkeypatch
):
    user = _crear_usuario("super-trabajador-renaper-servidor", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI RENAPER servidor")
    url = reverse("centrodeinfancia_trabajador_crear", kwargs={"pk": centro.pk})
    datos_validos_trabajador()
    monkeypatch.setattr(
        "centrodeinfancia.views.ComedorService.obtener_datos_ciudadano_desde_renaper",
        lambda _dni: {
            "success": True,
            "data": {
                "nombre": "Juana",
                "apellido": "Pérez",
                "dni": "30123456",
            },
            "datos_api": {},
        },
    )

    response = client.get(f"{url}?query=30123456")

    assert response.status_code == 200
    token = response.context["renaper_prefill_token"]
    assert token
    assert response.context["form"].fields["nombre"].disabled is True

    data = datos_validos_trabajador(
        nombre="Adulterado", apellido="Manipulado", dni="99999999"
    )
    data["renaper_prefill_token"] = token
    response = client.post(url, data=data)

    assert response.status_code == 302
    trabajador = Trabajador.objects.get(centro=centro)
    assert trabajador.nombre == "Juana"
    assert trabajador.apellido == "Pérez"
    assert trabajador.dni == 30123456
    assert trabajador.campos_verificados_renaper == ["nombre", "apellido", "dni"]


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
        data=datos_validos_trabajador(
            nombre="Maria",
            apellido="Suarez",
            telefono="011-4444-5555",
            subcomponente="egp",
            funcion_egp="coordinacion_general",
            funcion_cdi="",
            sala_cdi="",
        ),
    )

    assert response.status_code == 302
    assert response.url == reverse("centrodeinfancia_detalle", kwargs={"pk": centro.pk})
    trabajador.refresh_from_db()
    assert trabajador.nombre == "Maria"
    assert trabajador.telefono == "011-4444-5555"
    assert trabajador.subcomponente == "egp"
    assert trabajador.funcion_egp == "coordinacion_general"


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
        permisos=["change_trabajador"],
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


@pytest.mark.django_db
def test_trabajador_ver_devuelve_200(client):
    user = _crear_usuario("user-trabajador-ver", permisos=["view_trabajador"])
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Ver")
    trabajador = Trabajador.objects.create(
        centro=centro,
        nombre="Carlos",
        apellido="Rojas",
        subcomponente="cdi",
        funcion_cdi="educador_docente_sala",
    )

    response = client.get(
        reverse(
            "centrodeinfancia_trabajador_ver",
            kwargs={"pk": centro.pk, "trabajador_id": trabajador.pk},
        )
    )

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Rojas, Carlos" in content
    assert "Fuerza de trabajo" in content


@pytest.mark.django_db
def test_trabajador_ver_fuera_de_scope_devuelve_404(client):
    provincia_a = Provincia.objects.create(nombre="Mendoza")
    provincia_b = Provincia.objects.create(nombre="Jujuy")
    user = _crear_usuario(
        "user-ver-scope", provincia=provincia_a, permisos=["view_trabajador"]
    )
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Jujuy", provincia=provincia_b)
    trabajador = Trabajador.objects.create(centro=centro, nombre="X", apellido="Y")

    response = client.get(
        reverse(
            "centrodeinfancia_trabajador_ver",
            kwargs={"pk": centro.pk, "trabajador_id": trabajador.pk},
        )
    )

    assert response.status_code == 404
