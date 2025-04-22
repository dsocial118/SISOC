import os
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, ListView, UpdateView
from admisiones.forms.admisiones_forms import AdmisionForm
from admisiones.models.admisiones import Admision, ArchivoAdmision
from admisiones.services.admisiones_service import AdmisionService


@csrf_exempt
def subir_archivo_admision(request, admision_id, documentacion_id):
    if request.method == "POST" and request.FILES.get("archivo"):
        archivo_admision, created = AdmisionService.handle_file_upload(
            admision_id, documentacion_id, request.FILES["archivo"]
        )
        return JsonResponse({"success": True, "estado": archivo_admision.estado})
    return JsonResponse(
        {"success": False, "error": "No se recibió un archivo"}, status=400
    )


def eliminar_archivo_admision(request, admision_id, documentacion_id):
    if request.method == "DELETE":
        archivo = get_object_or_404(
            ArchivoAdmision, admision_id=admision_id, documentacion_id=documentacion_id
        )
        AdmisionService.delete_admision_file(archivo)
        return JsonResponse({"success": True, "nombre": archivo.documentacion.nombre})
    return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)


class AdmisionesTecnicosListView(ListView):
    model = Admision
    template_name = "admisiones_tecnicos_list.html"
    context_object_name = "comedores"

    def get_queryset(self):
        return AdmisionService.get_comedores_with_admision()


class AdmisionesTecnicosCreateView(CreateView):
    model = Admision
    template_name = "admisiones_tecnicos_form.html"
    form_class = AdmisionForm
    context_object_name = "admision"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(AdmisionService.get_admision_create_context(self.kwargs["pk"]))
        return context

    def post(self, request, *args, **kwargs):
        tipo_convenio_id = request.POST.get("tipo_convenio")
        if tipo_convenio_id:
            admision = AdmisionService.create_admision(
                self.kwargs["pk"], tipo_convenio_id
            )
            return redirect("admisiones_tecnicos_editar", pk=admision.pk)
        return self.get(request, *args, **kwargs)


class AdmisionesTecnicosUpdateView(UpdateView):
    model = Admision
    template_name = "admisiones_tecnicos_form.html"
    form_class = AdmisionForm
    context_object_name = "admision"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(AdmisionService.get_admision_update_context(self.get_object()))
        return context

    def post(self, request, *args, **kwargs):
        admision = self.get_object()

        if "tipo_convenio" in request.POST:
            if AdmisionService.update_convenio(
                admision, request.POST.get("tipo_convenio")
            ):
                messages.success(request, "Tipo de convenio actualizado correctamente.")
            allowed_hosts = [self.request.get_host()]  # Define trusted hosts
            if url_has_allowed_host_and_scheme(
                self.request.path_info, allowed_hosts=allowed_hosts
            ):
                return redirect(self.request.path_info)
            else:
                return redirect("/")

        return super().post(request, *args, **kwargs)
