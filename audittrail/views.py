import csv
import json
import logging
import re

from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import models
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.safestring import mark_safe
from django.views.generic import DetailView, ListView

from auditlog.models import LogEntry
from audittrail.constants import TRACKED_MODELS, tracked_model_choices
from audittrail.forms import AuditLogFilterForm
from audittrail.services import query_service


AUDITTRAIL_ACCESS_LOGGER = logging.getLogger("audittrail.access")


class AuditLogResolveMixin:
    """
    Mixin para normalizar y formatear diffs de auditlog.
    """

    BULK_METADATA_KEYS = query_service.BULK_METADATA_KEYS

    def resolve_entry_changes(self, entry):
        """
        Normaliza los valores old/new y resuelve FKs a su __str__ para que la UI muestre
        algo legible. Evita consultas innecesarias para valores nulos o vacíos.
        """
        changes = getattr(entry, "changes_display_dict", None) or {}
        model_cls = entry.content_type.model_class()
        resolved = {}
        fk_cache = getattr(self, "_audit_fk_cache", None)
        if fk_cache is None:
            fk_cache = {}
            self._audit_fk_cache = fk_cache

        for field_name, change in changes.items():
            field = None
            if model_cls:
                try:
                    field = model_cls._meta.get_field(field_name)
                except Exception:  # noqa: BLE001
                    field = None

            old_val = self._extract_value(change, "old")
            new_val = self._extract_value(change, "new")

            resolved[field_name] = {
                "old": self._format_value(old_val, field, fk_cache),
                "new": self._format_value(new_val, field, fk_cache),
            }

        return resolved

    @staticmethod
    def _format_actor_display(actor, fallback_label="Sistema"):
        return query_service.format_actor_display(actor, fallback_label=fallback_label)

    @staticmethod
    def _get_action_ui(entry):
        if entry.action == LogEntry.Action.CREATE:
            return {
                "label": "Creación",
                "badge_class": "bg-success",
                "is_delete": False,
            }
        if entry.action == LogEntry.Action.UPDATE:
            return {
                "label": "Actualización",
                "badge_class": "bg-primary",
                "is_delete": False,
            }
        if entry.action == LogEntry.Action.DELETE:
            return {
                "label": "Eliminación",
                "badge_class": "bg-danger",
                "is_delete": True,
            }
        return {
            "label": entry.get_action_display(),
            "badge_class": "bg-secondary",
            "is_delete": False,
        }

    def _extract_bulk_marker(self, entry):
        return query_service.extract_bulk_marker(
            entry,
            bulk_metadata_keys=self.BULK_METADATA_KEYS,
        )

    @staticmethod
    def _bulk_source_label(source):
        return query_service.bulk_source_label(source)

    def _decorate_entry_for_display(self, entry):
        return query_service.decorate_entry_for_display(
            entry=entry,
            action_ui=self._get_action_ui(entry),
            bulk_metadata_keys=self.BULK_METADATA_KEYS,
        )

    def _decorate_entries_for_display(self, entries):
        return query_service.decorate_entries_for_display(
            entries=entries,
            decorate_entry=self._decorate_entry_for_display,
        )

    def _build_active_filter_chips(self, form):
        if not form or not form.is_valid():
            return []

        data = form.cleaned_data
        form_fields = getattr(form, "fields", {})
        action_field = form_fields.get("action") if hasattr(form_fields, "get") else None
        action_choices = dict(getattr(action_field, "choices", []))
        chips = []

        if data.get("keyword"):
            chips.append({"label": "Texto", "value": data["keyword"]})
        if data.get("field_name"):
            chips.append({"label": "Campo", "value": data["field_name"]})
        if data.get("model"):
            chips.append({"label": "Modelo", "value": data["model"]})
        if data.get("object_pk"):
            chips.append({"label": "ID", "value": str(data["object_pk"])})
        if data.get("actor"):
            chips.append({"label": "Usuario", "value": data["actor"]})
        if data.get("origin"):
            origin_field = form_fields.get("origin") if hasattr(form_fields, "get") else None
            origin_choices = dict(getattr(origin_field, "choices", []))
            chips.append(
                {
                    "label": "Origen",
                    "value": origin_choices.get(data["origin"], str(data["origin"])),
                }
            )
        if data.get("batch_key"):
            chips.append({"label": "Batch key", "value": data["batch_key"]})
        if data.get("action") not in (None, ""):
            chips.append(
                {
                    "label": "Evento",
                    "value": action_choices.get(data["action"], str(data["action"])),
                }
            )
        if data.get("start_date"):
            chips.append({"label": "Desde", "value": data["start_date"].isoformat()})
        if data.get("end_date"):
            chips.append({"label": "Hasta", "value": data["end_date"].isoformat()})

        return chips

    @staticmethod
    def _extract_value(change, key):
        if isinstance(change, dict):
            return change.get(key)
        if isinstance(change, (list, tuple)):
            if key == "old" and len(change) > 0:
                return change[0]
            if key == "new" and len(change) > 1:
                return change[1]
        return change

    @staticmethod
    def _get_fk_cache_key(field, value):
        return (field.remote_field.model, value)

    def _format_value(
        self, value, field, fk_cache
    ):  # pylint: disable=too-many-return-statements
        # Chequear valores vacíos o None
        if value in (None, "", [], ()) or (
            isinstance(value, str)
            and (
                value.strip().lower() == "none"
                or value.strip().lower().endswith(".none")
            )
        ):
            return mark_safe("<em>No cargado</em>")

        # Formatear booleanos
        if isinstance(value, bool):
            return "Sí" if value else "No"

        # Formatear strings con patrón "app.Model.pk"
        if isinstance(value, str):
            cleaned = value.strip()
            dotted = cleaned.split(".")
            if len(dotted) >= 3 and re.fullmatch(r"[a-z_]+", dotted[0]) and dotted[1]:
                model_label = dotted[1].replace("_", " ").title()
                pk_part = dotted[-1]
                return (
                    f"{model_label} #{pk_part}"
                    if pk_part.isdigit()
                    else f"{model_label} ({pk_part})"
                )

        # Formatear ForeignKeys
        if field and isinstance(field, (models.ForeignKey, models.OneToOneField)):
            fk_key = self._get_fk_cache_key(field, value)
            obj = fk_cache.get(fk_key)
            if fk_key not in fk_cache:
                try:
                    obj = field.remote_field.model.objects.filter(pk=value).first()
                except Exception:  # noqa: BLE001
                    obj = None
                fk_cache[fk_key] = obj

            try:
                if obj:
                    label = str(obj)
                    if "object (" in label and ")" in label:
                        model_name = field.remote_field.model._meta.verbose_name.title()
                        return f"{model_name} #{value}"
                    return label
            except Exception:  # noqa: BLE001
                pass

        return value


class BaseAuditLogListView(
    AuditLogResolveMixin, LoginRequiredMixin, PermissionRequiredMixin, ListView
):
    model = LogEntry
    template_name = "audittrail/log_list.html"
    context_object_name = "entries"
    paginate_by = 25
    permission_required = "auditlog.view_logentry"
    export_permission = "audittrail.export_auditlog"

    def get_action_choices(self):
        return [
            ("", "Todos los eventos"),
            (LogEntry.Action.CREATE, "Creación"),
            (LogEntry.Action.UPDATE, "Actualización"),
            (LogEntry.Action.DELETE, "Eliminación"),
        ]

    def _apply_filters(self, qs, form: AuditLogFilterForm):
        if not form.is_valid():
            return qs
        return query_service.apply_filters(qs, form.cleaned_data)

    def get_form(self):
        return AuditLogFilterForm(self.request.GET or None)

    def get(self, request, *args, **kwargs):
        export_format = (request.GET.get("export") or "").strip().lower()
        if export_format not in {"csv", "json"}:
            return super().get(request, *args, **kwargs)

        self.object_list = self.get_queryset()
        filter_form = getattr(self, "filter_form", None)
        if not filter_form or not filter_form.is_valid():
            return self.render_to_response(self.get_context_data())

        if not request.user.has_perm(self.export_permission):
            self._log_export_event(
                export_format=export_format,
                status="denied",
                result_count=0,
                extra={"reason": "missing_permission"},
            )
            raise PermissionDenied("No tenés permiso para exportar auditoría.")

        export_errors = query_service.validate_export_request(filter_form.cleaned_data)
        if export_errors:
            for error in export_errors:
                filter_form.add_error(None, error)
            return self.render_to_response(self.get_context_data())

        total_rows = self.object_list.count()
        if total_rows > query_service.EXPORT_MAX_ROWS:
            filter_form.add_error(
                None,
                (
                    "La exportación excede el máximo permitido "
                    f"({query_service.EXPORT_MAX_ROWS} filas). Refiná los filtros."
                ),
            )
            self._log_export_event(
                export_format=export_format,
                status="rejected",
                result_count=total_rows,
                extra={"reason": "max_rows_exceeded"},
            )
            return self.render_to_response(self.get_context_data())

        response = self._build_export_response(export_format)
        self._log_export_event(
            export_format=export_format,
            status="ok",
            result_count=total_rows,
        )
        return response

    def get_queryset(self):
        qs = query_service.get_base_queryset()
        self.filter_form = self.get_form()
        return self._apply_filters(qs, self.filter_form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entries = context.get("entries") or []
        for entry in entries:
            entry.resolved_changes = self.resolve_entry_changes(entry)
        self._decorate_entries_for_display(entries)
        context["filter_form"] = getattr(self, "filter_form", None)
        context["title"] = "Auditoría de cambios"
        context["tracked_models"] = TRACKED_MODELS
        params = self.request.GET.copy()
        params.pop("page", None)
        params.pop("export", None)
        context["querystring"] = params.urlencode()
        context["active_filters"] = self._build_active_filter_chips(
            context["filter_form"]
        )
        context["list_return_path"] = self._get_list_return_path()
        return context

    def _get_list_return_path(self):
        params = self.request.GET.copy()
        params.pop("export", None)
        querystring = params.urlencode()
        path = self.request.path
        return f"{path}?{querystring}" if querystring else path

    def _serialize_entry_for_export(self, entry):
        resolved_changes = self.resolve_entry_changes(entry)
        self._decorate_entry_for_display(entry)
        content_type = getattr(entry, "content_type", None)
        return {
            "event_id": getattr(entry, "pk", None),
            "timestamp": (
                entry.timestamp.isoformat() if getattr(entry, "timestamp", None) else ""
            ),
            "action": getattr(entry, "ui_action_label", ""),
            "action_code": getattr(entry, "action", None),
            "app_label": getattr(content_type, "app_label", ""),
            "model": getattr(content_type, "model", ""),
            "object_pk": str(getattr(entry, "object_pk", "")),
            "user": getattr(entry, "ui_actor_primary", ""),
            "user_detail": getattr(entry, "ui_actor_secondary", ""),
            "source": getattr(entry, "ui_source", ""),
            "batch_key": (
                getattr(entry, "ui_bulk_value", "")
                if getattr(entry, "ui_bulk_source", None) == "batch_key"
                else ""
            ),
            "remote_addr": str(getattr(entry, "remote_addr", "") or ""),
            "changes": getattr(entry, "changes", None),
            "changes_resolved": resolved_changes,
        }

    def _iter_export_rows(self):
        for entry in self.object_list.iterator():
            yield self._serialize_entry_for_export(entry)

    def _build_export_filename(self, export_format):
        suffix = timezone.now().strftime("%Y%m%d_%H%M%S")
        is_instance = bool(getattr(self, "kwargs", {}).get("object_pk"))
        scope = "instancia" if is_instance else "listado"
        return f"auditoria_{scope}_{suffix}.{export_format}"

    def _build_export_response(self, export_format):
        if export_format == "json":
            payload = {
                "count": self.object_list.count(),
                "results": list(self._iter_export_rows()),
            }
            response = JsonResponse(
                payload,
                json_dumps_params={"ensure_ascii": False, "default": str},
            )
            response["Content-Disposition"] = (
                f'attachment; filename="{self._build_export_filename("json")}"'
            )
            return response

        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = (
            f'attachment; filename="{self._build_export_filename("csv")}"'
        )
        writer = csv.writer(response)
        writer.writerow(
            [
                "event_id",
                "timestamp",
                "action",
                "app_label",
                "model",
                "object_pk",
                "user",
                "user_detail",
                "source",
                "batch_key",
                "remote_addr",
                "changes",
                "changes_resolved",
            ]
        )
        for row in self._iter_export_rows():
            writer.writerow(
                [
                    row["event_id"],
                    row["timestamp"],
                    row["action"],
                    row["app_label"],
                    row["model"],
                    row["object_pk"],
                    row["user"],
                    row["user_detail"],
                    row["source"],
                    row["batch_key"],
                    row["remote_addr"],
                    json.dumps(row["changes"], ensure_ascii=False, default=str),
                    json.dumps(row["changes_resolved"], ensure_ascii=False, default=str),
                ]
            )
        return response

    def _build_access_log_payload(self):
        request = getattr(self, "request", None)
        form = getattr(self, "filter_form", None)
        cleaned_data = form.cleaned_data if form and form.is_valid() else {}
        return {
            "route": request.path if request else "",
            "view_mode": (
                "instance" if getattr(self, "kwargs", {}).get("object_pk") else "global"
            ),
            "user_id": getattr(getattr(request, "user", None), "pk", None),
            "filters": {
                "model": cleaned_data.get("model"),
                "has_object_pk": bool(cleaned_data.get("object_pk")),
                "has_actor": bool(cleaned_data.get("actor")),
                "has_field_name": bool(cleaned_data.get("field_name")),
                "has_keyword": bool(cleaned_data.get("keyword")),
                "origin": cleaned_data.get("origin"),
                "has_batch_key": bool(cleaned_data.get("batch_key")),
                "action": cleaned_data.get("action"),
                "start_date": str(cleaned_data.get("start_date") or ""),
                "end_date": str(cleaned_data.get("end_date") or ""),
            },
        }

    def _log_export_event(self, *, export_format, status, result_count, extra=None):
        payload = self._build_access_log_payload()
        payload.update(
            {
                "event_type": "audittrail_export",
                "export_format": export_format,
                "status": status,
                "result_count": result_count,
            }
        )
        if extra:
            payload.update(extra)
        AUDITTRAIL_ACCESS_LOGGER.info("audittrail_export", extra={"data": payload})


class AuditNoStoreMixin:
    """Evita cacheo de pantallas de auditoría."""

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        response["Cache-Control"] = "no-store, private"
        return response


class AuditLogListView(AuditNoStoreMixin, BaseAuditLogListView):
    """Listado global de eventos de auditoría."""

    def get_tracked_choices(self):
        return tracked_model_choices(include_blank=True)


class AuditLogInstanceView(AuditNoStoreMixin, BaseAuditLogListView):
    """Historial de auditoría para una instancia puntual."""

    def get_tracked_choices(self):
        # No permitimos cambiar el modelo desde la UI en modo instancia.
        app_label = self.kwargs["app_label"]
        model_name = self.kwargs["model_name"]
        for app, model, label in TRACKED_MODELS:
            if app == app_label and model == model_name:
                return [(f"{app}.{model}", label)]
        return []

    def get_form(self):
        form = super().get_form()
        form.initial.update(
            {
                "model": f"{self.kwargs['app_label']}.{self.kwargs['model_name']}",
                "object_pk": self.kwargs["object_pk"],
            }
        )
        return form

    def get_queryset(self):
        qs = query_service.get_instance_queryset(
            app_label=self.kwargs["app_label"],
            model_name=self.kwargs["model_name"],
            object_pk=self.kwargs["object_pk"],
        )
        self.filter_form = self.get_form()
        return self._apply_filters(qs, self.filter_form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Historial de la instancia"
        context["instance_object_pk"] = self.kwargs["object_pk"]
        context["is_instance_view"] = True
        return context


class AuditLogDetailView(
    AuditNoStoreMixin,
    AuditLogResolveMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    DetailView,
):
    model = LogEntry
    template_name = "audittrail/log_detail.html"
    context_object_name = "entry"
    permission_required = "auditlog.view_logentry"

    def get_queryset(self):
        return query_service.get_base_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["changes"] = self.resolve_entry_changes(self.object)
        self.object.resolved_changes = context["changes"]
        self._decorate_entry_for_display(self.object)
        context["back_url"] = self._get_back_url()
        return context

    # Definimos explícitamente el método para evitar errores si el mixin no se carga por algún motivo.
    def resolve_entry_changes(self, entry):  # type: ignore[override]
        return AuditLogResolveMixin.resolve_entry_changes(self, entry)

    def _get_back_url(self):
        request = getattr(self, "request", None)
        if request is None:
            return reverse("audittrail:log_list")

        next_url = request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return next_url
        return reverse("audittrail:log_list")
