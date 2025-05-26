from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from expedientespagos.models.expedientespagos import ExpedientePago

# Create your views here.


class ExpedientesPagosListView(LoginRequiredMixin, ListView):
    model = ExpedientePago
    template_name = "expedientespagos/expedientespagos_list.html"
    context_object_name = "expedientespagos"
    paginate_by = 10

    def get_queryset(self):
        return ExpedientePago.objects.all()


class ExpedientesPagosDetailView(LoginRequiredMixin, DetailView):
    model = ExpedientePago
    template_name = "expedientespagos/expedientespagos_detail.html"
    context_object_name = "expediente_pago"

    def get_queryset(self):
        return ExpedientePago.objects.all()


class ExpedientesPagosCreateView(LoginRequiredMixin, CreateView):
    model = ExpedientePago
    template_name = "expedientespagos/expedientespagos_form.html"
    fields = "__all__"
    success_url = reverse_lazy("expedientespagos:expedientespagos_list")

    def get_queryset(self):
        return ExpedientePago.objects.all()

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class ExpedientesPagosUpdateView(LoginRequiredMixin, UpdateView):
    model = ExpedientePago
    template_name = "expedientespagos/expedientespagos_form.html"
    fields = "__all__"
    success_url = reverse_lazy("expedientespagos:expedientespagos_list")

    def get_queryset(self):
        return ExpedientePago.objects.all()

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class ExpedientesPagosDeleteView(LoginRequiredMixin, DeleteView):
    model = ExpedientePago
    template_name = "expedientespagos/expedientespagos_confirm_delete.html"
    success_url = reverse_lazy("expedientespagos:expedientespagos_list")

    def get_queryset(self):
        return ExpedientePago.objects.all()

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
