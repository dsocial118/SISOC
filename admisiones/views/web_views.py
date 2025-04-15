import os
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.db.models import OuterRef, Subquery
from django.db import models
from django.views.generic import (
    CreateView,
    ListView,
    UpdateView,
)
from admisiones.forms.admisiones_forms import (
    AdmisionForm,
)
from admisiones.models.admisiones import (
    Admision,
    TipoConvenio,
    Documentacion,
    ArchivoAdmision,
)
from comedores.models.comedor import Comedor  # Confirmar con Juani: si el Modelo Comedor sigue vigente y utilizable o no.

from django.views.decorators.csrf import csrf_exempt
from django.conf import settings


@csrf_exempt
def subir_archivo_admision(request, admision_id, documentacion_id):
    if request.method == "POST" and request.FILES.get("archivo"):
        archivo = request.FILES["archivo"]
        admision = get_object_or_404(Admision, pk=admision_id)
        documentacion = get_object_or_404(Documentacion, pk=documentacion_id)

        # Guardamos el archivo en el modelo ArchivoAdmision
        archivo_admision, created = ArchivoAdmision.objects.update_or_create(
            admision=admision,
            documentacion=documentacion,
            defaults={"archivo": archivo, "estado": "A Validar"},
        )

        # Respuesta JSON correcta
        return JsonResponse({"success": True, "estado": archivo_admision.estado})

    # Si no es POST o no hay archivo
    return JsonResponse(
        {"success": False, "error": "No se recibió un archivo"}, status=400
    )


def eliminar_archivo_admision(request, admision_id, documentacion_id):
    if request.method == "DELETE":
        archivo = get_object_or_404(
            ArchivoAdmision, admision_id=admision_id, documentacion_id=documentacion_id
        )

        # Eliminar el archivo físico del servidor
        if archivo.archivo:
            archivo_path = os.path.join(settings.MEDIA_ROOT, str(archivo.archivo))
            if os.path.exists(archivo_path):
                os.remove(archivo_path)

        # Eliminar de la base de datos
        archivo.delete()

        return JsonResponse({"success": True, "nombre": archivo.documentacion.nombre})

    return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)


class AdmisionesTecnicosListView(ListView):
    model = Admision
    template_name = "comedores/admisiones_tecnicos_list.html"
    context_object_name = "comedores"

    def get_queryset(self):
        admision_subquery = Admision.objects.filter(comedor=OuterRef("pk")).values(
            "id"
        )[:1]
        return Comedor.objects.annotate(admision_id=Subquery(admision_subquery))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class AdmisionesTecnicosCreateView(CreateView):
    model = Admision
    template_name = "comedor/admisiones_tecnicos_form.html"
    form_class = AdmisionForm
    context_object_name = "admision"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs["pk"]
        comedor = get_object_or_404(Comedor, pk=pk)
        convenios = TipoConvenio.objects.all()

        context["comedor"] = comedor
        context["convenios"] = convenios
        context["es_crear"] = True

        return context

    def post(self, request, *args, **kwargs):
        pk = self.kwargs["pk"]
        comedor = get_object_or_404(Comedor, pk=pk)
        tipo_convenio_id = request.POST.get("tipo_convenio")

        if tipo_convenio_id:
            tipo_convenio = get_object_or_404(TipoConvenio, pk=tipo_convenio_id)
            admision = Admision.objects.create(
                comedor=comedor, tipo_convenio=tipo_convenio
            )
            return redirect(
                "admisiones_tecnicos_editar", pk=admision.pk
            )  # Redirige a la edición

        return self.get(request, *args, **kwargs)  # Si hay un error, recarga la página


class AdmisionesTecnicosUpdateView(UpdateView):
    model = Admision
    template_name = "comedor/admisiones_tecnicos_form.html"
    form_class = AdmisionForm
    context_object_name = "admision"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admision = self.get_object()
        comedor = Comedor.objects.get(pk=admision.comedor_id)
        convenios = TipoConvenio.objects.all()

        # Obtener documentación requerida para el convenio actual
        documentaciones = Documentacion.objects.filter(
            models.Q(tipo="todos") | models.Q(convenios=admision.tipo_convenio)
        ).distinct()

        # Obtener archivos subidos para el convenio actual
        archivos_subidos = ArchivoAdmision.objects.filter(admision=admision)
        archivos_dict = {
            archivo.documentacion.id: archivo for archivo in archivos_subidos
        }

        # Crear lista de documentos del convenio actual
        documentos_info = []
        for doc in documentaciones:
            archivo_info = archivos_dict.get(doc.id)
            documentos_info.append(
                {
                    "id": doc.id,
                    "nombre": doc.nombre,
                    "estado": archivo_info.estado if archivo_info else "Pendiente",
                    "archivo_url": archivo_info.archivo.url if archivo_info else None,
                }
            )

        context["documentos"] = documentos_info
        context["comedor"] = comedor
        context["convenios"] = convenios

        return context

    def post(self, request, *args, **kwargs):
        admision = self.get_object()

        if "tipo_convenio" in request.POST:  # Si viene del modal
            nuevo_convenio_id = request.POST.get("tipo_convenio")
            if nuevo_convenio_id:
                nuevo_convenio = TipoConvenio.objects.get(pk=nuevo_convenio_id)
                admision.tipo_convenio = nuevo_convenio
                admision.save()
                archivos = ArchivoAdmision.objects.filter(admision=admision).all()
                archivos.delete()
                messages.success(request, "Tipo de convenio actualizado correctamente.")

            return redirect(self.request.path_info)  # Recarga la misma página

        return super().post(request, *args, **kwargs)  # Manejo normal del formulario