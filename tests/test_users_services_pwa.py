import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError

from comedores.models import Comedor
from core.models import Provincia
from users.models import AccesoComedorPWA
from users.services_pwa import (
    create_operador_for_comedor,
    deactivate_operador,
    get_accessible_comedor_ids,
    is_pwa_user,
    sync_representante_accesses,
)


@pytest.fixture
def comedores(db):
    provincia = Provincia.objects.create(nombre="Santa Fe")
    comedor_1 = Comedor.objects.create(nombre="Comedor 1", provincia=provincia)
    comedor_2 = Comedor.objects.create(nombre="Comedor 2", provincia=provincia)
    return comedor_1, comedor_2


def _create_user(username):
    user_model = get_user_model()
    return user_model.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="testpass123",
    )


@pytest.mark.django_db
def test_is_pwa_user_and_accessible_comedores(comedores):
    comedor_1, comedor_2 = comedores
    user = _create_user("rep_service")
    assert is_pwa_user(user) is False
    assert get_accessible_comedor_ids(user) == []

    AccesoComedorPWA.objects.create(
        user=user,
        comedor=comedor_1,
        rol=AccesoComedorPWA.ROL_REPRESENTANTE,
        activo=True,
    )
    AccesoComedorPWA.objects.create(
        user=user,
        comedor=comedor_2,
        rol=AccesoComedorPWA.ROL_REPRESENTANTE,
        activo=True,
    )

    assert is_pwa_user(user) is True
    assert set(get_accessible_comedor_ids(user)) == {comedor_1.id, comedor_2.id}


@pytest.mark.django_db
def test_create_operador_for_comedor_success(comedores):
    comedor_1, _ = comedores
    representante = _create_user("rep_creator")
    AccesoComedorPWA.objects.create(
        user=representante,
        comedor=comedor_1,
        rol=AccesoComedorPWA.ROL_REPRESENTANTE,
        activo=True,
    )

    acceso = create_operador_for_comedor(
        comedor_id=comedor_1.id,
        actor=representante,
        username="op_creator",
        email="op_creator@example.com",
        password="Secreta123!",
    )

    assert acceso.rol == AccesoComedorPWA.ROL_OPERADOR
    assert acceso.creado_por_id == representante.id
    assert acceso.user.is_active is True


@pytest.mark.django_db
def test_create_operador_for_comedor_requires_representante(comedores):
    comedor_1, _ = comedores
    actor = _create_user("actor_no_rep")

    with pytest.raises(PermissionDenied):
        create_operador_for_comedor(
            comedor_id=comedor_1.id,
            actor=actor,
            username="op_fail",
            email="op_fail@example.com",
            password="Secreta123!",
        )


@pytest.mark.django_db
def test_create_operador_for_comedor_rejects_duplicate_email(comedores):
    comedor_1, _ = comedores
    representante = _create_user("rep_dup")
    _create_user("usuario_existente")
    get_user_model().objects.filter(username="usuario_existente").update(
        email="duplicado@example.com"
    )
    AccesoComedorPWA.objects.create(
        user=representante,
        comedor=comedor_1,
        rol=AccesoComedorPWA.ROL_REPRESENTANTE,
        activo=True,
    )

    with pytest.raises(ValidationError):
        create_operador_for_comedor(
            comedor_id=comedor_1.id,
            actor=representante,
            username="op_dup",
            email="duplicado@example.com",
            password="Secreta123!",
        )


@pytest.mark.django_db
def test_create_operador_for_comedor_handles_integrity_error(comedores, monkeypatch):
    comedor_1, _ = comedores
    representante = _create_user("rep_race")
    AccesoComedorPWA.objects.create(
        user=representante,
        comedor=comedor_1,
        rol=AccesoComedorPWA.ROL_REPRESENTANTE,
        activo=True,
    )

    def _raise_integrity_error(*args, **kwargs):
        raise IntegrityError("duplicate key")

    monkeypatch.setattr(
        "users.services_pwa.User.objects.create_user",
        _raise_integrity_error,
    )

    with pytest.raises(ValidationError):
        create_operador_for_comedor(
            comedor_id=comedor_1.id,
            actor=representante,
            username="op_race",
            email="op_race@example.com",
            password="Secreta123!",
        )


@pytest.mark.django_db
def test_deactivate_operador_disables_user_and_access(comedores):
    comedor_1, _ = comedores
    representante = _create_user("rep_deactivate")
    AccesoComedorPWA.objects.create(
        user=representante,
        comedor=comedor_1,
        rol=AccesoComedorPWA.ROL_REPRESENTANTE,
        activo=True,
    )
    acceso = create_operador_for_comedor(
        comedor_id=comedor_1.id,
        actor=representante,
        username="op_deactivate",
        email="op_deactivate@example.com",
        password="Secreta123!",
    )

    deactivate_operador(
        comedor_id=comedor_1.id,
        user_id=acceso.user_id,
        actor=representante,
    )

    acceso.refresh_from_db()
    acceso.user.refresh_from_db()
    assert acceso.activo is False
    assert acceso.user.is_active is False


@pytest.mark.django_db
def test_sync_representante_accesses_switches_selected_comedores(comedores):
    comedor_1, comedor_2 = comedores
    user = _create_user("rep_sync")

    sync_representante_accesses(user=user, comedor_ids=[comedor_1.id], actor=None)
    assert (
        AccesoComedorPWA.objects.filter(
            user=user,
            comedor=comedor_1,
            rol=AccesoComedorPWA.ROL_REPRESENTANTE,
            activo=True,
        ).exists()
        is True
    )

    sync_representante_accesses(user=user, comedor_ids=[comedor_2.id], actor=None)
    assert (
        AccesoComedorPWA.objects.filter(
            user=user,
            comedor=comedor_1,
            rol=AccesoComedorPWA.ROL_REPRESENTANTE,
            activo=True,
        ).exists()
        is False
    )
    assert (
        AccesoComedorPWA.objects.filter(
            user=user,
            comedor=comedor_2,
            rol=AccesoComedorPWA.ROL_REPRESENTANTE,
            activo=True,
        ).exists()
        is True
    )
