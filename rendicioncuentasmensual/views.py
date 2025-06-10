from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from comedores.models.comedor import Comedor
from .models import RendicionCuentaMensual, DocumentacionAdjunta
from .services import RendicionCuentaMensualService
from .forms import RendicionCuentaMensualForm, DocumentacionAdjuntaForm


@csrf_exempt
def eliminar_archivo(request, archivo_id):
    if request.method == "POST":
        archivo = get_object_or_404(DocumentacionAdjunta, id=archivo_id)
        archivo.delete()
        return JsonResponse(
            {"success": True, "message": "Archivo eliminado correctamente."}
        )
    return JsonResponse(
        {"success": False, "message": "Método no permitido."}, status=405
    )


class RendicionCuentaMensualListView(ListView):
    model = RendicionCuentaMensual
    template_name = "rendicioncuentasmensual_list.html"
    context_object_name = "rendiciones_cuentas_mensuales"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor_id = self.kwargs.get("comedor_id")
        context["rendiciones_cuentas_mensuales"] = (
            RendicionCuentaMensualService.obtener_rendiciones_cuentas_mensuales(
                Comedor.objects.get(id=comedor_id)
            )
        )
        context["comedorid"] = comedor_id
        return context


class RendicionCuentaMensualDetailView(DetailView):
    model = RendicionCuentaMensual
    template_name = "rendicioncuentasmensual_detail.html"
    context_object_name = "rendicion_cuenta_mensual"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["rendicion"] = (
            RendicionCuentaMensualService.obtener_rendicion_cuenta_mensual(
                self.kwargs.get("pk")
            )
        )
        return context


class RendicionCuentaMensualCreateView(CreateView):
    model = RendicionCuentaMensual
    template_name = "rendicioncuentasmensual_form.html"
    form_class = RendicionCuentaMensualForm

    def form_valid(self, form):
        comedor_id = self.kwargs.get("comedor_id")
        comedor = Comedor.objects.get(id=comedor_id)

        rendicion = form.save(commit=False)
        rendicion.comedor = comedor
        rendicion.save()

        archivos = self.request.FILES.getlist("archivo")
        for archivo_enviado in archivos:
            doc_adjunta = DocumentacionAdjunta.objects.create(
                nombre=archivo_enviado.name,
                archivo=archivo_enviado,
            )
            rendicion.arvhios_adjuntos.add(doc_adjunta)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "rendicioncuentasmensual_list",
            kwargs={"comedor_id": self.kwargs.get("comedor_id")},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor_id = self.kwargs.get("comedor_id")
        context["comedorid"] = comedor_id
        context["form"] = RendicionCuentaMensualForm()
        context["documentacion_adjunta_form"] = DocumentacionAdjuntaForm()
        return context


class RendicionCuentaMensualUpdateView(UpdateView):
    model = RendicionCuentaMensual
    template_name = "rendicioncuentasmensual_form.html"
    form_class = RendicionCuentaMensualForm

    def form_valid(self, form):
        rendicion = self.get_object()
        form.instance.comedor = rendicion.comedor
        form.instance.ultima_modificacion = rendicion.ultima_modificacion
        form.instance.fecha_creacion = rendicion.fecha_creacion
        rendicion = form.save()

        archivos = self.request.FILES.getlist("archivo")
        for archivo in archivos:
            doc_adjunta = DocumentacionAdjunta.objects.create(
                nombre=archivo.name,
                archivo=archivo,
            )
            rendicion.arvhios_adjuntos.add(doc_adjunta)

        return super().form_valid(form)

    def get_success_url(self):
        comedor_id = self.object.comedor.id
        return reverse_lazy(
            "rendicioncuentasmensual_list", kwargs={"comedor_id": comedor_id}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor_id = self.object.comedor.id
        context["comedorid"] = comedor_id
        context["form"] = RendicionCuentaMensualForm(instance=self.object)
        context["documentacion_adjunta_form"] = DocumentacionAdjuntaForm()
        context["archivos_adjuntos"] = self.object.arvhios_adjuntos.all()
        return context


class RendicionCuentaMensualDeleteView(DeleteView):
    model = RendicionCuentaMensual
    template_name = "rendicioncuentasmensual_confirm_delete.html"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.arvhios_adjuntos.all().delete()
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            "rendicioncuentasmensual_list",
            kwargs={"comedor_id": self.object.comedor.id},
        )
