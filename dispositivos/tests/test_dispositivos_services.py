from datetime import timedelta

import pytest
from django.utils import timezone

from core.models import Municipio, Provincia
from dispositivos.models import Dispositivo
from dispositivos.services import get_dispositivos_queryset


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
