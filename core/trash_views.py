"""Global Trash UI (Papelera) for superadmins."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

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


class TrashListView(LoginRequiredMixin, SuperAdminRequiredMixin, View):
    """List soft-deleted records by model with basic search."""

    template_name = "core/trash_list.html"
    paginate_by = 25

    def get(self, request):
        model_choices = get_soft_delete_model_choices()
        if not model_choices:
            raise Http404("No hay modelos con borrado lógico registrados.")

        selected_key = request.GET.get("model") or model_choices[0][0]
        model = _soft_models_by_key().get(selected_key)
        if model is None:
            selected_key = model_choices[0][0]
            model = _soft_models_by_key()[selected_key]

        search_query = (request.GET.get("q") or "").strip()
        queryset = model.all_objects.filter(deleted_at__isnull=False).select_related(
            "deleted_by"
        )
        queryset = _search_queryset(model, queryset, search_query).order_by(
            "-deleted_at",
            "-pk",
        )

        paginator = Paginator(queryset, self.paginate_by)
        page_obj = paginator.get_page(request.GET.get("page") or 1)
        rows = [
            {
                "obj": item,
                "app_label": item._meta.app_label,
                "model_name": item._meta.model_name,
            }
            for item in page_obj.object_list
        ]

        context = {
            "model_choices": model_choices,
            "selected_model_key": selected_key,
            "selected_model_label": str(model._meta.verbose_name_plural).title(),
            "page_obj": page_obj,
            "rows": rows,
            "search_query": search_query,
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
            "back_url": f"{reverse('papelera_list')}?model={_model_key(model)}",
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
            return redirect(
                "papelera_preview_restore",
                app_label=app_label,
                model_name=model._meta.model_name,
                pk=pk,
            )

        restored_count, _ = instance.restore(user=request.user, cascade=True)
        messages.success(
            request,
            f"Restauración completada. Registros restaurados: {restored_count}.",
        )
        return redirect(f"{reverse('papelera_list')}?model={_model_key(model)}")
