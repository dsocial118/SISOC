import os
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, UpdateView, DetailView
from admisiones.forms.admisiones_forms import (
    AdmisionForm,
    CaratularForm,
    LegalesRectificarForm,
    AnexoForm,
)
from admisiones.models.admisiones import (
    Admision,
    ArchivoAdmision,
    ArchivoAdmision,
    InformeTecnicoPDF,
    Anexo,
    CampoASubsanar,
    ObservacionGeneralInforme,
)
from admisiones.services.admisiones_service import AdmisionService
from django.views.generic.edit import FormMixin

from django.urls import reverse
from django.http import HttpResponseRedirect


@require_POST
def subir_archivo_admision(request, admision_id, documentacion_id):
    if request.FILES.get("archivo"):
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


def actualizar_estado_archivo(request):
    resultado = AdmisionService.actualizar_estado_ajax(request)

    if resultado.get("success"):
        return JsonResponse(
            {
                "success": True,
                "nuevo_estado": resultado.get("nuevo_estado"),
                "grupo_usuario": resultado.get("grupo_usuario"),
                "mostrar_select": resultado.get("mostrar_select", False),
                "opciones": resultado.get("opciones", []),
            }
        )
    else:
        return JsonResponse(
            {
                "success": False,
                "error": resultado.get("error", "Error desconocido"),
            },
            status=400,
        )


class AdmisionesTecnicosListView(ListView):
    model = Admision
    template_name = "admisiones_tecnicos_list.html"
    context_object_name = "comedores"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("busqueda", "").strip().lower()
        comedores = AdmisionService.get_comedores_with_admision(self.request.user)

        if query:
            comedores = comedores.filter(
                Q(nombre__icontains=query)
                | Q(provincia__nombre__icontains=query)
                | Q(tipocomedor__nombre__icontains=query)
                | Q(calle__icontains=query)
                | Q(numero__icontains=query)
                | Q(referente__nombre__icontains=query)
                | Q(referente__apellido__icontains=query)
                | Q(referente__celular__icontains=query)
            )

        return comedores

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("busqueda", "")
        return context


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

        if "mandarLegales" in request.POST:
            if AdmisionService.marcar_como_enviado_a_legales(admision, request.user):
                messages.success(
                    request, "La admisión fue enviada a legales correctamente."
                )
            else:
                messages.info(
                    request, "La admisión ya estaba marcada como enviada a legales."
                )
            return redirect(self.request.path_info)

        if "btnDisponibilizarAcomp" in request.POST:
            if AdmisionService.marcar_como_enviado_a_acompaniamiento(
                admision, request.user
            ):
                messages.success(request, "Se envio a Acompañamiento correctamente.")
            else:
                messages.error(request, "Error al enviar a Acompañamiento.")
            return redirect(self.request.path_info)
        
        if "btnRectificarDocumentacion" in request.POST:
            if AdmisionService.marcar_como_documentacion_rectificada(
                admision, request.user
            ):
                messages.success(request, "Se rectificó la documentación.")
            else:
                messages.error(request, "Error al querer realizar la rectificación.")
            return redirect(self.request.path_info)

        if "btnCaratulacion" in request.POST:
            form = CaratularForm(request.POST, instance=admision)
            if form.is_valid():
                form.save()
                messages.success(
                    request, "Caratulación del expediente guardado correctamente."
                )
            else:
                messages.error(request, "Error al guardar la caratulación.")
            return redirect(self.request.path_info)

        if "tipo_convenio" in request.POST:
            if AdmisionService.update_convenio(
                admision, request.POST.get("tipo_convenio")
            ):
                messages.success(request, "Tipo de convenio actualizado correctamente.")
            return redirect(self.request.path_info)

        return super().post(request, *args, **kwargs)


class InformeTecnicosCreateView(CreateView):
    template_name = "informe_tecnico_form.html"
    context_object_name = "informe_tecnico"

    def get_form_class(self):
        tipo = self.kwargs.get("tipo", "base")
        return AdmisionService.get_form_class_por_tipo(tipo)

    def get_queryset(self):
        tipo = self.kwargs.get("tipo", "base")
        return AdmisionService.get_queryset_informe_por_tipo(tipo)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        admision_id = self.kwargs.get("admision_id")
        admision = AdmisionService.get_admision(admision_id)
        kwargs["admision"] = admision
        return kwargs

    def form_valid(self, form):
        tipo = self.kwargs.get("tipo", "base")
        admision_id = self.kwargs.get("admision_id")
        form.instance.tipo = tipo
        AdmisionService.preparar_informe_para_creacion(form.instance, admision_id)
        return super().form_valid(form)

    def get_success_url(self):
        admision_id = self.object.admision.id
        return reverse("admisiones_tecnicos_editar", args=[admision_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admision_id = self.kwargs.get("admision_id")
        anexo = Anexo.objects.filter(admision_id=admision_id).first()
        context["tipo"] = self.kwargs.get("tipo", "base")
        context["admision"] = AdmisionService.get_admision(admision_id)
        context["anexo"] = anexo
        return context


class InformeTecnicosUpdateView(UpdateView):
    template_name = "informe_tecnico_form.html"
    context_object_name = "informe_tecnico"

    def get_queryset(self):
        tipo = self.kwargs.get("tipo", "base")
        return AdmisionService.get_queryset_informe_por_tipo(tipo)

    def get_form_class(self):
        tipo = self.kwargs.get("tipo", "base")
        return AdmisionService.get_form_class_por_tipo(tipo)

    def form_valid(self, form):
        AdmisionService.verificar_estado_para_revision(form.instance)
        return super().form_valid(form)

    def get_success_url(self):
        admision_id = self.object.admision.id
        return reverse("admisiones_tecnicos_editar", args=[admision_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tipo = self.kwargs.get("tipo", "base")
        informe = self.object
        campos_a_subsanar = CampoASubsanar.objects.filter(informe=informe).values_list(
            "campo", flat=True
        )
        try:
            observacion = ObservacionGeneralInforme.objects.get(informe=informe)
        except ObservacionGeneralInforme.DoesNotExist:
            observacion = None
        context.update(
            {
                "tipo": tipo,
                "admision": informe.admision,
                "comedor": informe.admision.comedor,
                "campos": AdmisionService.get_campos_visibles_informe(informe),
                "anexo": Anexo.objects.filter(admision_id=informe.admision.id).first(),
                "campos_a_subsanar": list(campos_a_subsanar),
                "observacion": observacion,
            }
        )
        return context


class InformeTecnicoDetailView(DetailView):
    template_name = "informe_tecnico_detalle.html"
    context_object_name = "informe_tecnico"

    def get_queryset(self):
        tipo = self.kwargs.get("tipo", "base")
        return AdmisionService.get_queryset_informe_por_tipo(tipo)

    def post(self, request, *args, **kwargs):
        tipo = self.kwargs.get("tipo", "base")
        informe = AdmisionService.get_informe_por_tipo_y_pk(tipo, kwargs["pk"])

        nuevo_estado = request.POST.get("estado")

        if nuevo_estado in ["A subsanar", "Validado"]:
            AdmisionService.actualizar_estado_informe(informe, nuevo_estado, tipo)

            if nuevo_estado == "A subsanar":
                campos_a_subsanar = request.POST.getlist("campos_a_subsanar")
                observacion = request.POST.get("observacion", "").strip()

                CampoASubsanar.objects.filter(informe=informe).delete()

                for campo in campos_a_subsanar:
                    CampoASubsanar.objects.create(informe=informe, campo=campo)

                obs_obj, created = ObservacionGeneralInforme.objects.get_or_create(
                    informe=informe
                )
                obs_obj.texto = observacion
                obs_obj.save()
            else:
                CampoASubsanar.objects.filter(informe=informe).delete()
                ObservacionGeneralInforme.objects.filter(informe=informe).delete()

        admision_id = informe.admision.id
        return HttpResponseRedirect(
            reverse("admisiones_tecnicos_editar", args=[admision_id])
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tipo = self.kwargs.get("tipo", "base")
        informe = self.object

        context["tipo"] = tipo
        context["admision"] = informe.admision
        context["campos"] = AdmisionService.get_campos_visibles_informe(informe)
        context["pdf"] = InformeTecnicoPDF.objects.filter(
            admision=informe.admision, tipo=tipo, informe_id=informe.id
        ).first()
        return context


class AdmisionesLegalesListView(ListView):
    model = Admision
    template_name = "admisiones_legales_list.html"
    context_object_name = "admisiones"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("busqueda", "").strip().lower()
        queryset = Admision.objects.filter(enviado_legales=True).select_related(
            "comedor", "tipo_convenio"
        )

        if query:
            queryset = queryset.filter(
                Q(comedor__nombre__icontains=query)
                | Q(tipo_convenio__nombre__icontains=query)
                | Q(num_expediente__icontains=query)
                | Q(num_if__icontains=query)
                | Q(estado_legales__icontains=query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("busqueda", "")
        return context


class AdmisionesLegalesDetailView(FormMixin, DetailView):
    model = Admision
    template_name = "admisiones_legales_detalle.html"
    context_object_name = "admision"
    form_class = LegalesRectificarForm

    def get_success_url(self):
        return reverse("admisiones_legales_ver", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(AdmisionService.get_legales_context(self.get_object()))
        if "form" not in context:
            context["form"] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        admision = self.get_object()

        if "btnLegalesNumIF" in request.POST:
            return AdmisionService.guardar_legales_num_if(request, admision)

        if "ValidacionJuridicos" in request.POST:
            return AdmisionService.validar_juridicos(request, admision)

        if "btnRESO" in request.POST:
            return AdmisionService.guardar_formulario_reso(request, admision)

        if "btnProyectoConvenio" in request.POST:
            return AdmisionService.guardar_formulario_proyecto_convenio(
                request, admision
            )

        if "btnObservaciones" in request.POST:
            return AdmisionService.enviar_a_rectificar(request, admision)

        if "btnDocumentoExpediente" in request.POST:
            return AdmisionService.guardar_documento_expediente(request, admision)


class AnexoCreateView(CreateView):
    model = Anexo
    form_class = AnexoForm
    template_name = "anexo_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admision_id = self.kwargs.get("admision_id")
        admision = Admision.objects.filter(id=admision_id).first()
        context["admision"] = admision
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        admision_id = self.kwargs.get("admision_id")
        admision = AdmisionService.get_admision(admision_id)
        kwargs["admision"] = admision
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.admision = get_object_or_404(Admision, id=kwargs["admision_id"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.admision = self.admision
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("admisiones_tecnicos_editar", kwargs={"pk": self.admision.id})

    def form_invalid(self, form):
        print("Form errors:", form.errors)
        return super().form_invalid(form)


class AnexoUpdateView(UpdateView):
    model = Anexo
    form_class = AnexoForm
    template_name = "anexo_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admision_id = self.kwargs.get("admision_id")
        admision = Admision.objects.filter(id=admision_id).first()
        context["admision"] = admision
        return context

    def get_object(self, queryset=None):
        admision_id = self.kwargs["admision_id"]
        return get_object_or_404(Anexo, admision_id=admision_id)

    def get_success_url(self):
        return reverse(
            "admisiones_tecnicos_editar", kwargs={"pk": self.object.admision.id}
        )
