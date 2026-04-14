"""
Regresión: lookup de ciudadano vía documento_unico_key en comedor_service
y celiaquia ciudadano_service.
Fase 4 — identidad ciudadano.

Tests unitarios con mocker (sin DB).
"""
from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from comedores.services.comedor_service import impl as comedor_module
from celiaquia.services import ciudadano_service as celiaquia_module


# ---------------------------------------------------------------------------
# comedor_service — _buscar_ciudadano_existente_por_dni_renaper
# ---------------------------------------------------------------------------

class TestComedorBuscarPorDni:

    def test_retorna_registro_estandar_via_documento_unico_key(self, mocker):
        """Cuando existe un registro ESTANDAR por documento_unico_key, lo devuelve."""
        estandar = SimpleNamespace(pk=1)
        mock_filter = mocker.patch(
            "comedores.services.comedor_service.impl.Ciudadano.objects.filter",
            return_value=SimpleNamespace(first=lambda: estandar),
        )

        result = comedor_module.ComedorService._buscar_ciudadano_existente_por_dni_renaper(
            "12345678"
        )

        assert result is estandar
        mock_filter.assert_called_once_with(documento_unico_key="DNI_12345678")

    def test_fallback_cuando_documento_unico_key_no_existe(self, mocker):
        """Si no hay registro por documento_unico_key, cae al fallback ordenado."""
        fallback = SimpleNamespace(pk=2)

        def _filter(**kwargs):
            if "documento_unico_key" in kwargs:
                return SimpleNamespace(first=lambda: None)
            # fallback: filter(tipo_documento=..., documento=...).order_by(...).first()
            qs = SimpleNamespace(
                order_by=lambda *a: SimpleNamespace(first=lambda: fallback)
            )
            return qs

        mocker.patch(
            "comedores.services.comedor_service.impl.Ciudadano.objects.filter",
            side_effect=_filter,
        )

        result = comedor_module.ComedorService._buscar_ciudadano_existente_por_dni_renaper(
            "12345678"
        )

        assert result is fallback

    def test_retorna_none_si_no_existe_ciudadano(self, mocker):
        def _filter(**kwargs):
            if "documento_unico_key" in kwargs:
                return SimpleNamespace(first=lambda: None)
            return SimpleNamespace(
                order_by=lambda *a: SimpleNamespace(first=lambda: None)
            )

        mocker.patch(
            "comedores.services.comedor_service.impl.Ciudadano.objects.filter",
            side_effect=_filter,
        )

        result = comedor_module.ComedorService._buscar_ciudadano_existente_por_dni_renaper(
            "99999999"
        )

        assert result is None


# ---------------------------------------------------------------------------
# celiaquia ciudadano_service — get_or_create_ciudadano lookup primario
# ---------------------------------------------------------------------------

class TestCeliaquiaCiudadanoLookup:

    def _patch_resolvers(self, mocker):
        mocker.patch.object(
            celiaquia_module.CiudadanoService, "_normalizar_tipo_documento",
            return_value="DNI"
        )
        mocker.patch.object(
            celiaquia_module.CiudadanoService, "_resolver_sexo", return_value=None
        )
        mocker.patch.object(
            celiaquia_module.CiudadanoService, "_resolver_provincia", return_value=None
        )
        mocker.patch.object(
            celiaquia_module.CiudadanoService, "_resolver_municipio", return_value=None
        )
        mocker.patch.object(
            celiaquia_module.CiudadanoService, "_resolver_localidad", return_value=None
        )
        mocker.patch.object(
            celiaquia_module.CiudadanoService, "_to_date", return_value=None
        )
        mocker.patch.object(
            celiaquia_module.CiudadanoService, "_resolver_nacionalidad", return_value=None
        )

    def test_lookup_primario_usa_documento_unico_key(self, mocker):
        """get_or_create_ciudadano intenta primero por documento_unico_key."""
        existing = SimpleNamespace(
            pk=9,
            sexo_id=None, sexo=None,
            nombre="", apellido="",
            fecha_nacimiento=None,
            nacionalidad_id=None, nacionalidad=None,
            provincia_id=None, provincia=None,
            municipio_id=None, municipio=None,
            localidad_id=None, localidad=None,
            calle="", altura=None, barrio="",
            piso_departamento="", codigo_postal="",
            telefono="", email="",
            save=mocker.Mock(),
        )

        filter_calls = []

        def _filter(**kwargs):
            filter_calls.append(set(kwargs.keys()))
            if "documento_unico_key" in kwargs:
                return SimpleNamespace(first=lambda: existing)
            return SimpleNamespace(
                order_by=lambda *a: SimpleNamespace(first=lambda: None)
            )

        self._patch_resolvers(mocker)
        mocker.patch(
            "celiaquia.services.ciudadano_service.Ciudadano.objects.filter",
            side_effect=_filter,
        )

        result = celiaquia_module.CiudadanoService.get_or_create_ciudadano(
            {"tipo_documento": "DNI", "documento": "123"}
        )

        assert result is existing
        # La primera llamada a filter debe incluir documento_unico_key
        assert any("documento_unico_key" in call for call in filter_calls)
