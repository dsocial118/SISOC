"""Tests unitarios para ciudadanos.forms."""

from types import SimpleNamespace

from ciudadanos import forms as module


def test_get_cached_provincia_filter_choices_consulta_y_cachea(mocker):
    cache_get = mocker.patch("ciudadanos.forms.cache.get", return_value=None)
    cache_set = mocker.patch("ciudadanos.forms.cache.set")
    provincias = [
        SimpleNamespace(id=1, nombre="Buenos Aires"),
        SimpleNamespace(id=2, nombre="Cordoba"),
    ]
    order_by_mock = mocker.Mock(return_value=provincias)
    mocker.patch(
        "ciudadanos.forms.Provincia.objects.only",
        return_value=SimpleNamespace(order_by=order_by_mock),
    )

    result = module.get_cached_provincia_filter_choices()

    assert result == [("1", "Buenos Aires"), ("2", "Cordoba")]
    cache_get.assert_called_once_with(module.PROVINCIA_FILTER_CHOICES_CACHE_KEY)
    cache_set.assert_called_once()


def test_ciudadano_filtro_form_clean_provincia_devuelve_instancia(mocker):
    provincia = SimpleNamespace(id=7, nombre="Buenos Aires")
    mocker.patch(
        "ciudadanos.forms.get_cached_provincia_filter_choices",
        return_value=[("7", "Buenos Aires")],
    )
    mocker.patch(
        "ciudadanos.forms.Provincia.objects.only",
        return_value=SimpleNamespace(
            filter=lambda **_kwargs: SimpleNamespace(first=lambda: provincia)
        ),
    )

    form = module.CiudadanoFiltroForm(data={"provincia": "7"})

    assert form.is_valid() is True
    assert form.cleaned_data["provincia"] is provincia


def test_ciudadano_filtro_form_expone_tipo_registro(mocker):
    mocker.patch(
        "ciudadanos.forms.get_cached_provincia_filter_choices",
        return_value=[],
    )

    form = module.CiudadanoFiltroForm()

    assert "tipo_registro" in form.fields
