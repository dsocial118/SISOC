from datetime import timedelta
import re

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from django.views.generic import DetailView, ListView
from django.db.models import Q

from auditlog.models import LogEntry
from audittrail.constants import TRACKED_MODELS
from audittrail.forms import AuditLogFilterForm


class AuditLogResolveMixin:
    """
    Mixin para normalizar y formatear diffs de auditlog.
    """

    def resolve_entry_changes(self, entry):
        """
        Normaliza los valores old/new y resuelve FKs a su __str__ para que la UI muestre
        algo legible. Evita consultas innecesarias para valores nulos o vacíos.
        """
        changes = getattr(entry, "changes_display_dict", None) or {}
        model_cls = entry.content_type.model_class()
        resolved = {}

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
                "old": self._format_value(old_val, field),
                "new": self._format_value(new_val, field),
            }

        return resolved

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
    def _format_value(value, field):
        if value in (None, "", [], ()):
            return mark_safe("<em>No cargado</em>")
        if isinstance(value, str) and value.strip().lower() == "none":
            return mark_safe("<em>No cargado</em>")
        if isinstance(value, bool):
            return "Sí" if value else "No"
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned.lower().endswith(".none"):
                return mark_safe("<em>No cargado</em>")
            # Patrones tipo "app.Model.pk" -> "Model #pk"
            dotted = cleaned.split(".")
            if (
                len(dotted) >= 3
                and re.fullmatch(r"[a-z_]+", dotted[0])
                and dotted[1]
            ):
                model_label = dotted[1].replace("_", " ").title()
                pk_part = dotted[-1]
                if pk_part.isdigit():
                    return f"{model_label} #{pk_part}"
                return f"{model_label} ({pk_part})"
        if field and isinstance(field, (models.ForeignKey, models.OneToOneField)):
            try:
                obj = field.remote_field.model.objects.filter(pk=value).first()
                if obj:
                    label = str(obj)
                    if "object (" in label and ")" in label:
                        model_name = field.remote_field.model._meta.verbose_name.title()
                        return f"{model_name} #{value}"
                    return label
            except Exception:  # noqa: BLE001
                return value
        return value


class BaseAuditLogListView(AuditLogResolveMixin, LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = LogEntry
    template_name = "audittrail/log_list.html"
    context_object_name = "entries"
    paginate_by = 25
    permission_required = "auditlog.view_logentry"

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

        data = form.cleaned_data

        model_value = data.get("model")
        if model_value:
            qs = qs.filter(
                Q(content_type__app_label__icontains=model_value)
                | Q(content_type__model__icontains=model_value)
            )

        object_pk = data.get("object_pk")
        if object_pk:
            qs = qs.filter(object_pk=str(object_pk))

        actor = data.get("actor")
        if actor:
            qs = qs.filter(
                Q(actor__username__icontains=actor)
                | Q(actor__email__icontains=actor)
                | Q(actor__first_name__icontains=actor)
                | Q(actor__last_name__icontains=actor)
            )

        action = data.get("action")
        if action != "":
            qs = qs.filter(action=action)

        start_date = data.get("start_date")
        if start_date:
            qs = qs.filter(timestamp__date__gte=start_date)

        end_date = data.get("end_date")
        if end_date:
            # incluir el día completo
            qs = qs.filter(timestamp__lt=end_date + timedelta(days=1))

        return qs

    def get_form(self):
        return AuditLogFilterForm(self.request.GET or None)

    def get_queryset(self):
        qs = (
            LogEntry.objects.select_related("actor", "content_type")
            .all()
            .order_by("-timestamp", "-id")
        )
        self.filter_form = self.get_form()
        return self._apply_filters(qs, self.filter_form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entries = context.get("entries") or []
        for entry in entries:
            entry.resolved_changes = self.resolve_entry_changes(entry)
        context["filter_form"] = getattr(self, "filter_form", None)
        context["title"] = "Auditoría de cambios"
        context["tracked_models"] = TRACKED_MODELS
        params = self.request.GET.copy()
        params.pop("page", None)
        context["querystring"] = params.urlencode()
        return context

class AuditLogListView(BaseAuditLogListView):
    """Listado global de eventos de auditoría."""

    def get_tracked_choices(self):
        return tracked_model_choices(include_blank=True)


class AuditLogInstanceView(BaseAuditLogListView):
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
        ct = get_object_or_404(
            ContentType, app_label=self.kwargs["app_label"], model=self.kwargs["model_name"]
        )
        qs = (
            LogEntry.objects.select_related("actor", "content_type")
            .filter(content_type=ct, object_pk=str(self.kwargs["object_pk"]))
            .order_by("-timestamp", "-id")
        )
        self.filter_form = self.get_form()
        return self._apply_filters(qs, self.filter_form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Historial de la instancia"
        context["instance_object_pk"] = self.kwargs["object_pk"]
        context["is_instance_view"] = True
        return context


class AuditLogDetailView(AuditLogResolveMixin, LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = LogEntry
    template_name = "audittrail/log_detail.html"
    context_object_name = "entry"
    permission_required = "auditlog.view_logentry"

    def get_queryset(self):
        return LogEntry.objects.select_related("actor", "content_type").all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["changes"] = self.resolve_entry_changes(self.object)
        return context

    # Definimos explícitamente el método para evitar errores si el mixin no se carga por algún motivo.
    def resolve_entry_changes(self, entry):  # type: ignore[override]
        return AuditLogResolveMixin.resolve_entry_changes(self, entry)
