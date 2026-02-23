"""Tests de formularios para comunicados."""

import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

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
        user=User.objects.create_superuser(
            "admin_form_invalid", "form@test.com", "test"
        ),
    )

    assert not form.is_valid()
    assert "comedores" in form.errors


def test_form_valido_si_es_para_todos_los_comedores():
    form = ComunicadoForm(
        data=_base_form_data(para_todos_comedores="on"),
        user=User.objects.create_superuser(
            "admin_form_todos", "form_todos@test.com", "test"
        ),
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


def test_form_invalido_si_adjunto_tiene_extension_no_permitida():
    archivo = SimpleUploadedFile(
        "script.exe",
        b"contenido",
        content_type="application/octet-stream",
    )
    form = ComunicadoForm(
        data=_base_form_data(para_todos_comedores="on"),
        files={"archivos_adjuntos": archivo},
        user=User.objects.create_superuser(
            "admin_form_ext", "form_ext@test.com", "test"
        ),
    )

    assert not form.is_valid()
    assert "archivos_adjuntos" in form.errors


def test_form_invalido_si_adjunto_supera_tamanio_maximo():
    archivo = SimpleUploadedFile(
        "archivo.pdf",
        b"a" * (10 * 1024 * 1024 + 1),
        content_type="application/pdf",
    )
    form = ComunicadoForm(
        data=_base_form_data(para_todos_comedores="on"),
        files={"archivos_adjuntos": archivo},
        user=User.objects.create_superuser(
            "admin_form_size", "form_size@test.com", "test"
        ),
    )

    assert not form.is_valid()
    assert "archivos_adjuntos" in form.errors


def test_form_valido_si_adjunto_es_pdf_y_tamanio_permitido():
    archivo = SimpleUploadedFile(
        "archivo.pdf",
        b"%PDF-1.4",
        content_type="application/pdf",
    )
    form = ComunicadoForm(
        data=_base_form_data(para_todos_comedores="on"),
        files={"archivos_adjuntos": archivo},
        user=User.objects.create_superuser(
            "admin_form_pdf", "form_pdf@test.com", "test"
        ),
    )

    assert form.is_valid()
