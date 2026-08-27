from datetime import timedelta

import pytest
from django.utils import timezone

from core.models import Municipio, Provincia
from services.dispositivos.dispositivos.boundary import (
    DispositivosActor,
    TerritorialScope,
    get_geography_scope_map,
)
from services.dispositivos.dispositivos.models import Dispositivo
from services.dispositivos.dispositivos.services import get_dispositivos_queryset


@pytest.mark.django_db
def test_get_dispositivos_queryset_ordena_por_fecha_desc():
    provincia = Provincia.objects.create(nombre="Santa Fe")
    municipio = Municipio.objects.create(nombre="Rosario", provincia=provincia)

    viejo = Dispositivo.objects.create(
        nombre_institucion="Dispositivo A",
        tipo_gestion="estatal",
        cuit_institucion="20123456789",
        provincia=provincia,
        municipio=municipio,
        calle="A",
        altura="100",
        telefono_prefijo="11",
        telefono_numero="1234567",
        responsable_nombre_completo="Resp A",
        responsable_dni="12345678",
        tipo_dispositivo="refugio",
        modalidad_funcionamiento="permanente",
        capacidad_total_plazas="0_15",
    )
    nuevo = Dispositivo.objects.create(
        nombre_institucion="Dispositivo B",
        tipo_gestion="estatal",
        cuit_institucion="20987654321",
        provincia=provincia,
        municipio=municipio,
        calle="B",
        altura="200",
        telefono_prefijo="22",
        telefono_numero="7654321",
        responsable_nombre_completo="Resp B",
        responsable_dni="23456789",
        tipo_dispositivo="refugio",
        modalidad_funcionamiento="permanente",
        capacidad_total_plazas="16_30",
    )
    Dispositivo.objects.filter(pk=viejo.pk).update(
        created_at=timezone.now() - timedelta(minutes=1)
    )
    Dispositivo.objects.filter(pk=nuevo.pk).update(created_at=timezone.now())

    queryset = list(get_dispositivos_queryset())

    assert queryset[0].pk == nuevo.pk
    assert queryset[1].pk == viejo.pk


def test_geography_scope_preserva_provincia_completa_y_municipios_especificos():
    actor = DispositivosActor(
        actor_id=7,
        is_authenticated=True,
        is_superuser=False,
        is_territorial=True,
        scopes=(
            TerritorialScope(provincia_id=1, municipio_id=10),
            TerritorialScope(provincia_id=1, municipio_id=11),
            TerritorialScope(provincia_id=2),
            TerritorialScope(provincia_id=2, municipio_id=20),
        ),
    )

    assert get_geography_scope_map(actor) == {1: {10, 11}, 2: None}


def test_geography_scope_actor_territorial_sin_alcances_no_habilita_opciones():
    actor = DispositivosActor(
        actor_id=7,
        is_authenticated=True,
        is_superuser=False,
        is_territorial=True,
    )

    assert get_geography_scope_map(actor) == {}


def test_actor_solo_reconoce_los_permisos_recibidos():
    actor = DispositivosActor(
        actor_id=7,
        is_authenticated=True,
        is_superuser=False,
        is_territorial=False,
        permissions=frozenset({"dispositivos.view_dispositivo"}),
    )

    assert actor.has_permission("dispositivos.view_dispositivo")
    assert not actor.has_permission("dispositivos.change_dispositivo")
