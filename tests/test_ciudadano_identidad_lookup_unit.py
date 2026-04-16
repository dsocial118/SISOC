"""
Regresión: lookup de ciudadano vía documento_unico_key en comedor_service
y celiaquia ciudadano_service.
Fase 4 — identidad ciudadano.

Tests unitarios con mocker (sin DB).
"""

from types import SimpleNamespace

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

        result = (
            comedor_module.ComedorService._buscar_ciudadano_existente_por_dni_renaper(
                "12345678"
            )
        )

        assert result is estandar
        expected_documento = "{}_{}".format("DNI", "12345678")
        mock_filter.assert_called_once_with(documento_unico_key=expected_documento)

    def test_fallback_cuando_documento_unico_key_no_existe(self, mocker):
        """Si no hay documento_unico_key, prioriza un registro ESTANDAR."""
        fallback = SimpleNamespace(pk=2)
        filter_calls = []

        def _filter(**kwargs):
            filter_calls.append(kwargs)
            if "documento_unico_key" in kwargs:
                return SimpleNamespace(first=lambda: None)
            if (
                kwargs.get("tipo_registro_identidad")
                == comedor_module.Ciudadano.TIPO_REGISTRO_ESTANDAR
            ):
                return SimpleNamespace(first=lambda: fallback)
            return SimpleNamespace(first=lambda: None)

        mocker.patch(
            "comedores.services.comedor_service.impl.Ciudadano.objects.filter",
            side_effect=_filter,
        )

        result = (
            comedor_module.ComedorService._buscar_ciudadano_existente_por_dni_renaper(
                "12345678"
            )
        )

        assert result is fallback
        assert (
            filter_calls[1]["tipo_registro_identidad"]
            == comedor_module.Ciudadano.TIPO_REGISTRO_ESTANDAR
        )

    def test_retorna_none_si_no_existe_ciudadano(self, mocker):
        def _filter(**kwargs):
            return SimpleNamespace(first=lambda: None)

        mocker.patch(
            "comedores.services.comedor_service.impl.Ciudadano.objects.filter",
            side_effect=_filter,
        )

        result = (
            comedor_module.ComedorService._buscar_ciudadano_existente_por_dni_renaper(
                "99999999"
            )
        )

        assert result is None


# ---------------------------------------------------------------------------
# celiaquia ciudadano_service — get_or_create_ciudadano lookup primario
# ---------------------------------------------------------------------------


class TestCeliaquiaCiudadanoLookup:

    def _patch_resolvers(self, mocker):
        mocker.patch.object(
            celiaquia_module.CiudadanoService,
            "_normalizar_tipo_documento",
            return_value="DNI",
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
            celiaquia_module.CiudadanoService,
            "_resolver_nacionalidad",
            return_value=None,
        )

    def test_lookup_primario_usa_documento_unico_key(self, mocker):
        """get_or_create_ciudadano intenta primero por documento_unico_key."""
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

    def test_lookup_fallback_prefiere_estandar_antes_de_crear(self, mocker):
        existing = SimpleNamespace(
            pk=10,
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
        filter_calls = []

        def _filter(**kwargs):
            filter_calls.append(kwargs)
            if "documento_unico_key" in kwargs:
                return SimpleNamespace(first=lambda: None)
            if (
                kwargs.get("tipo_registro_identidad")
                == celiaquia_module.Ciudadano.TIPO_REGISTRO_ESTANDAR
            ):
                return SimpleNamespace(first=lambda: existing)
            return SimpleNamespace(first=lambda: None)

        self._patch_resolvers(mocker)
        create_mock = mocker.patch(
            "celiaquia.services.ciudadano_service.Ciudadano.objects.create"
        )
        mocker.patch(
            "celiaquia.services.ciudadano_service.Ciudadano.objects.filter",
            side_effect=_filter,
        )

        result = celiaquia_module.CiudadanoService.get_or_create_ciudadano(
            {"tipo_documento": "DNI", "documento": "123"}
        )

        assert result is existing
        assert (
            filter_calls[1]["tipo_registro_identidad"]
            == celiaquia_module.Ciudadano.TIPO_REGISTRO_ESTANDAR
        )
        create_mock.assert_not_called()
