from datetime import date, datetime
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from ciudadanos.models import Ciudadano
from centrodeinfancia.models import CentroDeInfancia, NominaCentroInfancia
from centrodeinfancia.services_nomina_ninos_pdf import build_export_data
from centrodeinfancia.services_renaper_estado import (
    build_adult_validation_map,
    estado_renaper_nomina,
)
from core.models import Provincia

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "estado_nino",
    [
        Ciudadano.RENAPER_VALIDADO,
        Ciudadano.RENAPER_NO_VALIDADO,
        Ciudadano.RENAPER_NO_CONSULTADO,
    ],
)
@pytest.mark.parametrize(
    "estados_adulto",
    [
        [],
        [Ciudadano.RENAPER_VALIDADO],
        [Ciudadano.RENAPER_NO_VALIDADO],
        [Ciudadano.RENAPER_NO_CONSULTADO],
        [Ciudadano.RENAPER_VALIDADO, Ciudadano.RENAPER_VALIDADO],
        [Ciudadano.RENAPER_VALIDADO, Ciudadano.RENAPER_NO_VALIDADO],
    ],
)
def test_paridad_con_calculo_previo_del_pdf(estado_nino, estados_adulto):
    provincia = Provincia.objects.create(nombre="Provincia paridad")
    centro = CentroDeInfancia.objects.create(nombre="CDI paridad", provincia=provincia)
    user = User.objects.create_superuser("paridad", "", "test1234")
    ciudadano = Ciudadano.objects.create(
        documento=55111111,
        apellido="Niño",
        nombre="Prueba",
        fecha_nacimiento=date(2024, 1, 15),
        estado_validacion_renaper=estado_nino,
    )
    for estado in estados_adulto:
        Ciudadano.objects.create(
            documento=30111111,
            apellido="Adulto",
            nombre="Prueba",
            fecha_nacimiento=date(1990, 1, 15),
            estado_validacion_renaper=estado,
            tipo_registro_identidad=Ciudadano.TIPO_REGISTRO_DNI_NO_VALIDADO,
        )
    ficha = NominaCentroInfancia.objects.create(
        centro=centro,
        ciudadano=ciudadano,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
        responsable_legal_1_dni=30111111,
        responsable_legal_2_dni=30111111,
    )
    nino_previo = "Sí" if estado_nino == Ciudadano.RENAPER_VALIDADO else "No"
    adulto_previo = (
        "Sí"
        if len(estados_adulto) == 1 and estados_adulto[0] == Ciudadano.RENAPER_VALIDADO
        else "No"
    )
    esperado = {
        "renaper_nino": nino_previo,
        "renaper_responsable_1": adulto_previo,
        "renaper_responsable_2": adulto_previo,
    }
    assert estado_renaper_nomina(ficha) == esperado
    mapa = build_adult_validation_map({"30111111"})
    assert estado_renaper_nomina(ficha, adult_validation=mapa) == esperado
    export = build_export_data(
        user=user,
        provincia=provincia,
        generado_en=timezone.make_aware(datetime(2026, 9, 15)),
    )
    row = export.centros[0].rows[0]
    assert row.renaper_nino == nino_previo
    assert row.adulto_renaper == adulto_previo


def test_responsables_independientes_y_ausentes():
    adulto = Ciudadano.objects.create(
        documento=30111111,
        apellido="Adulto",
        nombre="Dos",
        fecha_nacimiento=date(1990, 1, 15),
        estado_validacion_renaper=Ciudadano.RENAPER_VALIDADO,
    )
    ficha = SimpleNamespace(
        ciudadano=SimpleNamespace(
            estado_validacion_renaper=Ciudadano.RENAPER_NO_CONSULTADO
        ),
        responsable_legal_1_dni=None,
        responsable_legal_2_dni=adulto.documento,
    )
    assert estado_renaper_nomina(ficha) == {
        "renaper_nino": "No",
        "renaper_responsable_1": "No",
        "renaper_responsable_2": "Sí",
    }
    ficha.responsable_legal_2_dni = None
    assert estado_renaper_nomina(ficha)["renaper_responsable_2"] == "No"
    assert Ciudadano.objects.count() == 1


def test_adulto_borrado_no_cuenta_como_coincidencia():
    adulto = Ciudadano.objects.create(
        documento=30111111,
        apellido="Adulto",
        nombre="Borrado",
        fecha_nacimiento=date(1990, 1, 15),
        estado_validacion_renaper=Ciudadano.RENAPER_VALIDADO,
    )
    Ciudadano.objects.filter(pk=adulto.pk).update(deleted_at=timezone.now())
    # El mapa responde por cada documento pedido: un borrado nunca afirma "Sí".
    assert build_adult_validation_map({"30111111"}) == {"30111111": "No"}
