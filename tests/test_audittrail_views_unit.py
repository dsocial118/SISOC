"""Tests unitarios para audittrail.views."""

from datetime import date
from types import SimpleNamespace

from django.http import QueryDict

from audittrail import views as module


class _QS:
    def __init__(self):
        self.calls = []

    def filter(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self


class _Form:
    def __init__(self, valid=True, cleaned=None):
        self._valid = valid
        self.cleaned_data = cleaned or {}
        self.initial = {}

    def is_valid(self):
        return self._valid


def test_extract_value_and_format_value_basic_paths():
    mixin = module.AuditLogResolveMixin()

    assert mixin._extract_value({"old": 1, "new": 2}, "old") == 1
    assert mixin._extract_value([3, 4], "new") == 4
    assert mixin._extract_value("x", "old") == "x"

    empty = mixin._format_value(None, None, {})
    assert "No cargado" in str(empty)
    assert mixin._format_value(True, None, {}) == "Sí"
    assert mixin._format_value(False, None, {}) == "No"
    assert mixin._format_value("core.user.12", None, {}) == "User #12"
    assert mixin._format_value("core.user.abc", None, {}) == "User (abc)"


def test_resolve_entry_changes_with_model_field_lookup_failure():
    mixin = module.AuditLogResolveMixin()

    class _Meta:
        @staticmethod
        def get_field(_name):
            raise Exception("missing")

    model_cls = SimpleNamespace(_meta=_Meta())
    content_type = SimpleNamespace(model_class=lambda: model_cls)
    entry = SimpleNamespace(
        content_type=content_type,
        changes_display_dict={
            "campo": [None, "valor"],
            "campo2": {"old": "core.item.1", "new": "ok"},
        },
    )

    out = mixin.resolve_entry_changes(entry)
    assert "campo" in out and "campo2" in out
    assert "No cargado" in str(out["campo"]["old"])
    assert out["campo2"]["old"] == "Item #1"


def test_base_apply_filters_and_context_data(mocker):
    view = module.BaseAuditLogListView()
    qs = _QS()

    form = _Form(
        valid=True,
        cleaned={
            "model": "centro",
            "object_pk": 10,
            "actor": "ana",
            "action": "",
            "start_date": date(2024, 1, 1),
            "end_date": date(2024, 1, 2),
        },
    )

    out = view._apply_filters(qs, form)
    assert out is qs
    # model + object_pk + actor + start + end
    assert len(qs.calls) == 5

    invalid = _Form(valid=False)
    assert view._apply_filters(qs, invalid) is qs

    entry = SimpleNamespace()
    mocker.patch(
        "django.views.generic.list.ListView.get_context_data",
        return_value={"entries": [entry]},
    )
    mocker.patch.object(view, "resolve_entry_changes", return_value={"x": 1})
    view.request = SimpleNamespace(GET=QueryDict("page=3&actor=ana"))
    view.filter_form = form
    ctx = view.get_context_data()
    assert ctx["title"] == "Auditoría de cambios"
    assert ctx["querystring"] == "actor=ana"


def test_audit_instance_choices_form_and_context(mocker):
    view = module.AuditLogInstanceView()
    view.kwargs = {"app_label": "core", "model_name": "ciudadano", "object_pk": 7}

    mocker.patch(
        "audittrail.views.TRACKED_MODELS",
        [("core", "ciudadano", "Ciudadano")],
    )
    assert view.get_tracked_choices() == [("core.ciudadano", "Ciudadano")]

    mocker.patch("audittrail.views.BaseAuditLogListView.get_form", return_value=_Form())
    form = view.get_form()
    assert form.initial["model"] == "core.ciudadano"
    assert form.initial["object_pk"] == 7

    mocker.patch(
        "audittrail.views.BaseAuditLogListView.get_context_data", return_value={}
    )
    ctx = view.get_context_data()
    assert ctx["is_instance_view"] is True
    assert ctx["instance_object_pk"] == 7


def test_audit_detail_get_context_data_and_resolver_passthrough(mocker):
    view = module.AuditLogDetailView()
    view.object = SimpleNamespace(
        changes_display_dict={}, content_type=SimpleNamespace(model_class=lambda: None)
    )

    mocker.patch(
        "django.views.generic.detail.DetailView.get_context_data", return_value={}
    )
    mocker.patch.object(view, "resolve_entry_changes", return_value={"k": "v"})

    ctx = view.get_context_data()
    assert ctx["changes"] == {"k": "v"}

    # método explícito de passthrough
    passthrough = module.AuditLogDetailView.resolve_entry_changes(view, view.object)
    assert isinstance(passthrough, dict)
