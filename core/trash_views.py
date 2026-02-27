"""Global Trash UI (Papelera) for superadmins."""

from __future__ import annotations

from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from core.forms import TrashFilterForm
from core.security import safe_redirect
from core.soft_delete_preview import build_restore_preview
from core.soft_delete_registry import (
    get_soft_delete_model_choices,
    iter_soft_delete_models,
)
from core.soft_delete_views import SuperAdminRequiredMixin


def _model_key(model):
    return f"{model._meta.app_label}.{model.__name__}"


def _soft_models_by_key():
    return {_model_key(model): model for model in iter_soft_delete_models()}


def _resolve_model_or_404(app_label: str, model_name: str):
    normalized = (model_name or "").lower()
    for model in iter_soft_delete_models():
        if model._meta.app_label != app_label:
            continue
        if model.__name__.lower() == normalized or model._meta.model_name == normalized:
            return model
    raise Http404("Modelo no soportado por la papelera.")


def _search_queryset(model, queryset, query: str):
    query = (query or "").strip()
    if not query:
        return queryset

    filters = Q()
    if query.isdigit():
        filters |= Q(pk=int(query))

    for field in model._meta.get_fields():  # noqa: SLF001
        if not getattr(field, "concrete", False):
            continue
        if field.many_to_many:
            continue
        if field.is_relation:
            continue
        internal_type = field.get_internal_type()
        if internal_type in {"CharField", "TextField", "EmailField"}:
            filters |= Q(**{f"{field.name}__icontains": query})

    return queryset.filter(filters) if filters else queryset.none()


def _apply_deleted_by_filter(queryset, deleted_by_query: str):
    deleted_by_query = (deleted_by_query or "").strip()
    if not deleted_by_query:
        return queryset
    return queryset.filter(
        Q(deleted_by__username__icontains=deleted_by_query)
        | Q(deleted_by__first_name__icontains=deleted_by_query)
        | Q(deleted_by__last_name__icontains=deleted_by_query)
    )


def _apply_deleted_date_range_filter(queryset, deleted_from=None, deleted_to=None):
    if deleted_from:
        queryset = queryset.filter(deleted_at__date__gte=deleted_from)
    if deleted_to:
        queryset = queryset.filter(deleted_at__date__lte=deleted_to)
    return queryset


def _get_safe_next_url(request, target=None):
    target = target or request.GET.get("next") or request.POST.get("next")
    if not target:
        return None
    if url_has_allowed_host_and_scheme(
        target,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return target
    return None


def _append_next(base_url: str, next_url: str | None):
    if not next_url:
        return base_url
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{urlencode({'next': next_url})}"


def _build_active_filters(cleaned_data, selected_model_label, default_model_key):
    active_filters = []
    selected_model_key = cleaned_data.get("model")
    if selected_model_key and selected_model_key != default_model_key:
        active_filters.append({"label": "Modelo", "value": selected_model_label})
    if cleaned_data.get("q"):
        active_filters.append({"label": "Búsqueda", "value": cleaned_data["q"]})
    if cleaned_data.get("deleted_by"):
        active_filters.append(
            {"label": "Eliminado por", "value": cleaned_data["deleted_by"]}
        )
    if cleaned_data.get("deleted_from"):
        active_filters.append(
            {
                "label": "Desde",
                "value": cleaned_data["deleted_from"].strftime("%d/%m/%Y"),
            }
        )
    if cleaned_data.get("deleted_to"):
        active_filters.append(
            {
                "label": "Hasta",
                "value": cleaned_data["deleted_to"].strftime("%d/%m/%Y"),
            }
        )
    return active_filters


def _instance_details(instance):
    details = []
    for field in instance._meta.concrete_fields:
        value = getattr(instance, field.attname, None)
        label = getattr(field, "verbose_name", field.name).title()
        details.append({"label": label, "value": value})
    return details


def _build_filter_form_and_data(request, model_choices, models_by_key):
    form_data = request.GET.copy() if request.GET else None
    if form_data is not None:
        selected_key = form_data.get("model", "")
        if selected_key not in models_by_key:
            selected_key = ""
        form_data["model"] = selected_key
        filter_form = TrashFilterForm(form_data, model_choices=model_choices)
    else:
        selected_key = ""
        filter_form = TrashFilterForm(
            model_choices=model_choices,
            initial={"model": selected_key},
        )

    form_is_valid = filter_form.is_valid() if filter_form.is_bound else True
    filter_data = (
        filter_form.cleaned_data if filter_form.is_bound and form_is_valid else {}
    )
    return filter_form, selected_key, filter_data


def _get_models_to_scan(selected_key, models_by_key, order_keys):
    if selected_key:
        return [models_by_key[selected_key]]
    return [models_by_key[key] for key in order_keys]


def _build_deleted_rows(models_to_scan, filter_data):
    rows = []
    for model in models_to_scan:
        queryset = model.all_objects.filter(deleted_at__isnull=False).select_related(
            "deleted_by"
        )
        if filter_data:
            queryset = _search_queryset(model, queryset, filter_data.get("q", ""))
            queryset = _apply_deleted_by_filter(queryset, filter_data.get("deleted_by"))
            queryset = _apply_deleted_date_range_filter(
                queryset,
                filter_data.get("deleted_from"),
                filter_data.get("deleted_to"),
            )

        model_label = str(model._meta.verbose_name).title()
        for item in queryset.order_by("-deleted_at", "-pk"):
            rows.append(
                {
                    "obj": item,
                    "app_label": item._meta.app_label,
                    "model_name": item._meta.model_name,
                    "model_label": model_label,
                }
            )

    rows.sort(
        key=lambda row: (row["obj"].deleted_at, row["obj"].pk),
        reverse=True,
    )
    return rows


def _build_pagination_querystring(request):
    pagination_query_params = request.GET.copy()
    pagination_query_params.pop("page", None)
    return pagination_query_params.urlencode()


class TrashListView(LoginRequiredMixin, SuperAdminRequiredMixin, View):
    """List soft-deleted records by model with basic search."""

    template_name = "core/trash_list.html"
    paginate_by = 25

    def get(self, request):
        model_choices = get_soft_delete_model_choices()
        if not model_choices:
            raise Http404("No hay modelos con borrado lógico registrados.")

        models_by_key = _soft_models_by_key()
        order_keys = [key for key, _ in model_choices]
        filter_form, selected_key, filter_data = _build_filter_form_and_data(
            request=request,
            model_choices=model_choices,
            models_by_key=models_by_key,
        )
        selected_key = filter_data.get("model", selected_key or "")
        selected_model_label = (
            str(models_by_key[selected_key]._meta.verbose_name_plural).title()
            if selected_key
            else "Todos los modelos"
        )

        rows = _build_deleted_rows(
            models_to_scan=_get_models_to_scan(
                selected_key=selected_key,
                models_by_key=models_by_key,
                order_keys=order_keys,
            ),
            filter_data=filter_data,
        )
        page_obj = Paginator(rows, self.paginate_by).get_page(
            request.GET.get("page") or 1
        )

        active_filters = (
            _build_active_filters(
                filter_data,
                selected_model_label=selected_model_label,
                default_model_key="",
            )
            if filter_data
            else []
        )

        context = {
            "filter_form": filter_form,
            "model_choices": model_choices,
            "selected_model_key": selected_key,
            "selected_model_label": selected_model_label,
            "page_obj": page_obj,
            "rows": page_obj.object_list,
            "search_query": filter_data.get("q", ""),
            "active_filters": active_filters,
            "pagination_querystring": _build_pagination_querystring(request),
            "current_full_path": request.get_full_path(),
            "show_all_models": not selected_key,
        }
        return render(request, self.template_name, context)


class TrashRestorePreviewView(LoginRequiredMixin, SuperAdminRequiredMixin, View):
    """Preview restore impact before confirming."""

    template_name = "core/trash_restore_confirm.html"

    def get(self, request, app_label: str, model_name: str, pk: int):
        model = _resolve_model_or_404(app_label, model_name)
        instance = model.all_objects.filter(pk=pk, deleted_at__isnull=False).first()
        if instance is None:
            raise Http404("El registro no está en papelera.")

        preview = build_restore_preview(instance)
        default_back_url = f"{reverse('papelera_list')}?model={_model_key(model)}"
        next_url = _get_safe_next_url(request)
        context = {
            "instance": instance,
            "model": model,
            "preview": preview,
            "restore_url": reverse(
                "papelera_restore",
                kwargs={
                    "app_label": app_label,
                    "model_name": model._meta.model_name,
                    "pk": pk,
                },
            ),
            "back_url": next_url or default_back_url,
            "next_url": next_url,
            "model_identifier": f"{model._meta.app_label}.{model._meta.model_name}",
            "instance_details": _instance_details(instance),
        }
        return render(request, self.template_name, context)


class TrashRestoreView(LoginRequiredMixin, SuperAdminRequiredMixin, View):
    """Execute restore in cascade from Trash UI."""

    def post(self, request, app_label: str, model_name: str, pk: int):
        if not request.user.is_superuser:
            return HttpResponseForbidden()

        model = _resolve_model_or_404(app_label, model_name)
        instance = model.all_objects.filter(pk=pk, deleted_at__isnull=False).first()
        if instance is None:
            raise Http404("El registro no está en papelera.")

        if str(request.POST.get("confirmed") or "0") != "1":
            preview_url = reverse(
                "papelera_preview_restore",
                kwargs={
                    "app_label": app_label,
                    "model_name": model._meta.model_name,
                    "pk": pk,
                },
            )
            return redirect(_append_next(preview_url, _get_safe_next_url(request)))

        restored_count, _ = instance.restore(user=request.user, cascade=True)
        messages.success(
            request,
            f"Restauración completada. Registros restaurados: {restored_count}.",
        )
        return safe_redirect(
            request,
            f"{reverse('papelera_list')}?model={_model_key(model)}",
            target=request.POST.get("next"),
        )
