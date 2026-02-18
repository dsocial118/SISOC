"""Tests for test relevamientos helpers unit."""

from types import SimpleNamespace

from relevamientos.helpers import RelevamientoFormManager


class DummyForm:
    def __init__(self, post_data=None, instance=None):
        self.post_data = post_data
        self.instance = instance
        self.errors = {"field": ["error"]} if post_data == "invalid" else {}

    def is_valid(self):
        return self.post_data != "invalid"


def test_build_forms_uses_instance_when_present(mocker):
    mocker.patch.object(
        RelevamientoFormManager,
        "FORM_CLASSES",
        {"a_form": DummyForm, "b_form": DummyForm},
    )
    instance = object()

    forms = RelevamientoFormManager.build_forms(
        post_data="data",
        instance_map={"a_form": instance},
    )

    assert forms["a_form"].instance is instance
    assert forms["b_form"].instance is None
    assert forms["a_form"].post_data == "data"
    assert forms["b_form"].post_data == "data"


def test_validate_all_valid_and_get_errors_with_precomputed_results():
    forms = {
        "ok_form": DummyForm(post_data="data"),
        "bad_form": DummyForm(post_data="invalid"),
    }

    results = RelevamientoFormManager.validate_forms(forms)

    assert results == {"ok_form": True, "bad_form": False}
    assert RelevamientoFormManager.all_valid(forms, results) is False
    assert RelevamientoFormManager.get_errors(forms, results) == {
        "bad_form": {"field": ["error"]}
    }


def test_all_valid_and_get_errors_without_precomputed_results():
    forms = {
        "ok_form": DummyForm(post_data="data"),
        "bad_form": DummyForm(post_data="invalid"),
    }

    assert RelevamientoFormManager.all_valid(forms) is False
    assert RelevamientoFormManager.get_errors(forms) == {
        "bad_form": {"field": ["error"]}
    }


def test_get_comedor_context_merges_extra_fields(mocker):
    fake_values = {"id": 1, "nombre": "Comedor Norte"}
    mock_get = mocker.patch(
        "relevamientos.helpers.get_object_or_404", return_value=fake_values
    )
    mock_values = mocker.patch(
        "relevamientos.helpers.Comedor.objects.values", return_value="queryset"
    )

    result = RelevamientoFormManager.get_comedor_context(1, {"extra": "value"})

    mock_values.assert_called_once_with("id", "nombre")
    mock_get.assert_called_once_with("queryset", pk=1)
    assert result == {"id": 1, "nombre": "Comedor Norte", "extra": "value"}


def test_show_form_errors_emits_message_per_invalid_form(mocker):
    request = SimpleNamespace()
    forms = {
        "ok_form": DummyForm(post_data="data"),
        "bad_form": DummyForm(post_data="invalid"),
    }
    mock_error = mocker.patch("relevamientos.helpers.messages.error")

    RelevamientoFormManager.show_form_errors(request, forms)

    mock_error.assert_called_once_with(
        request, "Errores en bad_form: {'field': ['error']}"
    )
