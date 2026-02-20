from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from comedores.models import Comedor
from core.soft_delete_preview import build_delete_preview
from core.soft_delete_views import SoftDeleteDeleteViewMixin, is_soft_deletable_instance
from rendicioncuentasmensual.models import RendicionCuentaMensual, DocumentacionAdjunta
from rendicioncuentasmensual.services import RendicionCuentaMensualService
from rendicioncuentasmensual.forms import (
    RendicionCuentaMensualForm,
    DocumentacionAdjuntaForm,
)


@login_required
@require_POST
def eliminar_archivo(request, archivo_id):
    archivo = get_object_or_404(DocumentacionAdjunta, id=archivo_id)
    preview_enabled = str(
        request.GET.get("preview") or request.POST.get("preview") or ""
    )
    if preview_enabled in {"1", "true", "True"} and is_soft_deletable_instance(archivo):
        return JsonResponse(
            {
                "success": True,
                "preview": build_delete_preview(archivo),
            }
        )

    if is_soft_deletable_instance(archivo):
        archivo.delete(user=request.user, cascade=True)
    else:
        archivo.delete()
    return JsonResponse(
        {"success": True, "message": "Archivo eliminado correctamente."}
    )


class RendicionCuentaMensualListView(LoginRequiredMixin, ListView):
    model = RendicionCuentaMensual
    template_name = "rendicioncuentasmensual_list.html"
    context_object_name = "rendiciones_cuentas_mensuales"
    paginate_by = 10

    def get_queryset(self):
        """Retorna rendiciones ordenadas para evitar warning de paginación"""
        return RendicionCuentaMensual.objects.order_by("-id")

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


class RendicionCuentaMensualDetailView(LoginRequiredMixin, DetailView):
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


class RendicionCuentaMensualCreateView(LoginRequiredMixin, CreateView):
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


class RendicionCuentaMensualUpdateView(LoginRequiredMixin, UpdateView):
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


class RendicionCuentaMensualDeleteView(
    SoftDeleteDeleteViewMixin,
    LoginRequiredMixin,
    DeleteView,
):
    model = RendicionCuentaMensual
    template_name = "rendicioncuentasmensual_confirm_delete.html"
    success_message = "Rendición dada de baja correctamente."

    def get_success_url(self):
        return reverse_lazy(
            "rendicioncuentasmensual_list",
            kwargs={"comedor_id": self.object.comedor.id},
        )
