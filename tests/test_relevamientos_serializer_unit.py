"""Unit tests for RelevamientoSerializer behavior."""

from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from relevamientos.serializer import RelevamientoSerializer


@pytest.mark.django_db
def test_clean_maps_nested_data_and_ids(mocker):
    """clean should normalize nested payload and replace related blocks with IDs."""
    instance = SimpleNamespace(
        comedor="comedor_old",
        funcionamiento="func_old",
        espacio="espacio_old",
        colaboradores="col_old",
        recursos="rec_old",
        compras="compras_old",
        anexo="anexo_old",
        punto_entregas="punto_old",
        prestacion="prest_old",
        excepcion="exc_old",
    )

    mocker.patch("relevamientos.serializer.format_fecha_django", return_value="2025-01-01")
    mocker.patch("relevamientos.serializer.validate_unicode_email")
    update_comedor = mocker.patch(
        "relevamientos.serializer.RelevamientoService.update_comedor", return_value=7
    )
    mocker.patch(
        "relevamientos.serializer.RelevamientoService.create_or_update_funcionamiento",
        return_value=SimpleNamespace(id=11),
    )
    mocker.patch(
        "relevamientos.serializer.RelevamientoService.create_or_update_espacio",
        return_value=SimpleNamespace(id=12),
    )
    mocker.patch(
        "relevamientos.serializer.RelevamientoService.create_or_update_colaboradores",
        return_value=SimpleNamespace(id=13),
    )
    mocker.patch(
        "relevamientos.serializer.RelevamientoService.create_or_update_recursos",
        return_value=SimpleNamespace(id=14),
    )
    mocker.patch(
        "relevamientos.serializer.RelevamientoService.create_or_update_compras",
        return_value=SimpleNamespace(id=15),
    )
    mocker.patch(
        "relevamientos.serializer.RelevamientoService.create_or_update_anexo",
        return_value=SimpleNamespace(id=16),
    )
    mocker.patch(
        "relevamientos.serializer.RelevamientoService.create_or_update_punto_entregas",
        return_value=SimpleNamespace(id=17),
    )
    mocker.patch(
        "relevamientos.serializer.RelevamientoService.create_or_update_prestacion",
        return_value=SimpleNamespace(id=18),
    )
    mocker.patch(
        "relevamientos.serializer.RelevamientoService.create_or_update_excepcion",
        return_value=SimpleNamespace(id=19),
    )
    responsables = mocker.patch(
        "relevamientos.serializer.RelevamientoService.create_or_update_responsable_y_referente",
        return_value=(101, 202),
    )

    payload = {
        "fecha_visita": "01/01/2025",
        "comedor": {"provincia": "BA"},
        "territorial": {"nombre": "Territorial", "gestionar_uid": "uid-1"},
        "funcionamiento": {"servicio_por_turnos": "Y"},
        "espacio": {"cocina": {}},
        "colaboradores": {},
        "recursos": {"recibe_otros": "N"},
        "compras": {},
        "anexo": {},
        "punto_entregas": {},
        "prestacion": {},
        "excepcion": {},
        "responsable_es_referente": "Y",
        "referente_comedor": {
            "celular": " 11-22.33 ",
            "documento": " 12.34-5 ",
            "mail": " ref@test.com ",
        },
        "responsable_relevamiento": {
            "celular": "",
            "documento": "",
            "mail": " resp@test.com ",
        },
        "sisoc_id": 5,
        "imagenes": "  img1, img2  ",
    }

    serializer = RelevamientoSerializer(instance=instance, data=payload, partial=True)
    out = serializer.clean()

    assert out is serializer
    assert serializer.initial_data["fecha_visita"] == "2025-01-01"
    assert serializer.initial_data["comedor"] == 7
    assert serializer.initial_data["territorial_nombre"] == "Territorial"
    assert serializer.initial_data["territorial_uid"] == "uid-1"
    assert "territorial" not in serializer.initial_data
    assert serializer.initial_data["funcionamiento"] == 11
    assert serializer.initial_data["espacio"] == 12
    assert serializer.initial_data["colaboradores"] == 13
    assert serializer.initial_data["recursos"] == 14
    assert serializer.initial_data["compras"] == 15
    assert serializer.initial_data["anexo"] == 16
    assert serializer.initial_data["punto_entregas"] == 17
    assert serializer.initial_data["prestacion"] == 18
    assert serializer.initial_data["excepcion"] == 19
    assert serializer.initial_data["responsable_es_referente"] is True
    assert serializer.initial_data["responsable_relevamiento"] == 101
    assert serializer.initial_data["referente_comedor"] == 202
    assert serializer.initial_data["imagenes"] == ["img1", "img2"]
    update_comedor.assert_called_once()
    called_comedor, called_instance = update_comedor.call_args[0]
    assert called_comedor["provincia"] == "BA"
    assert called_instance == "comedor_old"
    assert responsables.called

    args, _ = responsables.call_args
    assert args[1]["celular"] is None
    assert args[1]["documento"] is None
    assert args[2]["celular"] == "112233"
    assert args[2]["documento"] == "12345"


@pytest.mark.django_db
def test_clean_raises_on_invalid_nested_email(mocker):
    """clean should raise a serializer ValidationError for invalid nested email."""
    mocker.patch(
        "relevamientos.serializer.validate_unicode_email",
        side_effect=DjangoValidationError(["mail inválido"]),
    )

    serializer = RelevamientoSerializer(
        data={"referente_comedor": {"mail": "bad@example"}}, partial=True
    )

    with pytest.raises(serializers.ValidationError) as exc:
        serializer.clean()

    assert "referente_comedor" in exc.value.detail


@pytest.mark.django_db
def test_convert_yn_recursive_and_normalize_email_helpers():
    """Internal helpers should convert Y/N recursively and normalize emails."""
    serializer = RelevamientoSerializer(data={}, partial=True)

    payload = {
        "responsable_es_referente": "Y",
        "nested": [{"recibe_otros": "N"}, {"otro": "N"}],
    }
    serializer._convert_yn_to_boolean(payload)
    assert payload["responsable_es_referente"] is True
    assert payload["nested"][0]["recibe_otros"] is False
    assert payload["nested"][1]["otro"] is False

    assert serializer._normalize_email("  ") is None
    assert serializer._normalize_email("  x@y.com ") == "x@y.com"
    assert serializer._normalize_email(None) is None


@pytest.mark.django_db
def test_validate_success_and_reraise_on_error(mocker):
    """validate should proxy to ModelSerializer and reraise unexpected exceptions."""
    serializer = RelevamientoSerializer(data={}, partial=True)
    attrs = {"a": 1}

    mocker.patch("rest_framework.serializers.ModelSerializer.validate", return_value=attrs)
    assert serializer.validate(attrs) == attrs

    mocker.patch(
        "rest_framework.serializers.ModelSerializer.validate",
        side_effect=RuntimeError("boom"),
    )
    with pytest.raises(RuntimeError, match="boom"):
        serializer.validate(attrs)
