"""Tests unitarios para helpers de comedores.forms.comedor_form."""

from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError

from comedores.forms import comedor_form as module


class _QS:
    def __init__(self, obj=None, exc=None):
        self.obj = obj
        self.exc = exc

    def all(self):
        return self

    def filter(self, **_kwargs):
        return self

    def order_by(self, *_a):
        return self

    def get(self, **_kwargs):
        if self.exc:
            raise self.exc
        return self.obj


def _build_form_stub():
    form = module.ComedorForm.__new__(module.ComedorForm)
    form.previous_estado_chain = (None, None, None)
    form.current_user = None
    form.cleaned_data = {}
    form.add_error = lambda *args, **kwargs: None
    form.fields = {
        "estado_general": SimpleNamespace(initial=None, queryset=None),
        "subestado": SimpleNamespace(initial=None, queryset=None),
        "motivo": SimpleNamespace(initial=None, queryset=None),
    }
    form.initial = {}
    form.is_bound = False
    form.data = {}
    form.add_prefix = lambda x: x
    return form


def test_referente_clean_mail_paths(mocker):
    form = module.ReferenteForm.__new__(module.ReferenteForm)

    form.cleaned_data = {"mail": None}
    assert form.clean_mail() is None

    form.cleaned_data = {"mail": 123}
    with pytest.raises(ValidationError):
        form.clean_mail()

    form.cleaned_data = {"mail": "   "}
    assert form.clean_mail() is None

    validator = mocker.patch("comedores.forms.comedor_form.validate_unicode_email")
    form.cleaned_data = {"mail": "  a@b.com "}
    assert form.clean_mail() == "a@b.com"
    validator.assert_called_once_with("a@b.com")


def test_build_estado_tree_and_selected_helpers(mocker):
    form = _build_form_stub()

    detalle_a = SimpleNamespace(id=2, estado="d2")
    detalle_b = SimpleNamespace(id=1, estado="d1")
    proceso = SimpleNamespace(
        id=10,
        estado="proc",
        estado_actividad_id=5,
        estado_actividad=SimpleNamespace(estado="act"),
        estadodetalle_set=SimpleNamespace(all=lambda: [detalle_a, detalle_b]),
    )

    mocker.patch(
        "comedores.forms.comedor_form.EstadoProceso.objects.select_related",
        return_value=SimpleNamespace(
            prefetch_related=lambda *_a: SimpleNamespace(order_by=lambda *_b: [proceso])
        ),
    )

    tree = form._build_estado_tree()
    assert tree["5"]["label"] == "act"
    assert tree["5"]["procesos"][0]["detalles"][0]["id"] == 1

    actividad = SimpleNamespace(id=1)
    proceso_ok = SimpleNamespace(id=2, estado_actividad_id=1)
    detalle_ok = SimpleNamespace(id=3, estado_proceso_id=2)

    form.fields["estado_general"].queryset = _QS(obj=actividad)
    form.fields["subestado"].queryset = _QS(obj=proceso_ok)
    form.fields["motivo"].queryset = _QS(obj=detalle_ok)
    form.initial = {"estado_general": 1, "subestado": 2, "motivo": 3}

    assert form._get_selected_actividad() is actividad

    mocker.patch(
        "comedores.forms.comedor_form.EstadoProceso.objects.all",
        return_value=_QS(obj=proceso_ok),
    )
    assert form._get_selected_proceso(actividad) is proceso_ok

    mocker.patch(
        "comedores.forms.comedor_form.EstadoDetalle.objects.all",
        return_value=_QS(obj=detalle_ok),
    )
    assert form._get_selected_detalle(proceso_ok) is detalle_ok


def test_clean_validates_missing_and_mismatches(mocker):
    form = _build_form_stub()
    errors = []
    form.add_error = lambda field, message: errors.append((field, message))

    mocker.patch(
        "django.forms.models.BaseModelForm.clean", return_value={"estado_general": None}
    )
    out = form.clean()
    assert out["estado_general"] is None
    assert errors[0][0] == "estado_general"

    errors.clear()
    actividad = SimpleNamespace(id=1)
    proceso_bad = SimpleNamespace(id=2, estado_actividad_id=999)
    mocker.patch(
        "django.forms.models.BaseModelForm.clean",
        return_value={
            "estado_general": actividad,
            "subestado": proceso_bad,
            "motivo": None,
        },
    )
    form.clean()
    assert any(field == "subestado" for field, _ in errors)

    errors.clear()
    proceso_ok = SimpleNamespace(id=2, estado_actividad_id=1)
    detalle_bad = SimpleNamespace(estado_proceso_id=999)
    mocker.patch(
        "django.forms.models.BaseModelForm.clean",
        return_value={
            "estado_general": actividad,
            "subestado": proceso_ok,
            "motivo": detalle_bad,
        },
    )
    form.clean()
    assert any(field == "motivo" for field, _ in errors)


def test_save_preserves_ultimo_estado_and_sync(mocker):
    form = _build_form_stub()

    ultimo_original = object()
    comedor = SimpleNamespace(
        ultimo_estado=None,
        save=mocker.Mock(),
    )
    form.instance = SimpleNamespace(ultimo_estado=ultimo_original)
    form.cleaned_data = {
        "estado_general": SimpleNamespace(id=1),
        "subestado": SimpleNamespace(id=2),
        "motivo": SimpleNamespace(id=3),
    }

    mocker.patch("django.forms.models.BaseModelForm.save", return_value=comedor)
    form.save_m2m = mocker.Mock()
    sync = mocker.patch.object(form, "_sync_estado_historial")

    result = form.save(commit=True)
    assert result is comedor
    assert sync.called
    assert comedor.save.called


def test_sync_estado_historial_calls_only_when_changed(mocker):
    form = _build_form_stub()
    form.previous_estado_chain = (
        SimpleNamespace(id=1),
        SimpleNamespace(id=2),
        SimpleNamespace(id=3),
    )

    registrar = mocker.patch("comedores.forms.comedor_form.registrar_cambio_estado")

    form._sync_estado_historial(
        comedor="c",
        actividad=SimpleNamespace(id=1),
        proceso=SimpleNamespace(id=2),
        detalle=SimpleNamespace(id=3),
    )
    registrar.assert_not_called()

    form._sync_estado_historial(
        comedor="c",
        actividad=SimpleNamespace(id=1),
        proceso=SimpleNamespace(id=2),
        detalle=SimpleNamespace(id=4),
    )
    registrar.assert_called_once()
