"""Propagación automática de comedores a usuarios PWA de organización."""

from threading import Event, Thread

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.db import close_old_connections, connection, transaction
from django.db.models.signals import post_save
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from comedores.models import Comedor, Programas
from core.models import Provincia
from organizaciones.models import Organizacion
from users.api import aplicar_cambio_organizacion_comedor
from users.models import AccesoComedorPWA, AccesoOrganizacionPWA
from users.services_pwa import (
    get_accessible_comedor_ids,
    get_organizacion_ids,
    sync_representante_accesses,
)


@pytest.fixture
def escenario(db):
    provincia = Provincia.objects.create(nombre="Córdoba")
    programa = Programas.objects.create(nombre="Abordaje Comunitario")
    organizacion = Organizacion.objects.create(nombre="Organización PWA")
    otra_organizacion = Organizacion.objects.create(nombre="Otra Organización")
    comedor = Comedor.objects.create(
        nombre="Comedor Inicial",
        provincia=provincia,
        organizacion=organizacion,
        programa=programa,
    )
    return {
        "provincia": provincia,
        "programa": programa,
        "organizacion": organizacion,
        "otra_organizacion": otra_organizacion,
        "comedor": comedor,
    }


def _crear_usuario_de_organizacion(escenario, username="rep_org"):
    user = get_user_model().objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="testpass123",
    )
    sync_representante_accesses(
        user=user,
        access_specs=[
            {
                "comedor_id": escenario["comedor"].id,
                "tipo_asociacion": AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
                "organizacion_id": escenario["organizacion"].id,
            }
        ],
        actor=None,
    )
    return user


@pytest.mark.django_db
def test_sync_representante_accesses_registra_la_organizacion(escenario):
    user = _crear_usuario_de_organizacion(escenario)

    assert get_organizacion_ids(user) == [escenario["organizacion"].id]


@pytest.mark.django_db
def test_acceso_residual_no_autoriza_sin_membresia_activa(escenario):
    user = _crear_usuario_de_organizacion(escenario, username="rep_membership_baja")
    active_user = _crear_usuario_de_organizacion(
        escenario,
        username="rep_membership_activa",
    )

    AccesoOrganizacionPWA.objects.filter(
        user=user,
        organizacion=escenario["organizacion"],
    ).update(activo=False)

    assert AccesoComedorPWA.objects.filter(
        user=user,
        comedor=escenario["comedor"],
        activo=True,
    ).exists()
    assert get_accessible_comedor_ids(user) == []

    call_command(
        "sincronizar_accesos_pwa_organizaciones",
        "--organizacion",
        str(escenario["organizacion"].id),
        "--apply",
    )

    assert not AccesoComedorPWA.objects.filter(
        user=user,
        comedor=escenario["comedor"],
        activo=True,
    ).exists()
    assert get_accessible_comedor_ids(active_user) == [escenario["comedor"].id]


@pytest.mark.django_db
def test_fachada_publica_aplica_cambio_de_organizacion(escenario):
    user = _crear_usuario_de_organizacion(escenario, username="rep_users_api")
    comedor_nuevo = Comedor.objects.create(
        nombre="Comedor para fachada",
        provincia=escenario["provincia"],
        organizacion=None,
        programa=escenario["programa"],
    )

    result = aplicar_cambio_organizacion_comedor(
        comedor_id=comedor_nuevo.id,
        previous_organizacion_id=None,
        new_organizacion_id=escenario["organizacion"].id,
    )

    assert result == {"altas": 1, "bajas": 0}
    assert AccesoComedorPWA.objects.filter(
        user=user,
        comedor=comedor_nuevo,
        activo=True,
    ).exists()


@pytest.mark.django_db
def test_fallo_de_side_effect_revierte_alta_de_comedor_y_accesos(escenario):
    user = _crear_usuario_de_organizacion(escenario, username="rep_atomic_org")
    dispatch_uid = "tests.pwa.raise-after-comedor-save"

    def fail_after_save(**_kwargs):
        raise RuntimeError("fallo de side effect")

    post_save.connect(fail_after_save, sender=Comedor, dispatch_uid=dispatch_uid)
    try:
        with pytest.raises(RuntimeError, match="fallo de side effect"):
            Comedor.objects.create(
                nombre="Comedor Debe Revertirse",
                provincia=escenario["provincia"],
                organizacion=escenario["organizacion"],
                programa=escenario["programa"],
            )
    finally:
        post_save.disconnect(sender=Comedor, dispatch_uid=dispatch_uid)

    assert not Comedor.all_objects.filter(nombre="Comedor Debe Revertirse").exists()
    assert not AccesoComedorPWA.objects.filter(
        user=user,
        comedor__nombre="Comedor Debe Revertirse",
    ).exists()


@pytest.mark.mysql_compat
@pytest.mark.django_db(transaction=True)
def test_alta_espera_el_lock_de_la_membresia_en_mysql(escenario):
    if connection.vendor != "mysql":
        pytest.skip("La semántica de SELECT FOR UPDATE se valida sobre MySQL.")

    user = _crear_usuario_de_organizacion(escenario, username="rep_lock_org")
    comedor_nuevo = Comedor.objects.create(
        nombre="Comedor para carrera",
        provincia=escenario["provincia"],
        organizacion=None,
        programa=escenario["programa"],
    )
    started = Event()
    finished = Event()
    errors = []

    def grant_in_other_transaction():
        close_old_connections()
        started.set()
        try:
            aplicar_cambio_organizacion_comedor(
                comedor_id=comedor_nuevo.id,
                previous_organizacion_id=None,
                new_organizacion_id=escenario["organizacion"].id,
            )
        except Exception as exc:  # pragma: no cover - reportado en el hilo principal
            errors.append(exc)
        finally:
            close_old_connections()
            finished.set()

    with transaction.atomic():
        AccesoOrganizacionPWA.objects.select_for_update().get(
            user=user,
            organizacion=escenario["organizacion"],
        )
        worker = Thread(target=grant_in_other_transaction, daemon=True)
        worker.start()
        assert started.wait(timeout=2)
        was_blocked = not finished.wait(timeout=1)

    worker.join(timeout=10)

    assert was_blocked is True
    assert finished.is_set()
    assert errors == []
    assert AccesoComedorPWA.objects.filter(
        user=user,
        comedor=comedor_nuevo,
        activo=True,
    ).exists()


@pytest.mark.django_db
def test_comedor_nuevo_de_la_organizacion_se_asigna_al_usuario(escenario):
    user = _crear_usuario_de_organizacion(escenario)

    comedor_nuevo = Comedor.objects.create(
        nombre="Comedor Nuevo",
        provincia=escenario["provincia"],
        organizacion=escenario["organizacion"],
        programa=escenario["programa"],
    )

    assert set(get_accessible_comedor_ids(user)) == {
        escenario["comedor"].id,
        comedor_nuevo.id,
    }


@pytest.mark.django_db
def test_comedor_que_pasa_a_la_organizacion_se_asigna_al_usuario(escenario):
    user = _crear_usuario_de_organizacion(escenario)
    comedor_externo = Comedor.objects.create(
        nombre="Comedor Externo",
        provincia=escenario["provincia"],
        organizacion=escenario["otra_organizacion"],
        programa=escenario["programa"],
    )
    assert comedor_externo.id not in get_accessible_comedor_ids(user)

    comedor_externo.organizacion = escenario["organizacion"]
    comedor_externo.save(update_fields=["organizacion"])

    assert comedor_externo.id in get_accessible_comedor_ids(user)


@pytest.mark.django_db
def test_comedor_que_sale_de_la_organizacion_se_da_de_baja(escenario):
    user = _crear_usuario_de_organizacion(escenario)
    comedor = escenario["comedor"]

    comedor.organizacion = escenario["otra_organizacion"]
    comedor.save(update_fields=["organizacion"])

    assert get_accessible_comedor_ids(user) == []
    acceso = AccesoComedorPWA.objects.get(user=user, comedor=comedor)
    assert acceso.activo is False
    assert acceso.fecha_baja is not None


@pytest.mark.django_db
def test_la_organizacion_sobrevive_a_la_baja_de_todos_sus_comedores(escenario):
    user = _crear_usuario_de_organizacion(escenario)
    comedor = escenario["comedor"]

    comedor.organizacion = escenario["otra_organizacion"]
    comedor.save(update_fields=["organizacion"])
    assert get_accessible_comedor_ids(user) == []

    comedor_nuevo = Comedor.objects.create(
        nombre="Comedor Repuesto",
        provincia=escenario["provincia"],
        organizacion=escenario["organizacion"],
        programa=escenario["programa"],
    )

    assert get_accessible_comedor_ids(user) == [comedor_nuevo.id]


@pytest.mark.django_db
def test_representante_inactivo_recibe_nuevos_comedores_antes_de_reactivarse(
    client, escenario
):
    user = _crear_usuario_de_organizacion(escenario, username="rep_reactivado")
    admin = get_user_model().objects.create_superuser(
        username="admin_reactivar_rep",
        email="admin_reactivar_rep@example.com",
        password="testpass123",
    )
    admin.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="auth",
            codename="delete_user",
        )
    )
    client.force_login(admin)

    response = client.post(reverse("usuario_borrar", kwargs={"pk": user.pk}))
    assert response.status_code in {302, 303}
    user.refresh_from_db()
    assert user.is_active is False

    comedor_nuevo = Comedor.objects.create(
        nombre="Comedor Creado Durante la Baja",
        provincia=escenario["provincia"],
        organizacion=escenario["organizacion"],
        programa=escenario["programa"],
    )

    response = client.post(reverse("usuario_activar", kwargs={"pk": user.pk}))
    assert response.status_code in {302, 303}
    user.refresh_from_db()
    assert user.is_active is True
    assert comedor_nuevo.id in get_accessible_comedor_ids(user)


@pytest.mark.django_db
def test_usuario_de_ambas_organizaciones_conserva_el_comedor_que_se_mueve(escenario):
    user = _crear_usuario_de_organizacion(escenario)
    comedor_otra_org = Comedor.objects.create(
        nombre="Comedor Otra Org",
        provincia=escenario["provincia"],
        organizacion=escenario["otra_organizacion"],
        programa=escenario["programa"],
    )
    sync_representante_accesses(
        user=user,
        access_specs=[
            {
                "comedor_id": escenario["comedor"].id,
                "tipo_asociacion": AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
                "organizacion_id": escenario["organizacion"].id,
            },
            {
                "comedor_id": comedor_otra_org.id,
                "tipo_asociacion": AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
                "organizacion_id": escenario["otra_organizacion"].id,
            },
        ],
        actor=None,
    )

    comedor = escenario["comedor"]
    comedor.organizacion = escenario["otra_organizacion"]
    comedor.save(update_fields=["organizacion"])

    assert set(get_accessible_comedor_ids(user)) == {comedor.id, comedor_otra_org.id}
    acceso = AccesoComedorPWA.objects.get(user=user, comedor=comedor)
    assert acceso.activo is True
    assert acceso.organizacion_id == escenario["otra_organizacion"].id


@pytest.mark.django_db
def test_comedor_que_pierde_su_organizacion_se_da_de_baja(escenario):
    user = _crear_usuario_de_organizacion(escenario)
    comedor = escenario["comedor"]

    comedor.organizacion = None
    comedor.save(update_fields=["organizacion"])

    assert get_accessible_comedor_ids(user) == []
    assert get_organizacion_ids(user) == [escenario["organizacion"].id]


@pytest.mark.django_db
def test_soft_delete_y_restore_reconcilian_el_acceso_de_organizacion(escenario):
    user = _crear_usuario_de_organizacion(escenario, username="rep_restore_org")
    comedor = escenario["comedor"]

    comedor.delete(cascade=False)

    acceso = AccesoComedorPWA.objects.get(user=user, comedor_id=comedor.id)
    assert acceso.activo is False
    assert get_accessible_comedor_ids(user) == []

    comedor = Comedor.all_objects.get(pk=comedor.pk)
    comedor.restore(cascade=False)

    acceso.refresh_from_db()
    assert acceso.activo is True
    assert get_accessible_comedor_ids(user) == [comedor.id]


@pytest.mark.django_db
def test_no_alcanza_a_usuarios_asociados_por_espacio(escenario):
    user = get_user_model().objects.create_user(
        username="rep_espacio",
        email="rep_espacio@example.com",
        password="testpass123",
    )
    sync_representante_accesses(
        user=user,
        access_specs=[
            {
                "comedor_id": escenario["comedor"].id,
                "tipo_asociacion": AccesoComedorPWA.TIPO_ASOCIACION_ESPACIO,
                "organizacion_id": None,
            }
        ],
        actor=None,
    )

    comedor_nuevo = Comedor.objects.create(
        nombre="Comedor Nuevo",
        provincia=escenario["provincia"],
        organizacion=escenario["organizacion"],
        programa=escenario["programa"],
    )

    assert get_organizacion_ids(user) == []
    assert get_accessible_comedor_ids(user) == [escenario["comedor"].id]
    assert not AccesoComedorPWA.objects.filter(
        user=user, comedor=comedor_nuevo
    ).exists()


@pytest.mark.django_db
def test_comedor_alimentar_comunidad_sin_estado_habilitado_no_se_visualiza(escenario):
    user = _crear_usuario_de_organizacion(escenario)
    programa_alimentar = Programas.objects.create(nombre="Alimentar Comunidad")

    comedor_nuevo = Comedor.objects.create(
        nombre="Comedor Alimentar",
        provincia=escenario["provincia"],
        organizacion=escenario["organizacion"],
        programa=programa_alimentar,
    )

    assert AccesoComedorPWA.objects.filter(
        user=user, comedor=comedor_nuevo, activo=True
    ).exists()
    assert comedor_nuevo.id not in get_accessible_comedor_ids(user)


@pytest.mark.django_db
def test_comando_sincroniza_comedores_pendientes(escenario):
    user = _crear_usuario_de_organizacion(escenario)
    comedor_pendiente = Comedor.objects.create(
        nombre="Comedor Pendiente",
        provincia=escenario["provincia"],
        organizacion=escenario["organizacion"],
        programa=escenario["programa"],
    )
    AccesoComedorPWA.objects.filter(user=user, comedor=comedor_pendiente).delete()

    with CaptureQueriesContext(connection) as captured_queries:
        call_command("sincronizar_accesos_pwa_organizaciones")

    access_table_writes = [
        query["sql"]
        for query in captured_queries.captured_queries
        if query["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE"))
        and (
            "users_accesocomedorpwa" in query["sql"].lower()
            or "users_auditaccesocomedorpwa" in query["sql"].lower()
        )
    ]
    assert access_table_writes == []
    assert comedor_pendiente.id not in get_accessible_comedor_ids(user)

    call_command("sincronizar_accesos_pwa_organizaciones", "--apply")
    assert comedor_pendiente.id in get_accessible_comedor_ids(user)


@pytest.mark.django_db
def test_desactivar_accesos_representante_da_de_baja_la_organizacion(escenario):
    user = _crear_usuario_de_organizacion(escenario)

    sync_representante_accesses(user=user, access_specs=[], actor=None)

    assert get_organizacion_ids(user) == []
    assert AccesoOrganizacionPWA.objects.filter(user=user, activo=False).count() == 1
