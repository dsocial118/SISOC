from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, Http404
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from core.services.column_preferences import build_columns_context_from_fields
from expedientespagos.models import ExpedientePago
from expedientespagos.forms import ExpedientePagoForm
from expedientespagos.services import ExpedientesPagosService
from comedores.models import Comedor


@method_decorator(ensure_csrf_cookie, name="dispatch")
class ExpedientesPagosListView(LoginRequiredMixin, ListView):
    model = ExpedientePago
    template_name = "expedientespagos_list.html"
    context_object_name = "expedientespagos"
    paginate_by = 10

    def get_queryset(self):
        """Retorna expedientes ordenados para evitar warning de paginación"""
        return ExpedientePago.objects.order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor_id = self.kwargs.get("pk")
        context["expedientes_pagos"] = (
            ExpedientesPagosService.obtener_expedientes_pagos(comedor_id)
        )
        context["comedorid"] = comedor_id

        headers = [
            {"title": "Mes de Pago"},
            {"title": "Año"},
            {"title": "Expediente de Pago"},
            {"title": "Expediente del Convenio"},
            {"title": "Total"},
            {"title": "Fecha de creación"},
        ]

        fields = [
            {"name": "mes_pago"},
            {"name": "ano"},
            {"name": "expediente_pago"},
            {"name": "expediente_convenio"},
            {"name": "total"},
            {"name": "fecha_creacion"},
        ]

        context.update(
            build_columns_context_from_fields(
                self.request,
                "expedientes_pagos_list",
                headers,
                fields,
            )
        )

        context["table_actions"] = [
            {"label": "Ver", "url_name": "expedientespagos_detail", "type": "info"}
        ]

        return context


class ExpedientesPagosDetailView(LoginRequiredMixin, DetailView):
    model = ExpedientePago
    template_name = "expedientespagos_detail.html"
    context_object_name = "expediente_pago"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["expediente"] = ExpedientesPagosService.obtener_expediente_pago(
            self.kwargs.get("pk")
        )
        return context


class ExpedientesPagosCreateView(LoginRequiredMixin, CreateView):
    model = ExpedientePago
    template_name = "expedientespagos_form.html"
    form_class = ExpedientePagoForm

    def _get_role_flags(self):
        es_area_legales = (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name="Area Legales").exists()
        )
        es_tecnico_comedor = (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name="Tecnico Comedor").exists()
        )
        return es_area_legales, es_tecnico_comedor

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        es_area_legales, es_tecnico_comedor = self._get_role_flags()
        kwargs.update(
            {
                "es_area_legales": es_area_legales,
                "es_tecnico_comedor": es_tecnico_comedor,
            }
        )
        return kwargs

    def get_success_url(self):
        return reverse_lazy(
            "expedientespagos_list", kwargs={"pk": self.kwargs.get("pk")}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor_id = self.kwargs.get("pk")
        context["comedorid"] = comedor_id
        context["form"] = ExpedientePagoForm()
        es_area_legales, es_tecnico_comedor = self._get_role_flags()
        context["es_area_legales"] = es_area_legales
        context["es_tecnico_comedor"] = es_tecnico_comedor
        # URL de cancelación para el componente form_buttons
        context["expedientes_list_url"] = reverse(
            "expedientespagos_list", kwargs={"pk": comedor_id}
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        comedor_id = self.kwargs.get("pk")
        form = self.get_form()
        comedor = Comedor.objects.get(pk=comedor_id)
        if form.is_valid():
            # Crear el objeto y asignarlo a self.object
            self.object = ExpedientesPagosService.crear_expediente_pago(
                comedor, form.cleaned_data
            )
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class ExpedientesPagosUpdateView(LoginRequiredMixin, UpdateView):
    model = ExpedientePago
    template_name = "expedientespagos_form.html"
    form_class = ExpedientePagoForm

    def _get_role_flags(self):
        es_area_legales = (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name="Area Legales").exists()
        )
        es_tecnico_comedor = (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name="Tecnico Comedor").exists()
        )
        return es_area_legales, es_tecnico_comedor

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        es_area_legales, es_tecnico_comedor = self._get_role_flags()
        kwargs.update(
            {
                "es_area_legales": es_area_legales,
                "es_tecnico_comedor": es_tecnico_comedor,
            }
        )
        return kwargs

    def get_success_url(self):
        return reverse_lazy(
            "expedientespagos_list", kwargs={"pk": self.object.comedor.id}
        )

    def form_valid(self, form):
        # Mantén el mismo comedor que tenía originalmente
        form.instance.comedor = self.get_object().comedor
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        expediente = self.get_object()
        context["comedorid"] = expediente.comedor.id
        es_area_legales, es_tecnico_comedor = self._get_role_flags()
        context["es_area_legales"] = es_area_legales
        context["es_tecnico_comedor"] = es_tecnico_comedor
        # URL de cancelación para el componente form_buttons
        context["expedientes_list_url"] = reverse(
            "expedientespagos_list", kwargs={"pk": expediente.comedor.id}
        )
        return context

    def post(self, request, *args, **kwargs):
        # Configurar self.object antes de llamar a form_valid
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class ExpedientesPagosDeleteView(LoginRequiredMixin, DeleteView):
    model = ExpedientePago
    template_name = "expedientespagos_confirm_delete.html"

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except ExpedientePago.DoesNotExist as exc:
            raise Http404("El expediente de pago no existe.") from exc

    def get_success_url(self):
        return reverse("lista_comedores_acompanamiento")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(request, "Expediente eliminado correctamente.")
        return HttpResponseRedirect(self.get_success_url())
