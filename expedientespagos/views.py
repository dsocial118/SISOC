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
    
    def get_success_url(self):
        return reverse_lazy("expedientespagos_list", kwargs={"pk": self.kwargs.get("pk")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor_id = self.kwargs.get("pk")
        context["comedorid"] = comedor_id
        context["form"] = ExpedientePagoForm()
        return context
       
    def post(self, request, *args, **kwargs):
        comedor_id = self.kwargs.get("pk")
        form = ExpedientePagoForm(request.POST)
        if form.is_valid():
            expediente_pago = ExpedientesPagosService.crear_expediente_pago(
                comedor_id, form.cleaned_data
            )
            self.object = expediente_pago
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

class ExpedientesPagosUpdateView(UpdateView):
    model = ExpedientePago
    template_name = "expedientespagos_form.html"
    fields = "__all__"
    
    def get_success_url(self):
        return reverse_lazy("expedientespagos_list", kwargs={"pk": self.object.comedor.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        expediente = self.get_object()
        context["comedorid"] = expediente.comedor.id
        context["form"] = self.get_form()
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
    success_url = reverse_lazy("expedientespagos_list")

    def get_queryset(self):
        return ExpedientePago.objects.all()
