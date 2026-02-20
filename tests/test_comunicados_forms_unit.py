"""Tests de formularios para comunicados."""

import pytest
from django.contrib.auth.models import User

from comunicados.forms import ComunicadoForm
from comunicados.models import SubtipoComunicado, TipoComunicado
from comedores.models import Comedor


pytestmark = pytest.mark.django_db


def _base_form_data(**overrides):
    data = {
        "titulo": "Comunicado prueba",
        "cuerpo": "Contenido de prueba",
        "tipo": TipoComunicado.EXTERNO,
        "subtipo": SubtipoComunicado.COMEDORES,
        "fecha_vencimiento": "",
    }
    data.update(overrides)
    return data


def test_form_invalido_si_es_externo_comedores_sin_destinatarios():
    form = ComunicadoForm(
        data=_base_form_data(),
        user=User.objects.create_superuser("admin_form_invalid", "form@test.com", "test"),
    )

    assert not form.is_valid()
    assert "comedores" in form.errors


def test_form_valido_si_es_para_todos_los_comedores():
    form = ComunicadoForm(
        data=_base_form_data(para_todos_comedores="on"),
        user=User.objects.create_superuser("admin_form_todos", "form_todos@test.com", "test"),
    )

    assert form.is_valid()


def test_form_valido_si_selecciona_comedor_especifico():
    comedor = Comedor.objects.create(nombre="Comedor destino")
    form = ComunicadoForm(
        data=_base_form_data(comedores=[str(comedor.pk)]),
        user=User.objects.create_superuser(
            "admin_form_destino", "form_destino@test.com", "test"
        ),
    )

    assert form.is_valid()
