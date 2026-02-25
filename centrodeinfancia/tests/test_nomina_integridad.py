from datetime import date

import pytest
from django.db import transaction

from ciudadanos.models import Ciudadano
from centrodeinfancia.models import CentroDeInfancia, NominaCentroInfancia
from centrodeinfancia.views import NominaCentroInfanciaCreateView
from core.models import Provincia


@pytest.mark.django_db(transaction=True)
def test_crear_nomina_con_bloqueo_evitar_duplicados():
    provincia = Provincia.objects.create(nombre="Rio Negro")
    centro = CentroDeInfancia.objects.create(nombre="CDI RN", provincia=provincia)
    ciudadano = Ciudadano.objects.create(
        apellido="Lopez",
        nombre="Ana",
        fecha_nacimiento=date(2012, 5, 10),
        documento=33333333,
    )

    with transaction.atomic():
        creado_1 = NominaCentroInfanciaCreateView._crear_nomina_con_bloqueo(
            centro=centro,
            ciudadano=ciudadano,
            estado=NominaCentroInfancia.ESTADO_ACTIVO,
            observaciones="Alta inicial",
        )

    with transaction.atomic():
        creado_2 = NominaCentroInfanciaCreateView._crear_nomina_con_bloqueo(
            centro=centro,
            ciudadano=ciudadano,
            estado=NominaCentroInfancia.ESTADO_ACTIVO,
            observaciones="Intento duplicado",
        )

    assert creado_1 is True
    assert creado_2 is False
    assert (
        NominaCentroInfancia.objects.filter(
            centro=centro,
            ciudadano=ciudadano,
            deleted_at__isnull=True,
        ).count()
        == 1
    )
