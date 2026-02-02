# celiaquia/tests/test_validation_errors.py
"""Tests for validation error handling in celiaquia views."""

import json
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.test import RequestFactory

from celiaquia.views.confirm_envio import ExpedienteConfirmView
from celiaquia.views.cupo import (
    CupoBajaLegajoView,
    CupoProvinciaDetailView,
    CupoSuspenderLegajoView,
)


class DummyUser:
    """Simple user stub for request objects."""

    is_staff = True
    is_authenticated = True
    username = "tester"


factory = RequestFactory()


def test_confirm_envio_validation_error_returns_validation_message():
    request = factory.post("/expediente/1/confirm/")
    request.user = DummyUser()
    request._dont_enforce_csrf_checks = True

    dummy_estado = type("Estado", (), {"nombre": "EN_ESPERA"})()
    dummy_exp = type(
        "Exp",
        (),
        {"pk": 1, "usuario_provincia": object(), "estado": dummy_estado},
    )()

    dummy_qs = MagicMock()
    dummy_qs.select_related.return_value = dummy_qs
    dummy_qs.filter.return_value = dummy_qs
    dummy_qs.exists.return_value = False

    dummy_err_qs = MagicMock()
    dummy_err_qs.filter.return_value = dummy_err_qs
    dummy_err_qs.exists.return_value = False

    with (
        patch(
            "celiaquia.views.confirm_envio.get_object_or_404", return_value=dummy_exp
        ),
        patch("celiaquia.views.confirm_envio.ExpedienteCiudadano.objects", dummy_qs),
        patch("celiaquia.views.confirm_envio.RegistroErroneo.objects", dummy_err_qs),
        patch(
            "celiaquia.views.confirm_envio.ExpedienteService.confirmar_envio",
            side_effect=ValidationError("err"),
        ),
    ):
        response = ExpedienteConfirmView.as_view()(request, pk=1)

    assert response.status_code == 400
    assert json.loads(response.content) == {"success": False, "error": "err"}


def test_configurar_cupo_validation_error_returns_generic_message():
    request = factory.post("/cupo/1/", {"accion": "config", "total_asignado": "1"})
    request.user = DummyUser()
    request._dont_enforce_csrf_checks = True

    with (
        patch("celiaquia.views.cupo.get_object_or_404", return_value=object()),
        patch(
            "celiaquia.views.cupo.CupoService.configurar_total",
            side_effect=ValidationError("err"),
        ),
    ):
        response = CupoProvinciaDetailView.as_view()(request, provincia_id=1)

    assert response.status_code == 400
    assert json.loads(response.content) == {
        "success": False,
        "message": "Error de validación.",
    }


def test_cupo_baja_legajo_validation_error_returns_generic_message():
    request = factory.post("/cupo/baja/", {"motivo": "x"})
    request.user = DummyUser()
    request._dont_enforce_csrf_checks = True

    with patch(
        "celiaquia.views.cupo._BaseAccionLegajo._get_legajo_validado",
        side_effect=ValidationError("err"),
    ):
        response = CupoBajaLegajoView.as_view()(request, provincia_id=1, legajo_id=1)

    assert response.status_code == 400
    assert json.loads(response.content) == {
        "success": False,
        "message": "No se pudo validar el legajo.",
    }


def test_cupo_suspender_legajo_validation_error_returns_generic_message():
    request = factory.post("/cupo/suspender/", {"motivo": "x"})
    request.user = DummyUser()
    request._dont_enforce_csrf_checks = True

    with patch(
        "celiaquia.views.cupo._BaseAccionLegajo._get_legajo_validado",
        side_effect=ValidationError("err"),
    ):
        response = CupoSuspenderLegajoView.as_view()(
            request, provincia_id=1, legajo_id=1
        )

    assert response.status_code == 400
    assert json.loads(response.content) == {
        "success": False,
        "message": "El legajo no es válido.",
    }
