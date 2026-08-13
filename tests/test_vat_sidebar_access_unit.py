"""Contratos de navegacion VAT desacoplados de los template tags globales."""

from types import SimpleNamespace

from VAT.sidebar_access import es_usuario_solo_vat
from core.templatetags.custom_filters import is_vat_sidebar_only


def test_vat_sidebar_only_delega_en_el_predicado_registrado(mocker):
    resolver = mocker.patch(
        "core.templatetags.custom_filters.resolver_predicado_sidebar",
        return_value=True,
    )
    user = SimpleNamespace(is_authenticated=True, is_superuser=False)

    assert is_vat_sidebar_only(user) is True
    resolver.assert_called_once_with("vat", user)


def test_es_usuario_solo_vat_respeta_usuarios_no_autenticados_y_superusuarios(mocker):
    mocker.patch("VAT.sidebar_access.is_vat_sse", return_value=True)
    user = SimpleNamespace(is_authenticated=True, is_superuser=False)

    assert es_usuario_solo_vat(user) is True
    assert (
        es_usuario_solo_vat(SimpleNamespace(is_authenticated=False, is_superuser=False))
        is False
    )
    assert (
        es_usuario_solo_vat(SimpleNamespace(is_authenticated=True, is_superuser=True))
        is False
    )
