from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.urls import reverse

from core.models import MontoPrestacionPrograma, Programa
from historial.models import Historial
from historial.services import historial_service
from historial.services.historial_service import HistorialService


pytestmark = pytest.mark.django_db


@pytest.fixture
def programa():
    return Programa.objects.create(nombre="Programa ABM")


@pytest.fixture
def prestacion(user, programa):
    return MontoPrestacionPrograma.objects.create(
        programa=programa,
        desayuno_valor=Decimal("100.00"),
        usuario_creador=user,
    )


@pytest.fixture
def gestor_prestaciones_user(user):
    # El route-level permission check actual solo admite codenames canónicos o superuser.
    return get_user_model().objects.create_superuser(
        username="gestor_prestaciones_super",
        email="gestor_prestaciones_super@example.com",
        password="testpass",
    )


@pytest.mark.parametrize(
    ("url_name", "con_pk"),
    [
        ("montoprestacion_listar", False),
        ("montoprestacion_crear", False),
        ("montoprestacion_editar", True),
        ("montoprestacion_eliminar", True),
        ("montoprestacion_detalle", True),
    ],
)
def test_abm_prestaciones_requiere_grupo(client, user, prestacion, url_name, con_pk):
    client.force_login(user)
    kwargs = {"pk": prestacion.pk} if con_pk else {}

    response = client.get(reverse(url_name, kwargs=kwargs))

    assert response.status_code == 403


def test_create_asigna_usuario_y_registra_historial(
    client,
    gestor_prestaciones_user,
    programa,
    monkeypatch,
):
    client.force_login(gestor_prestaciones_user)
    monkeypatch.setattr(
        "config.middlewares.threadlocals.get_current_user",
        lambda: gestor_prestaciones_user,
    )

    response = client.post(
        reverse("montoprestacion_crear"),
        data={
            "programa": programa.pk,
            "desayuno_valor": "150.00",
            "almuerzo_valor": "",
            "merienda_valor": "",
            "cena_valor": "",
        },
    )

    assert response.status_code in {302, 303}
    created = MontoPrestacionPrograma.objects.get()
    assert created.usuario_creador == gestor_prestaciones_user
    assert created.programa == programa
    assert Historial.objects.filter(
        accion="Creación de Monto de Prestación",
        object_id=str(created.pk),
    ).exists()


def test_create_rechaza_registro_sin_montos(client, gestor_prestaciones_user, programa):
    client.force_login(gestor_prestaciones_user)

    response = client.post(
        reverse("montoprestacion_crear"),
        data={
            "programa": programa.pk,
            "desayuno_valor": "",
            "almuerzo_valor": "",
            "merienda_valor": "",
            "cena_valor": "",
        },
    )

    assert response.status_code == 200
    assert MontoPrestacionPrograma.objects.count() == 0
    assert "Debe informar al menos un monto." in response.content.decode()


def test_update_renderiza_contexto_componentes(
    client, gestor_prestaciones_user, prestacion
):
    client.force_login(gestor_prestaciones_user)

    response = client.get(
        reverse("montoprestacion_editar", kwargs={"pk": prestacion.pk})
    )

    assert response.status_code == 200
    assert "Editar Monto de Prestación" in response.content.decode()
    assert reverse("montoprestacion_listar") in response.content.decode()


def test_update_hace_rollback_si_falla_historial(
    client,
    gestor_prestaciones_user,
    prestacion,
    monkeypatch,
):
    client.force_login(gestor_prestaciones_user)

    monkeypatch.setattr(
        HistorialService,
        "registrar_historial",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("historial caido")),
    )

    with pytest.raises(RuntimeError, match="historial caido"):
        client.post(
            reverse("montoprestacion_editar", kwargs={"pk": prestacion.pk}),
            data={
                "programa": prestacion.programa_id,
                "desayuno_valor": "999.99",
                "almuerzo_valor": "",
                "merienda_valor": "",
                "cena_valor": "",
            },
        )

    prestacion.refresh_from_db()
    assert prestacion.desayuno_valor == Decimal("100.00")


def test_delete_no_borra_si_falla_historial(
    client,
    gestor_prestaciones_user,
    prestacion,
    monkeypatch,
):
    client.force_login(gestor_prestaciones_user)

    monkeypatch.setattr(
        HistorialService,
        "registrar_historial",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("historial caido")),
    )

    with pytest.raises(RuntimeError, match="historial caido"):
        client.post(
            reverse("montoprestacion_eliminar", kwargs={"pk": prestacion.pk}),
        )

    assert MontoPrestacionPrograma.objects.filter(pk=prestacion.pk).exists()
