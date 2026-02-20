from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.base import Model
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView

from comedores.forms.observacion_form import ObservacionForm
from comedores.models import Comedor, Observacion
from core.security import safe_redirect
from core.soft_delete_views import SoftDeleteDeleteViewMixin


class ObservacionCreateView(LoginRequiredMixin, CreateView):
    model = Observacion
    form_class = ObservacionForm
    template_name = "observacion/observacion_form.html"
    context_object_name = "observacion"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "comedor": Comedor.objects.values("id", "nombre").get(
                    pk=self.kwargs["comedor_pk"]
                )
            }
        )

        return context

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form.instance.comedor_id = Comedor.objects.get(pk=self.kwargs["comedor_pk"]).id
        usuario = self.request.user
        form.instance.observador = f"{usuario.first_name} {usuario.last_name}"
        form.instance.fecha_visita = timezone.now()
        self.object = form.save()
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        default_url = reverse("observacion_detalle", kwargs={"pk": int(self.object.id)})
        return safe_redirect(
            self.request,
            default=default_url,
            target=next_url,
        )


class ObservacionDetailView(LoginRequiredMixin, DetailView):
    model = Observacion
    template_name = "observacion/observacion_detail.html"
    context_object_name = "observacion"

    def get_object(self, queryset=None) -> Model:
        return (
            Observacion.objects.prefetch_related("comedor")
            .values(
                "id",
                "fecha_visita",
                "observacion",
                "comedor__id",
                "comedor__nombre",
                "observador",
            )
            .get(pk=self.kwargs["pk"])
        )


class ObservacionUpdateView(LoginRequiredMixin, UpdateView):
    model = Observacion
    form_class = ObservacionForm
    template_name = "observacion/observacion_form.html"
    context_object_name = "observacion"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        comedor = getattr(self.object, "comedor", None)
        if comedor:
            context.update({"comedor": {"id": comedor.id, "nombre": comedor.nombre}})

        return context

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        # Mantener el mismo comedor asociado sin depender de la URL
        form.instance.comedor = self.object.comedor
        usuario = self.request.user
        form.instance.observador = f"{usuario.first_name} {usuario.last_name}"
        form.instance.fecha_visita = timezone.now()
        self.object = form.save()

        return redirect(
            "observacion_detalle",
            pk=int(self.object.id),
        )


class ObservacionDeleteView(SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView):
    model = Observacion
    template_name = "observacion/observacion_confirm_delete.html"
    context_object_name = "observacion"
    success_message = "Observación dada de baja correctamente."

    def get_success_url(self):
        comedor = self.object.comedor

        return reverse_lazy("comedor_detalle", kwargs={"pk": comedor.id})
