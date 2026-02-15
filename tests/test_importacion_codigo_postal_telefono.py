"""Tests for test importacion codigo postal telefono."""

from io import BytesIO
from datetime import date

import pandas as pd
import pytest
from django.contrib.auth import get_user_model

from celiaquia.models import EstadoExpediente, EstadoLegajo, Expediente
from celiaquia.services.importacion_service import ImportacionService
from ciudadanos.models import Ciudadano


@pytest.mark.django_db
def test_import_with_postal_code_and_phone():
    user = get_user_model().objects.create(username="tester")
    estado_exp = EstadoExpediente.objects.create(nombre="CREADO")
    expediente = Expediente.objects.create(usuario_provincia=user, estado=estado_exp)
    EstadoLegajo.objects.create(nombre="DOCUMENTO_PENDIENTE")
    df = pd.DataFrame(
        [
            {
                "apellido": "Perez",
                "nombre": "Juan",
                "documento": 1234567890,
                "fecha_nacimiento": date(1990, 1, 1),
                "telefono": 3815237945,
                "codigo_postal": 1406,
            }
        ]
    )
    bio = BytesIO()
    df.to_excel(bio, index=False)
    bio.seek(0)

    ImportacionService.importar_legajos_desde_excel(expediente, bio, user)

    ciudadano = Ciudadano.objects.get(documento=1234567890)
    assert ciudadano.telefono == "3815237945"
    assert ciudadano.codigo_postal == "1406"
