from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy
from expedientespagos.models import ExpedientePago
from expedientespagos.forms import ExpedientePagoForm
from expedientespagos.services import ExpedientesPagosService



class ExpedientesPagosListView(ListView):
    model = ExpedientePago
    template_name = "expedientespagos_list.html"
    context_object_name = "expedientespagos"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor_id = self.kwargs.get("pk")
        context["expedientes_pagos"] = ExpedientesPagosService.obtener_expedientes_pagos(comedor_id)
        context["comedorid"] = comedor_id

        return context

class ExpedientesPagosDetailView(DetailView):
    model = ExpedientePago
    template_name = "expedientespagos_detail.html"
    context_object_name = "expediente_pago"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["expediente"] = ExpedientesPagosService.obtener_expediente_pago(self.kwargs.get("pk"))
        return context


class ExpedientesPagosCreateView(CreateView):
    model = ExpedientePago
    template_name = "expedientespagos_form.html"
    fields = "__all__"
    success_url = reverse_lazy("expedientespagos:expedientespagos_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor_id = self.kwargs.get("pk")
        context["comedorid"] = comedor_id
        context["form"] = ExpedientePagoForm()
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class ExpedientesPagosUpdateView(UpdateView):
    model = ExpedientePago
    template_name = "expedientespagos_form.html"
    fields = "__all__"
    success_url = reverse_lazy("expedientespagos:expedientespagos_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        acompanamiento_id = self.kwargs.get("pk")
        context["acompanamiento"] = acompanamiento_id
        context["form"] = ExpedientePagoForm()
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)



class ExpedientesPagosDeleteView(DeleteView):
    model = ExpedientePago
    template_name = "expedientespagos_confirm_delete.html"
    success_url = reverse_lazy("expedientespagos:expedientespagos_list")

    def get_queryset(self):
        return ExpedientePago.objects.all()

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
