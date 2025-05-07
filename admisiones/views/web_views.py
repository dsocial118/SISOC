import os
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, ListView, UpdateView, DetailView
from admisiones.forms.admisiones_forms import AdmisionForm, InformeTecnicoJuridicoForm, InformeTecnicoBaseForm
from admisiones.models.admisiones import Admision, ArchivoAdmision, ArchivoAdmision, InformeTecnicoBase, InformeTecnicoJuridico, InformeTecnicoPDF
from comedores.models.comedor import Comedor
from admisiones.services.admisiones_service import AdmisionService
from django.views.decorators.http import require_POST
import json
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from io import BytesIO
from xhtml2pdf import pisa

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
        return AdmisionService.get_comedores_with_admision(self.request.user)


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
            allowed_hosts = [self.request.get_host()] 
            if url_has_allowed_host_and_scheme(
                self.request.path_info, allowed_hosts=allowed_hosts
            ):
                return redirect(self.request.path_info)
            else:
                return redirect("/")
        if "estado" in request.POST and "documento_id" in request.POST:
            nuevo_estado = request.POST.get("estado")
            documento_id = request.POST.get("documento_id")
            archivo = get_object_or_404(ArchivoAdmision, admision_id=admision.id, documentacion_id=documento_id)
            if AdmisionService.update_estado_archivo(archivo, nuevo_estado):
                messages.success(request, "Estado actualizado correctamente.")
            else:
                messages.error(request, "Error al actualizar el estado.")
            return redirect(request.META.get('HTTP_REFERER'))

        return super().post(request, *args, **kwargs)

class InformeTecnicosCreateView(CreateView):
    template_name = "informe_tecnico_form.html"
    context_object_name = "informe_tecnico"

    def form_valid(self, form):
        admision_id = self.kwargs.get("admision_id")
        form.instance.admision_id = admision_id
        form.instance.estado = "Para revision"
        return super().form_valid(form)

    def get_success_url(self):
        admision_id = self.kwargs.get("admision_id")
        comedor = Admision.objects.get(pk=admision_id)
        return reverse("comedor_detalle", args=[comedor.comedor_id])


    def get_form_class(self):
        tipo = self.kwargs.get("tipo", "base")
        if tipo == "juridico":
            return InformeTecnicoJuridicoForm
        return InformeTecnicoBaseForm

    def get_queryset(self):
        tipo = self.kwargs.get("tipo", "base")
        if tipo == "juridico":
            return InformeTecnicoJuridico.objects.all()
        return InformeTecnicoBase.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tipo"] = self.kwargs.get("tipo", "base")
        context["admision"] = Admision.objects.get(id=self.kwargs.get("admision_id"))
        return context


class InformeTecnicosUpdateView(UpdateView):
    template_name = "informe_tecnico_form.html"
    context_object_name = "informe_tecnico"

    def get_queryset(self):
        tipo = self.kwargs.get("tipo", "base")
        if tipo == "juridico":
            return InformeTecnicoJuridico.objects.all()
        return InformeTecnicoBase.objects.all()

    def get_form_class(self):
        tipo = self.kwargs.get("tipo", "base")
        if tipo == "juridico":
            return InformeTecnicoJuridicoForm
        return InformeTecnicoBaseForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tipo"] = self.kwargs.get("tipo", "base")
        context["admision"] = self.object.admision
        context["comedor"] = self.object.admision.comedor  # ← agregás el comedor
        context["campos"] = [
            (field.verbose_name, field.value_from_object(self.object))
            for field in self.object._meta.fields
            if field.name not in ["id", "admision", "estado"]
        ]
        return context
    
    def form_valid(self, form):
        if form.instance.estado != "Validado":
            form.instance.estado = "Para revision"
        return super().form_valid(form)


    def get_success_url(self):
        return reverse("comedor_detalle", args=[self.object.admision.comedor_id])
    
class InformeTecnicoDetailView(DetailView):
    template_name = "informe_tecnico_detalle.html"
    context_object_name = "informe_tecnico"

    def get_queryset(self):
        tipo = self.kwargs.get("tipo", "base")
        if tipo == "juridico":
            return InformeTecnicoJuridico.objects.all()
        return InformeTecnicoBase.objects.all()
    
    def post(self, request, *args, **kwargs):
        tipo = self.kwargs.get("tipo", "base")
        if tipo == "juridico":
            self.object = get_object_or_404(InformeTecnicoJuridico, pk=self.kwargs['pk'])
        else:
            self.object = get_object_or_404(InformeTecnicoBase, pk=self.kwargs['pk'])

        nuevo_estado = request.POST.get("estado")
        if nuevo_estado in ["A subsanar", "Validado"]:
            self.object.estado = nuevo_estado
            self.object.save()

            if nuevo_estado == "Validado":
                self.generar_y_guardar_pdf(self.object, tipo)
        
        admision_id = self.object.admision_id
        comedor = get_object_or_404(Admision, pk=admision_id)
        return HttpResponseRedirect(reverse("comedor_detalle", kwargs={"pk": comedor.comedor_id}))
    
    def generar_y_guardar_pdf(self, informe, tipo):
        campos = [
            (field.verbose_name, field.value_from_object(informe))
            for field in informe._meta.fields
            if field.name not in ["id", "admision", "estado"]
        ]

        html = render_to_string("pdf_template.html", {
            "informe": informe,
            "campos": campos,
        })

        result = BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=result)
        if pisa_status.err:
            return  # opcional: loguear error

        nombre_archivo = f"{tipo}_informe_{informe.id}.pdf"
        pdf_file = ContentFile(result.getvalue(), name=nombre_archivo)

        InformeTecnicoPDF.objects.create(
            admision=informe.admision,
            tipo=tipo,
            informe_id=informe.id,
            archivo=pdf_file
        )


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tipo"] = self.kwargs.get("tipo", "base")
        context["admision"] = self.object.admision
        campos = [
            (field.verbose_name, getattr(self.object, field.name))  
            for field in self.object._meta.get_fields() 
            if field.name not in ["id", "admision", "estado"]
        ]
        context["campos"] = campos
        context["pdf"] = InformeTecnicoPDF.objects.filter(admision=self.object.admision, tipo=context["tipo"], informe_id=self.object.id).first()
        
        return context
