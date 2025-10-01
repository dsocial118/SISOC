from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, UpdateView, DetailView
from admisiones2.forms.admisiones_forms import (
    AdmisionForm,
    LegalesRectificarForm,
    LegalesNumIFForm,
    AnexoForm,
)
from admisiones2.models.admisiones import (
    Admision,
    ArchivoAdmision,
    Anexo,
)
from admisiones2.services.admisiones_service import AdmisionService


from admisiones2.services.informes_service import InformeService
from admisiones2.services.legales_service import LegalesService
from django.views.generic.edit import FormMixin
from django.template.loader import render_to_string

from django.urls import reverse
from django.http import HttpResponseRedirect


@require_POST
def subir_archivo_admision(request, admision_id, documentacion_id):
    archivo = request.FILES.get("archivo")
    if not archivo:
        return JsonResponse(
            {"success": False, "error": "No se recibio un archivo"}, status=400
        )

    archivo_admision, created = AdmisionService.handle_file_upload(
        admision_id, documentacion_id, archivo
    )
    if not archivo_admision:
        return JsonResponse(
            {"success": False, "error": "No se pudo guardar el archivo"}, status=400
        )

    documento = AdmisionService._serialize_documentacion(
        archivo_admision.documentacion,
        archivo_admision,
    )
    html = render_to_string(
        "admisiones2/includes/documento_row.html",
        {"doc": documento, "admision": archivo_admision.admision},
        request=request,
    )

    return JsonResponse(
        {
            "success": True,
            "html": html,
            "row_id": documento.get("row_id"),
            "documento": documento,
            "estado_display": documento.get("estado"),
            "estado_valor": documento.get("estado_valor"),
            "archivo_id": archivo_admision.id,
        }
    )


def eliminar_archivo_admision(request, admision_id, documentacion_id):
    if request.method == "DELETE":
        admision = get_object_or_404(Admision, pk=admision_id)

        if not request.user.is_superuser:

            comedor = admision.comedor
            if not comedor:
                return JsonResponse(
                    {"success": False, "error": "Admision sin comedor asociado."},
                    status=403,
                )

            if not AdmisionService._verificar_permiso_dupla(request.user, comedor):
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Sin permisos para modificar esta admision.",
                    },
                    status=403,
                )

        archivo = ArchivoAdmision.objects.filter(
            admision_id=admision_id, documentacion_id=documentacion_id
        ).first()

        if not archivo:
            archivo_id_param = request.GET.get("archivo_id")
            if archivo_id_param:
                archivo = ArchivoAdmision.objects.filter(
                    admision_id=admision_id, id=archivo_id_param
                ).first()

        if not archivo:
            archivo = get_object_or_404(
                ArchivoAdmision, admision_id=admision_id, id=documentacion_id
            )

        estado_actual = (archivo.estado or "").strip().lower()
        if estado_actual in {"aceptado", "a validar abogado"}:
            return JsonResponse(
                {
                    "success": False,
                    "error": "No se puede eliminar un documento en estado aceptado o a validar abogado.",
                },
                status=400,
            )

        documentacion = archivo.documentacion
        nombre_documento = (
            documentacion.nombre
            if documentacion
            else archivo.nombre_personalizado or "Documento adicional"
        )
        es_personalizado = documentacion is None

        documento_serializado = None
        if documentacion:
            documento_serializado = AdmisionService._serialize_documentacion(
                documentacion, None
            )

        AdmisionService.delete_admision_file(archivo)

        response_data = {
            "success": True,
            "nombre": nombre_documento,
            "personalizado": es_personalizado,
        }

        if documento_serializado:
            html = render_to_string(
                "admisiones2/includes/documento_row.html",
                {"doc": documento_serializado, "admision": admision},
                request=request,
            )
            response_data.update(
                {
                    "html": html,
                    "row_id": documento_serializado.get("row_id"),
                }
            )

        return JsonResponse(response_data)
    return JsonResponse({"success": False, "error": "Metodo no permitido"}, status=405)


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


@require_POST
def actualizar_numero_gde_archivo(request):
    resultado = AdmisionService.actualizar_numero_gde_ajax(request)

    if resultado.get("success"):
        return JsonResponse(
            {
                "success": True,
                "numero_gde": resultado.get("numero_gde"),
                "valor_anterior": resultado.get("valor_anterior"),
            }
        )
    else:
        return JsonResponse(
            {
                "success": False,
                "error": resultado.get("error", "Error desconocido"),
                "valor_anterior": resultado.get("valor_anterior"),
            },
            status=400,
        )


@require_POST
def crear_documento_personalizado(request, admision_id):
    archivo = request.FILES.get("archivo")
    nombre = request.POST.get("nombre", "")

    archivo_admision, error = AdmisionService.crear_documento_personalizado(
        admision_id, nombre, archivo, request.user
    )

    if not archivo_admision:
        status_code = 403 if error and "permiso" in error.lower() else 400
        return JsonResponse(
            {
                "success": False,
                "error": error or "No se pudo guardar el documento.",
            },
            status=status_code,
        )

    documento = AdmisionService.serialize_documento_personalizado(archivo_admision)
    html = render_to_string(
        "admisiones2/includes/documento_row.html",
        {"doc": documento, "admision": archivo_admision.admision},
        request=request,
    )

    return JsonResponse(
        {"success": True, "documento": documento, "html": html}, status=201
    )


class AdmisionesTecnicosListView(ListView):
    model = Admision
    template_name = "admisiones2/admisiones_tecnicos_list.html"
    context_object_name = "comedores"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("busqueda", "")
        return AdmisionService.get_comedores_filtrados(self.request.user, query)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("busqueda", "")

        context["breadcrumb_items"] = [
            {"name": "Admisiones", "url": "admisiones_tecnicos_listar"},
            {"name": "Listar", "active": True},
        ]

        return context


class AdmisionesTecnicosCreateView(CreateView):
    model = Admision
    template_name = "admisiones2/admisiones_tecnicos_form.html"
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
    template_name = "admisiones2/admisiones_tecnicos_form.html"
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
    template_name = "admisiones2/informe_tecnico_form.html"
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
        action = self.request.POST.get("action") if self.request.method == "POST" else None
        kwargs["admision"] = admision
        kwargs["require_full"] = (action == "submit")
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admision, tipo = InformeService.get_admision_y_tipo_from_kwargs(self.kwargs)
        context.setdefault("admision", admision)
        context.setdefault("tipo", tipo)
        context.setdefault("comedor", getattr(admision, "comedor", None))

        action = self.request.POST.get("action") if self.request.method == "POST" else None
        require_full = (action == "submit")

        if "anexof" not in context or self.request.method == "POST":
            data = self.request.POST if self.request.method == "POST" else None
            files = self.request.FILES if self.request.method == "POST" else None
            context["anexof"] = InformeService.get_anexo_form(
                admision, data, files, require_full=require_full
            )

        return context

    def form_valid(self, form):
        admision, tipo = InformeService.get_admision_y_tipo_from_kwargs(self.kwargs)
        form.instance.tipo = tipo
        action = self.request.POST.get("action")

        resultado = InformeService.guardar_informe_y_anexo(
            form,
            admision,
            self.request.POST,
            self.request.FILES,
            es_creacion=True,
            action=action,
        )

        if not resultado.get("success"):
            context = self.get_context_data(form=form)
            context["anexof"] = resultado.get("anexof")
            return self.render_to_response(context)

        self.object = resultado.get("informe")
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def get_success_url(self):
        return reverse("admisiones_tecnicos_editar", args=[self.object.admision.id])

class InformeTecnicosUpdateView(UpdateView):
    template_name = "admisiones2/informe_tecnico_form.html"
    context_object_name = "informe_tecnico"

    def get_queryset(self):
        tipo = InformeService.get_tipo_from_kwargs(self.kwargs)
        return InformeService.get_queryset_informe_por_tipo(tipo)

    def get_form_class(self):
        tipo = InformeService.get_tipo_from_kwargs(self.kwargs)
        return InformeService.get_form_class_por_tipo(tipo)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        action = self.request.POST.get("action") if self.request.method == "POST" else None
        kwargs["require_full"] = (action == "submit")
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tipo = InformeService.get_tipo_from_kwargs(self.kwargs)
        contexto_servicio = InformeService.get_informe_update_context(self.object, tipo)
        for clave, valor in contexto_servicio.items():
            context.setdefault(clave, valor)

        action = self.request.POST.get("action") if self.request.method == "POST" else None
        require_full = (action == "submit")

        data = self.request.POST if self.request.method == "POST" else None
        files = self.request.FILES if self.request.method == "POST" else None
        if "anexof" not in context or self.request.method == "POST":
            context["anexof"] = InformeService.get_anexo_form(
                self.object.admision, data, files, require_full=require_full
            )

        return context

    def form_valid(self, form):
        admision = form.instance.admision
        action = self.request.POST.get("action")

        resultado = InformeService.guardar_informe_y_anexo(
            form,
            admision,
            self.request.POST,
            self.request.FILES,
            es_creacion=False,
            action=action,
        )

        if not resultado.get("success"):
            context = self.get_context_data(form=form)
            context["anexof"] = resultado.get("anexof")
            return self.render_to_response(context)

        self.object = resultado.get("informe")
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def get_success_url(self):
        return reverse("admisiones_tecnicos_editar", args=[self.object.admision.id])


class InformeTecnicoDetailView(DetailView):
    template_name = "admisiones2/informe_tecnico_detalle.html"
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
    template_name = "admisiones2/admisiones_legales_list.html"
    context_object_name = "admisiones"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("busqueda", "")
        return LegalesService.get_admisiones_legales_filtradas(query)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("busqueda", "")

        context["breadcrumb_items"] = [
            {"name": "Expedientes", "url": "admisiones_legales_listar"},
            {"name": "Listar", "active": True},
        ]

        return context


class AdmisionesLegalesDetailView(FormMixin, DetailView):
    model = Admision
    template_name = "admisiones2/admisiones_legales_detalle.html"
    context_object_name = "admision"
    form_class = LegalesRectificarForm

    def get_success_url(self):
        return reverse("admisiones_legales_ver", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(LegalesService.get_legales_context(self.get_object()))
        if "form" not in context:
            context["form"] = self.get_form()
        if "form_legales_num_if" not in context:
            context["form_legales_num_if"] = LegalesNumIFForm(instance=self.get_object())
        return context

    def post(self, request, *args, **kwargs):
        admision = self.get_object()
        return LegalesService.procesar_post_legales(request, admision)


class AnexoCreateView(CreateView):
    model = Anexo
    form_class = AnexoForm
    template_name = "admisiones2/anexo_form.html"

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
    template_name = "admisiones2/anexo_form.html"

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
    template_name = "admisiones2/informe_tecnico_complementario_detalle.html"
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
