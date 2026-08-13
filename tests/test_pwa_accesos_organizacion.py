"""Propagación automática de comedores a usuarios PWA de organización."""

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from comedores.models import Comedor, Programas
from core.models import Provincia
from organizaciones.models import Organizacion
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

    call_command("sincronizar_accesos_pwa_organizaciones")
    assert comedor_pendiente.id not in get_accessible_comedor_ids(user)

    call_command("sincronizar_accesos_pwa_organizaciones", "--apply")
    assert comedor_pendiente.id in get_accessible_comedor_ids(user)


@pytest.mark.django_db
def test_desactivar_accesos_representante_da_de_baja_la_organizacion(escenario):
    user = _crear_usuario_de_organizacion(escenario)

    sync_representante_accesses(user=user, access_specs=[], actor=None)

    assert get_organizacion_ids(user) == []
    assert AccesoOrganizacionPWA.objects.filter(user=user, activo=False).count() == 1
