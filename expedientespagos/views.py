from django.http import HttpResponseRedirect, Http404
from django.contrib import messages
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy, reverse
from expedientespagos.models import ExpedientePago
from expedientespagos.forms import ExpedientePagoForm
from expedientespagos.services import ExpedientesPagosService
from comedores.models import Comedor


class ExpedientesPagosListView(ListView):
    model = ExpedientePago
    template_name = "expedientespagos_list.html"
    context_object_name = "expedientespagos"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor_id = self.kwargs.get("pk")
        context["expedientes_pagos"] = (
            ExpedientesPagosService.obtener_expedientes_pagos(comedor_id)
        )
        context["comedorid"] = comedor_id

        return context


class ExpedientesPagosDetailView(DetailView):
    model = ExpedientePago
    template_name = "expedientespagos_detail.html"
    context_object_name = "expediente_pago"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["expediente"] = ExpedientesPagosService.obtener_expediente_pago(
            self.kwargs.get("pk")
        )
        return context


class ExpedientesPagosCreateView(CreateView):
    model = ExpedientePago
    template_name = "expedientespagos_form.html"
    fields = "__all__"

    def get_success_url(self):
        return reverse_lazy(
            "expedientespagos_list", kwargs={"pk": self.kwargs.get("pk")}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor_id = self.kwargs.get("pk")
        context["comedorid"] = comedor_id
        context["form"] = ExpedientePagoForm()
        return context

    def post(self, request, *args, **kwargs):
        comedor_id = self.kwargs.get("pk")
        form = ExpedientePagoForm(request.POST)
        comedor = Comedor.objects.get(pk=comedor_id)
        if form.is_valid():
            expediente_pago = ExpedientesPagosService.crear_expediente_pago(
                comedor, form.cleaned_data
            )
            self.object = expediente_pago
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class ExpedientesPagosUpdateView(UpdateView):
    model = ExpedientePago
    template_name = "expedientespagos_form.html"
    form_class = ExpedientePagoForm

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
        return context

    def post(self, request, *args, **kwargs):
        expediente_pago = self.get_object()
        form = ExpedientePagoForm(request.POST, instance=expediente_pago)
        if form.is_valid():
            expediente_pago = ExpedientesPagosService.actualizar_expediente_pago(
                expediente_pago, form.cleaned_data
            )
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class ExpedientesPagosDeleteView(DeleteView):
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
