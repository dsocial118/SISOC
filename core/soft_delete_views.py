"""View helpers for delete preview and soft-delete execution."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseRedirect, JsonResponse

from core.soft_delete_preview import build_delete_preview, build_restore_preview


class SuperAdminRequiredMixin(UserPassesTestMixin):
    """Restrict access to true Django superadmins."""

    raise_exception = True

    def test_func(self):
        return bool(self.request.user and self.request.user.is_superuser)


def is_soft_deletable_instance(instance) -> bool:
    return (
        instance is not None
        and hasattr(instance.__class__, "all_objects")
        and hasattr(instance, "restore")
        and hasattr(instance, "deleted_at")
    )


def build_preview(instance, *, operation: str, sample_limit: int = 5):
    if operation == "restore":
        return build_restore_preview(instance, sample_limit=sample_limit)
    return build_delete_preview(instance, sample_limit=sample_limit)


def delete_with_preview_response(request, instance, *, preview_param: str = "preview"):
    """Handle preview-or-delete for non-DeleteView endpoints (JSON)."""
    if not is_soft_deletable_instance(instance):
        return None

    if str(request.GET.get(preview_param) or request.POST.get(preview_param) or "") in {
        "1",
        "true",
        "True",
    }:
        preview = build_delete_preview(instance)
        return JsonResponse(
            {
                "success": True,
                "preview": preview,
            }
        )

    deleted_count, _ = instance.delete(user=request.user, cascade=True)
    return JsonResponse(
        {
            "success": True,
            "deleted_count": deleted_count,
        }
    )


def restore_with_preview_response(request, instance, *, preview_param: str = "preview"):
    """Handle preview-or-restore for restore endpoints (JSON)."""
    if not is_soft_deletable_instance(instance):
        return None

    if str(request.GET.get(preview_param) or request.POST.get(preview_param) or "") in {
        "1",
        "true",
        "True",
    }:
        preview = build_restore_preview(instance)
        return JsonResponse(
            {
                "success": True,
                "preview": preview,
            }
        )

    restored_count, _ = instance.restore(user=request.user, cascade=True)
    return JsonResponse(
        {
            "success": True,
            "restored_count": restored_count,
        }
    )


class SoftDeleteDeleteViewMixin:
    """
    Plug this into web DeleteView classes to:
    - render delete cascade preview on GET confirm page,
    - execute logical delete on POST with actor.
    """

    success_message = "Baja lógica realizada correctamente."

    def _soft_delete_instance(self, instance):
        instance.delete(user=self.request.user, cascade=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = context.get("object") or getattr(self, "object", None)
        if is_soft_deletable_instance(obj):
            context["cascade_preview"] = build_delete_preview(obj)
        context.setdefault("confirm_text", "Dar de baja")
        context.setdefault("cancel_text", "Cancelar")
        return context

    def form_valid(self, form):
        self.object = self.get_object()
        if is_soft_deletable_instance(self.object):
            self._soft_delete_instance(self.object)
            if self.success_message:
                messages.success(self.request, self.success_message)
            return HttpResponseRedirect(self.get_success_url())
        return super().form_valid(form)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if is_soft_deletable_instance(self.object):
            self._soft_delete_instance(self.object)
            if self.success_message:
                messages.success(request, self.success_message)
            return HttpResponseRedirect(self.get_success_url())
        return super().delete(request, *args, **kwargs)
