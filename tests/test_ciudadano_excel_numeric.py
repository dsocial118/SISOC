"""Tests for test ciudadano excel numeric."""

from io import BytesIO
from datetime import date

import pandas as pd
import pytest

from celiaquia.services.ciudadano_service import CiudadanoService
from core.models import Sexo


@pytest.mark.django_db
def test_excel_numeric_sex_assigns_masculino():
    Sexo.objects.create(id=1, sexo="Femenino")
    Sexo.objects.create(id=2, sexo="Masculino")

    df = pd.DataFrame(
        [
            {
                "tipo_documento": "DNI",
                "documento": 12345678,
                "nombre": "Juan",
                "apellido": "Perez",
                "fecha_nacimiento": date(1990, 1, 1),
                "sexo": 2,
            }
        ]
    )
    bio = BytesIO()
    df.to_excel(bio, index=False)
    bio.seek(0)
    parsed = pd.read_excel(bio).iloc[0].to_dict()

    ciudadano = CiudadanoService.get_or_create_ciudadano(parsed)
    assert ciudadano.sexo.sexo == "Masculino"
