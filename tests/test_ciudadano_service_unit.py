"""Tests for test ciudadano service unit."""

from contextlib import nullcontext
from datetime import date, datetime
from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError

from celiaquia.services import ciudadano_service as module


class _FirstResult:
    def __init__(self, value):
        self._value = value

    def first(self):
        return self._value


def test_to_date_parsing_and_invalid_cases():
    assert module.CiudadanoService._to_date(None) is None
    assert module.CiudadanoService._to_date(date(2020, 1, 1)) == date(2020, 1, 1)
    assert module.CiudadanoService._to_date(datetime(2020, 1, 1, 10, 0, 0)) == datetime(2020, 1, 1, 10, 0, 0)
    assert module.CiudadanoService._to_date("2020/02/03 11:22:33") == date(2020, 2, 3)

    with pytest.raises(ValidationError):
        module.CiudadanoService._to_date("31-02-2024")

    with pytest.raises(ValidationError):
        module.CiudadanoService._to_date("fecha-no-valida")


def test_tipo_documento_and_resolvers_basics(mocker):
    default = module.CiudadanoService._normalizar_tipo_documento(None)
    assert module.CiudadanoService._normalizar_tipo_documento("dni") == default

    with pytest.raises(ValidationError):
        module.CiudadanoService._normalizar_tipo_documento("ZZ")

    sexo_obj = object()
    nac_obj = object()
    mocker.patch(
        "celiaquia.services.ciudadano_service.Sexo.objects.filter",
        return_value=_FirstResult(sexo_obj),
    )
    mocker.patch(
        "celiaquia.services.ciudadano_service.Nacionalidad.objects.filter",
        return_value=_FirstResult(nac_obj),
    )
    assert module.CiudadanoService._resolver_sexo("1") is sexo_obj
    assert module.CiudadanoService._resolver_sexo("Masculino") is sexo_obj
    assert module.CiudadanoService._resolver_nacionalidad("2") is nac_obj
    assert module.CiudadanoService._resolver_nacionalidad("Argentina") is nac_obj


def test_resolver_ubicacion_paths(mocker):
    provincia = SimpleNamespace(pk=10)
    municipio = SimpleNamespace(pk=20)
    localidad = SimpleNamespace(pk=30)

    mocker.patch(
        "celiaquia.services.ciudadano_service.Provincia.objects.get",
        return_value=provincia,
    )
    assert module.CiudadanoService._resolver_provincia("10") is provincia
    with pytest.raises(ValidationError):
        module.CiudadanoService._resolver_provincia("abc")

    with pytest.raises(ValidationError):
        module.CiudadanoService._resolver_municipio("20", None)

    mocker.patch(
        "celiaquia.services.ciudadano_service.Municipio.objects.get",
        return_value=municipio,
    )
    assert module.CiudadanoService._resolver_municipio("20", provincia) is municipio

    mocker.patch(
        "celiaquia.services.ciudadano_service.Localidad.objects.filter",
        return_value=_FirstResult(localidad),
    )
    assert module.CiudadanoService._resolver_localidad("30", None) is localidad


def test_get_or_create_ciudadano_validation_errors(mocker):
    mocker.patch.object(module.CiudadanoService, "_normalizar_tipo_documento", return_value="DNI")
    with pytest.raises(ValidationError):
        module.CiudadanoService.get_or_create_ciudadano({"tipo_documento": "DNI"})

    mocker.patch.object(module.CiudadanoService, "_resolver_sexo", return_value=None)
    with pytest.raises(ValidationError):
        module.CiudadanoService.get_or_create_ciudadano(
            {"tipo_documento": "DNI", "documento": "1", "sexo": "X"}
        )

    mocker.patch.object(module.CiudadanoService, "_resolver_sexo", return_value=SimpleNamespace(pk=1))
    mocker.patch.object(module.CiudadanoService, "_resolver_provincia", return_value=None)
    mocker.patch.object(module.CiudadanoService, "_resolver_municipio", return_value=None)
    mocker.patch.object(module.CiudadanoService, "_resolver_localidad", return_value=None)
    mocker.patch.object(module.CiudadanoService, "_to_date", return_value=None)
    mocker.patch.object(module.CiudadanoService, "_resolver_nacionalidad", return_value=None)
    with pytest.raises(ValidationError):
        module.CiudadanoService.get_or_create_ciudadano(
            {
                "tipo_documento": "DNI",
                "documento": "1",
                "sexo": "M",
                "nacionalidad": "X",
            }
        )


def test_get_or_create_ciudadano_updates_existing(mocker):
    existing = SimpleNamespace(
        pk=9,
        sexo_id=None,
        sexo=None,
        nombre="",
        apellido="",
        fecha_nacimiento=None,
        nacionalidad_id=None,
        nacionalidad=None,
        provincia_id=None,
        provincia=None,
        municipio_id=None,
        municipio=None,
        localidad_id=None,
        localidad=None,
        calle="",
        altura=None,
        barrio="",
        piso_departamento="",
        codigo_postal="",
        telefono="",
        email="",
        save=mocker.Mock(),
    )

    mocker.patch.object(module.CiudadanoService, "_normalizar_tipo_documento", return_value="DNI")
    mocker.patch.object(module.CiudadanoService, "_resolver_sexo", return_value=SimpleNamespace(pk=1))
    mocker.patch.object(module.CiudadanoService, "_resolver_provincia", return_value=SimpleNamespace(pk=2))
    mocker.patch.object(module.CiudadanoService, "_resolver_municipio", return_value=SimpleNamespace(pk=3))
    mocker.patch.object(module.CiudadanoService, "_resolver_localidad", return_value=SimpleNamespace(pk=4))
    mocker.patch.object(module.CiudadanoService, "_to_date", return_value=date(2000, 1, 1))
    mocker.patch.object(module.CiudadanoService, "_resolver_nacionalidad", return_value=SimpleNamespace(pk=5))
    mocker.patch(
        "celiaquia.services.ciudadano_service.Ciudadano.objects.filter",
        return_value=_FirstResult(existing),
    )

    result = module.CiudadanoService.get_or_create_ciudadano(
        {
            "tipo_documento": "DNI",
            "documento": "123",
            "nombre": "N",
            "apellido": "A",
            "calle": "C",
            "altura": 100,
            "barrio": "B",
            "piso_departamento": "1A",
            "codigo_postal": "7600",
            "telefono": "123",
            "email": "a@b.c",
        }
    )

    assert result is existing
    assert existing.save.called


def test_get_or_create_ciudadano_create_path_handles_program_missing(mocker):
    created = SimpleNamespace(pk=1)
    mocker.patch.object(module.CiudadanoService, "_normalizar_tipo_documento", return_value="DNI")
    mocker.patch.object(module.CiudadanoService, "_resolver_sexo", return_value=None)
    mocker.patch.object(module.CiudadanoService, "_resolver_provincia", return_value=None)
    mocker.patch.object(module.CiudadanoService, "_resolver_municipio", return_value=None)
    mocker.patch.object(module.CiudadanoService, "_resolver_localidad", return_value=None)
    mocker.patch.object(module.CiudadanoService, "_to_date", return_value=None)
    mocker.patch.object(module.CiudadanoService, "_resolver_nacionalidad", return_value=None)

    first_none = _FirstResult(None)
    mocker.patch(
        "celiaquia.services.ciudadano_service.Ciudadano.objects.filter",
        return_value=first_none,
    )
    mocker.patch(
        "celiaquia.services.ciudadano_service.Ciudadano.objects.create",
        return_value=created,
    )
    mocker.patch("celiaquia.services.ciudadano_service.transaction.atomic", return_value=nullcontext())

    from core.models import Programa

    mocker.patch("core.models.Programa.objects.get", side_effect=Programa.DoesNotExist)
    cp_mock = mocker.patch("ciudadanos.models.CiudadanoPrograma.objects.get_or_create")

    out = module.CiudadanoService.get_or_create_ciudadano(
        {"tipo_documento": "DNI", "documento": "777"}, usuario="u"
    )
    assert out is created
    cp_mock.assert_not_called()
