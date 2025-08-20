from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, UpdateView, DetailView
from admisiones.forms.admisiones_forms import (
    AdmisionForm,
    LegalesRectificarForm,
    AnexoForm,
)
from admisiones.models.admisiones import (
    Admision,
    ArchivoAdmision,
    Anexo,
)
from admisiones.services.admisiones_service import AdmisionService
from admisiones.services.informes_service import InformeService
from admisiones.services.legales_service import LegalesService
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
        query = self.request.GET.get("busqueda", "")
        return AdmisionService.get_comedores_filtrados(self.request.user, query)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("busqueda", "")

        # Breadcrumb items
        context["breadcrumb_items"] = [
            {"name": "Admisiones", "url": "admisiones_tecnicos_listar"},
            {"name": "Listar", "active": True},
        ]

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
        success, message = AdmisionService.procesar_post_update(request, admision)

        if success is not None:
            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)
            return redirect(self.request.path_info)

        return super().post(request, *args, **kwargs)


class InformeTecnicosCreateView(CreateView):
    template_name = "informe_tecnico_form.html"
    context_object_name = "informe_tecnico"

    def get_form_class(self):
        tipo = self.kwargs.get("tipo", "base")
        return InformeService.get_form_class_por_tipo(tipo)

    def get_queryset(self):
        tipo = self.kwargs.get("tipo", "base")
        return InformeService.get_queryset_informe_por_tipo(tipo)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        admision, _ = InformeService.get_admision_y_tipo_from_kwargs(self.kwargs)
        kwargs["admision"] = admision
        return kwargs

    def form_valid(self, form):
        admision, tipo = InformeService.get_admision_y_tipo_from_kwargs(self.kwargs)
        form.instance.tipo = tipo
        InformeService.preparar_informe_para_creacion(form.instance, admision.id)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("admisiones_tecnicos_editar", args=[self.object.admision.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            InformeService.get_informe_create_context(
                self.kwargs.get("admision_id"), self.kwargs.get("tipo", "base")
            )
        )
        return context


class InformeTecnicosUpdateView(UpdateView):
    template_name = "informe_tecnico_form.html"
    context_object_name = "informe_tecnico"

    def get_queryset(self):
        tipo = InformeService.get_tipo_from_kwargs(self.kwargs)
        return InformeService.get_queryset_informe_por_tipo(tipo)

    def get_form_class(self):
        tipo = InformeService.get_tipo_from_kwargs(self.kwargs)
        return InformeService.get_form_class_por_tipo(tipo)

    def form_valid(self, form):
        InformeService.verificar_estado_para_revision(form.instance)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("admisiones_tecnicos_editar", args=[self.object.admision.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tipo = InformeService.get_tipo_from_kwargs(self.kwargs)
        context.update(InformeService.get_informe_update_context(self.object, tipo))
        return context


class InformeTecnicoDetailView(DetailView):
    template_name = "informe_tecnico_detalle.html"
    context_object_name = "informe_tecnico"

    def get_queryset(self):
        tipo = self.kwargs.get("tipo", "base")
        return InformeService.get_queryset_informe_por_tipo(tipo)

    def post(self, request, *args, **kwargs):
        tipo = self.kwargs.get("tipo", "base")
        informe = InformeService.get_informe_por_tipo_y_pk(tipo, kwargs["pk"])

        InformeService.procesar_revision_informe(request, tipo, informe)

        return HttpResponseRedirect(
            reverse("admisiones_tecnicos_editar", args=[informe.admision.id])
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tipo = self.kwargs.get("tipo", "base")
        context.update(InformeService.get_context_informe_detail(self.object, tipo))
        return context


class AdmisionesLegalesListView(ListView):
    model = Admision
    template_name = "admisiones_legales_list.html"
    context_object_name = "admisiones"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("busqueda", "")
        return LegalesService.get_admisiones_legales_filtradas(query)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("busqueda", "")

        # Breadcrumb items
        context["breadcrumb_items"] = [
            {"name": "Expedientes", "url": "admisiones_legales_listar"},
            {"name": "Listar", "active": True},
        ]

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
        context.update(LegalesService.get_legales_context(self.get_object()))
        if "form" not in context:
            context["form"] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        admision = self.get_object()
        return LegalesService.procesar_post_legales(request, admision)


class AnexoCreateView(CreateView):
    model = Anexo
    form_class = AnexoForm
    template_name = "anexo_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.admision = AdmisionService.get_admision_instance(kwargs["admision_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"admision": self.admision})
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["admision"] = self.admision
        return kwargs

    def form_valid(self, form):
        form.instance.admision = self.admision
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("admisiones_tecnicos_editar", kwargs={"pk": self.admision.id})


class AnexoUpdateView(UpdateView):
    model = Anexo
    form_class = AnexoForm
    template_name = "anexo_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.admision = AdmisionService.get_admision_instance(kwargs["admision_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["admision"] = self.admision
        return context

    def get_object(self, queryset=None):
        return get_object_or_404(Anexo, admision=self.admision)

    def get_success_url(self):
        return reverse("admisiones_tecnicos_editar", kwargs={"pk": self.admision.id})


class InformeTecnicoComplementarioDetailView(DetailView):
    template_name = "informe_tecnico_complementario_detalle.html"
    context_object_name = "informe_tecnico"

    def get_queryset(self):
        tipo = self.kwargs.get("tipo", "base")
        return InformeService.get_queryset_informe_por_tipo(tipo)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        campos_modificados = {
            key.replace("campo_", ""): value.strip()
            for key, value in request.POST.items()
            if key.startswith("campo_") and value.strip()
        }
        informe = InformeService.guardar_campos_complementarios(
            informe_tecnico=self.object,
            campos_dict=campos_modificados,
            usuario=request.user,
        )
        InformeService.generar_y_guardar_pdf_complementario(informe)

        return HttpResponseRedirect(
            reverse("admisiones_tecnicos_editar", args=[self.object.admision.id])
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tipo = self.kwargs.get("tipo", "base")
        context.update(InformeService.get_context_informe_detail(self.object, tipo))
        return context
