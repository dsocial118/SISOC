from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from .models import RendicionCuentaMensual, DocumentacionAdjunta
from .services import RendicionCuentaMensualService
from comedores.models.comedor import Comedor
from django.urls import reverse_lazy, reverse
from .forms import RendicionCuentaMensualForm, DocumentacionAdjuntaForm


def crear_rendicion_cuenta_mensual(request):
    if request.method == "POST":
        form = RendicionCuentaMensualForm(request.POST, request.FILES)
        if form.is_valid():
            rendicion = form.save()
            return redirect("rendicion_cuenta_listar")
    else:
        form = RendicionCuentaMensualForm()
    return render(request, "rendicioncuentasmensual/crear.html", {"form": form})

class RendicionCuentaMensualListView(ListView):
    model = RendicionCuentaMensual
    template_name = "rendicioncuentasmensual_list.html"
    context_object_name = "rendiciones_cuentas_mensuales"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor_id = self.kwargs.get("comedor_id")
        context["rendiciones_cuentas_mensuales"] = RendicionCuentaMensualService.obtener_rendiciones_cuentas_mensuales(Comedor.objects.get(id=comedor_id))
        context["comedorid"] = comedor_id
        return context
    
class RendicionCuentaMensualDetailView(DetailView):
    model = RendicionCuentaMensual
    template_name = "rendicioncuentasmensual_detail.html"
    context_object_name = "rendicion_cuenta_mensual"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["rendicion"] = RendicionCuentaMensualService.obtener_rendicion_cuenta_mensual(self.kwargs.get("id_enviado"))
        return context
    
class RendicionCuentaMensualCreateView(CreateView):
    model = RendicionCuentaMensual
    template_name = "rendicioncuentasmensual_form.html"
    fields = "__all__"

    def form_valid(self, form):
        comedor_id = self.kwargs.get("comedor_id")
        comedor = Comedor.objects.get(id=comedor_id)
        rendicion = form.save(commit=False)
        rendicion.comedor = comedor
        rendicion.save()
        archivos = self.request.FILES.getlist("arvhios_adjuntos")
        for archivo in archivos:
            doc_adjunta = DocumentacionAdjunta.objects.create(
                nombre=archivo.name,
                archivo=archivo,
            )
            rendicion.arvhios_adjuntos.add(doc_adjunta)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("rendicioncuentasmensual_list", kwargs={"comedor_id": self.kwargs.get("comedor_id")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor_id = self.kwargs.get("comedor_id")
        context["comedorid"] = comedor_id
        context["form"] = RendicionCuentaMensualForm()
        return context

class RendicionCuentaMensualUpdateView(UpdateView):
    model = RendicionCuentaMensual
    template_name = "rendicioncuentasmensual_form.html"
    fields = "__all__"

    def form_valid(self, form):
        comedor_id = self.kwargs.get("comedor_id")
        comedor = Comedor.objects.get(id=comedor_id)
        rendicion = form.save(commit=False)
        rendicion.comedor = comedor
        rendicion.save()
        archivos = self.request.FILES.getlist("arvhios_adjuntos")
        for archivo in archivos:
            doc_adjunta = DocumentacionAdjunta.objects.create(
                nombre=archivo.name,
                archivo=archivo,
            )
            rendicion.arvhios_adjuntos.add(doc_adjunta)

        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy("rendicioncuentasmensual_list", kwargs={"comedor_id": self.kwargs.get("comedor_id")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor_id = self.kwargs.get("comedor_id")
        context["comedorid"] = comedor_id
        context["form"] = RendicionCuentaMensualForm(instance=self.object)
        return context

class RendicionCuentaMensualDeleteView(DeleteView):
    model = RendicionCuentaMensual
    template_name = "rendicioncuentasmensual_confirm_delete.html"
    context_object_name = "rendicion_cuenta_mensual"

    def get_success_url(self):
        return reverse_lazy("rendicioncuentasmensual_list", kwargs={"comedor_id": self.kwargs.get("comedor_id")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor_id = self.kwargs.get("comedor_id")
        context["comedorid"] = comedor_id
        return context
