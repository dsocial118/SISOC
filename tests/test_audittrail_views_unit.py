"""Tests unitarios para audittrail.views."""

from datetime import date
from types import SimpleNamespace

import pytest
from django.http import Http404
from django.http import QueryDict

from audittrail import views as module
from audittrail.forms import AuditLogFilterForm
from audittrail.services import query_service


class _QS:
    def __init__(self):
        self.calls = []

    def annotate(self, **kwargs):
        self.calls.append((("annotate",), kwargs))
        return self

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
            "keyword": "estado",
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
    # keyword + model + object_pk + actor + start + end
    assert len(qs.calls) == 6
    assert any(
        call[1]
        in ({"changes__icontains": "estado"}, {"changes_text__icontains": "estado"})
        for call in qs.calls
    )

    invalid = _Form(valid=False)
    assert view._apply_filters(qs, invalid) is qs

    entry = SimpleNamespace(
        action=module.LogEntry.Action.UPDATE,
        actor=None,
        additional_data=None,
        cid=None,
    )
    mocker.patch(
        "django.views.generic.list.ListView.get_context_data",
        return_value={"entries": [entry]},
    )
    mocker.patch.object(view, "resolve_entry_changes", return_value={"x": 1})
    view.request = SimpleNamespace(
        GET=QueryDict("page=3&actor=ana"),
        path="/auditoria/",
        get_full_path=lambda: "/auditoria/?page=3&actor=ana",
    )
    view.filter_form = form
    ctx = view.get_context_data()
    assert ctx["title"] == "Auditoría de cambios"
    assert ctx["querystring"] == "actor=ana"
    assert ctx["active_filters"][0]["label"] == "Texto"
    assert ctx["active_filters"][0]["value"] == "estado"


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
        changes_display_dict={},
        content_type=SimpleNamespace(model_class=lambda: None),
        action=module.LogEntry.Action.UPDATE,
        actor=None,
        additional_data=None,
        cid=None,
    )

    mocker.patch(
        "django.views.generic.detail.DetailView.get_context_data", return_value={}
    )
    mocker.patch.object(view, "resolve_entry_changes", return_value={"k": "v"})
    mocker.patch.object(view, "_get_back_url", return_value="/auditoria/")

    ctx = view.get_context_data()
    assert ctx["changes"] == {"k": "v"}

    # método explícito de passthrough
    passthrough = module.AuditLogDetailView.resolve_entry_changes(view, view.object)
    assert isinstance(passthrough, dict)


def test_decorate_entries_for_display_sets_actor_action_and_bulk_grouping():
    view = module.BaseAuditLogListView()

    actor = SimpleNamespace(
        username="ana",
        first_name="Ana",
        last_name="Pérez",
        get_username=lambda: "ana",
    )
    entries = [
        SimpleNamespace(
            action=module.LogEntry.Action.UPDATE,
            actor=actor,
            resolved_changes={"campo": {"old": "a", "new": "b"}},
            cid="req-1",
        ),
        SimpleNamespace(
            action=module.LogEntry.Action.UPDATE,
            actor=None,
            resolved_changes={},
            cid="req-1",
        ),
    ]

    view._decorate_entries_for_display(entries)

    assert entries[0].ui_actor_primary == "ana"
    assert entries[0].ui_actor_secondary == "Ana Pérez"
    assert entries[0].ui_action_label == "Actualización"
    assert entries[0].ui_bulk_grouped is True
    assert entries[0].ui_bulk_sequence_start is True
    assert entries[1].ui_bulk_sequence_continuation is True
    assert entries[1].ui_actor_primary == "Proceso"
    assert entries[1].ui_has_diffs is False


def test_keyword_filter_form_normalizes_and_applies_and_terms():
    form = AuditLogFilterForm(
        data={
            "keyword": "  estado   aprobado  ",
            "start_date": "2024-01-01",
            "end_date": "2024-01-10",
        }
    )
    assert form.is_valid() is True
    assert form.cleaned_data["keyword"] == "estado aprobado"

    qs = _QS()
    out = query_service.apply_keyword_filter(qs, form.cleaned_data["keyword"])
    assert out is qs
    assert len(qs.calls) == 2
    first_lookup = next(iter(qs.calls[0][1].keys()))
    second_lookup = next(iter(qs.calls[1][1].keys()))
    assert first_lookup in {"changes__icontains", "changes_text__icontains"}
    assert second_lookup in {"changes__icontains", "changes_text__icontains"}
    assert qs.calls[0][1][first_lookup] == "estado"
    assert qs.calls[1][1][second_lookup] == "aprobado"


def test_filter_form_requires_date_range_for_text_or_field_search():
    form = AuditLogFilterForm(data={"keyword": "aprobado"})
    assert form.is_valid() is False
    assert form.non_field_errors()

    form2 = AuditLogFilterForm(
        data={
            "field_name": "estado",
            "start_date": "2024-01-01",
            "end_date": "2024-05-01",
        }
    )
    assert form2.is_valid() is False
    assert form2.non_field_errors()


def test_actor_legible_helpers_and_grouping_heuristico_service():
    actor = SimpleNamespace(
        username="ana",
        first_name="Ana",
        last_name="Pérez",
        email="ana@example.com",
        get_username=lambda: "ana",
    )
    actor_ui = query_service.format_actor_display(actor)
    assert actor_ui["primary"] == "ana"
    assert actor_ui["secondary"] == "Ana Pérez"
    assert actor_ui["is_fallback"] is False

    fallback_ui = query_service.format_actor_display(None, fallback_label="Proceso")
    assert fallback_ui["primary"] == "Proceso"
    assert fallback_ui["is_fallback"] is True

    entries = [
        SimpleNamespace(
            ui_bulk_marker=None,
            ui_bulk_source="cid",
            cid="req-1",
            additional_data=None,
        ),
        SimpleNamespace(
            ui_bulk_marker=None,
            ui_bulk_source="cid",
            cid="req-1",
            additional_data=None,
        ),
        SimpleNamespace(
            ui_bulk_marker=None,
            ui_bulk_source=None,
            cid="req-2",
            additional_data=None,
        ),
    ]

    def _decorate(entry):
        entry.ui_bulk_marker = (
            f"cid:{entry.cid}" if getattr(entry, "cid", None) else None
        )
        entry.ui_bulk_source = "cid" if getattr(entry, "cid", None) else None
        return entry

    query_service.decorate_entries_for_display(
        entries=entries, decorate_entry=_decorate
    )
    assert entries[0].ui_bulk_grouped is True
    assert entries[0].ui_bulk_sequence_start is True
    assert entries[1].ui_bulk_sequence_continuation is True
    assert entries[2].ui_bulk_grouped is False


def test_query_service_new_filters_and_export_guards(mocker):
    qs = _QS()
    out = query_service.apply_filters(
        qs,
        {
            "field_name": "estado",
            "origin": "system",
            "batch_key": "lote-1",
            "keyword": "",
            "model": "",
            "object_pk": "",
            "actor": "",
            "action": "",
            "start_date": None,
            "end_date": None,
        },
    )
    assert out is qs
    assert any(
        call[1].get("audittrail_meta__batch_key__icontains") == "lote-1"
        for call in qs.calls
    )

    export_errors = query_service.validate_export_request(
        {
            "model": "",
            "object_pk": "",
            "start_date": None,
            "end_date": None,
        }
    )
    assert export_errors

    assert query_service._build_mysql_boolean_fulltext_query("aprobado convenio 1510")
    mocker.patch(
        "audittrail.services.query_service.impl._mysql_can_use_fulltext", return_value=True
    )
    qs_ft = _QS()
    out_ft = query_service.apply_optimized_keyword_filter(qs_ft, "aprobado convenio")
    assert out_ft is qs_ft
    assert any(call[0] == ("annotate",) for call in qs_ft.calls)


def test_instance_allowlist_validation_rejects_untracked_model():
    with pytest.raises(Http404):
        query_service.get_tracked_content_type_or_404(
            app_label="nope",
            model_name="invalido",
        )


def test_decorate_entry_for_display_prefers_phase2_meta_snapshot_and_batch_key():
    entry = SimpleNamespace(
        action=module.LogEntry.Action.UPDATE,
        actor=None,
        resolved_changes={"campo": {"old": "x", "new": "y"}},
        cid="legacy-cid",
        additional_data=None,
        audittrail_meta=SimpleNamespace(
            actor_username_snapshot="fixer.bot",
            actor_full_name_snapshot="Fix Bot",
            actor_display_snapshot="fixer.bot",
            source="management_command:reparar_auditoria",
            batch_key="fix-20260225-01",
        ),
    )

    action_ui = {
        "label": "Actualización",
        "badge_class": "bg-primary",
        "is_delete": False,
    }
    query_service.decorate_entry_for_display(entry=entry, action_ui=action_ui)

    assert entry.ui_actor_primary == "fixer.bot"
    assert entry.ui_actor_secondary == "Fix Bot"
    assert entry.ui_source == "management_command:reparar_auditoria"
    assert entry.ui_source_label.startswith("Comando")
    assert entry.ui_bulk_source == "batch_key"
    assert entry.ui_bulk_marker == "batch_key:fix-20260225-01"
