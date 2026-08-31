from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from admisiones.forms.templates_informe_tecnico_forms import (
    IncidenciaTemplateInformeTecnicoForm,
    PlantillaInformeTecnicoForm,
    PlantillaInformeTecnicoVersionForm,
)
from admisiones.models.admisiones import (
    IncidenciaTemplateInformeTecnico,
    InformeTecnico,
    PlantillaInformeTecnico,
    PlantillaInformeTecnicoVersion,
    TipoConvenio,
    VariableTemplateInformeTecnico,
)
from admisiones.services.informes_service import InformeService
from admisiones.services.templates_informe_tecnico_service import (
    PlantillaInformeTecnicoService,
)
from iam.services import user_has_permission_code


TEMPLATE_MANAGE_PERMISSION = "admisiones.gestionar_templates_informe_tecnico"


class GestorTemplatesPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        return user_has_permission_code(
            self.request.user,
            TEMPLATE_MANAGE_PERMISSION,
        )


class PlantillaInformeTecnicoListView(GestorTemplatesPermissionMixin, ListView):
    template_name = "admisiones/templates_informes_tecnicos/list.html"
    context_object_name = "plantillas"
    paginate_by = 50

    def get_queryset(self):
        estado = (self.request.GET.get("estado") or "activa").strip().lower()
        queryset = PlantillaInformeTecnico.objects.select_related(
            "tipo_convenio",
            "publicacion_vigente",
            "publicacion_vigente__version",
        ).order_by("codigo")
        if estado in {"activa", "inactiva", "eliminada"}:
            queryset = queryset.filter(estado=estado)
        busqueda = (self.request.GET.get("q") or "").strip()
        if busqueda:
            queryset = queryset.filter(
                Q(nombre__icontains=busqueda) | Q(codigo__icontains=busqueda)
            )

        filtros = {
            "tipo_admision": self.request.GET.get("tipo_admision", "").strip(),
            "tipo_convenio": self.request.GET.get("tipo_convenio", "").strip(),
            "es_ex_pnud": self.request.GET.get("es_ex_pnud", "").strip(),
            "estado_convenio_pnud": self.request.GET.get(
                "estado_convenio_pnud", ""
            ).strip(),
            "tipo_renovacion": self.request.GET.get("tipo_renovacion", "").strip(),
            "estado_financiamiento": self.request.GET.get(
                "estado_financiamiento", ""
            ).strip(),
            "informe_complementario_modifica_prestaciones": self.request.GET.get(
                "informe_complementario_modifica_prestaciones", ""
            ).strip(),
        }
        valores_validos = {
            "tipo_admision": dict(
                PlantillaInformeTecnico._meta.get_field("tipo_admision").choices
            ),
            "es_ex_pnud": dict(
                PlantillaInformeTecnico._meta.get_field("es_ex_pnud").choices
            ),
            "estado_convenio_pnud": dict(
                PlantillaInformeTecnico._meta.get_field("estado_convenio_pnud").choices
            ),
            "tipo_renovacion": dict(
                PlantillaInformeTecnico._meta.get_field("tipo_renovacion").choices
            ),
            "estado_financiamiento": dict(
                PlantillaInformeTecnico._meta.get_field("estado_financiamiento").choices
            ),
            "informe_complementario_modifica_prestaciones": dict(
                PlantillaInformeTecnico._meta.get_field(
                    "informe_complementario_modifica_prestaciones"
                ).choices
            ),
        }
        for campo, opciones in valores_validos.items():
            if filtros[campo] in opciones:
                queryset = queryset.filter(**{campo: filtros[campo]})

        if filtros["tipo_convenio"].isdigit():
            queryset = queryset.filter(tipo_convenio_id=filtros["tipo_convenio"])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["estado_filtro"] = (self.request.GET.get("estado") or "activa").strip()
        context["busqueda"] = (self.request.GET.get("q") or "").strip()
        context["filtros"] = {
            campo: (self.request.GET.get(campo) or "").strip()
            for campo in (
                "tipo_admision",
                "tipo_convenio",
                "es_ex_pnud",
                "estado_convenio_pnud",
                "tipo_renovacion",
                "estado_financiamiento",
                "informe_complementario_modifica_prestaciones",
            )
        }
        context["tipos_admision"] = PlantillaInformeTecnico._meta.get_field(
            "tipo_admision"
        ).choices
        context["tipos_convenio"] = TipoConvenio.objects.order_by("nombre")
        context["opciones_ex_pnud"] = PlantillaInformeTecnico._meta.get_field(
            "es_ex_pnud"
        ).choices
        context["estados_convenio_pnud"] = PlantillaInformeTecnico._meta.get_field(
            "estado_convenio_pnud"
        ).choices
        context["tipos_renovacion"] = PlantillaInformeTecnico._meta.get_field(
            "tipo_renovacion"
        ).choices
        context["estados_financiamiento"] = PlantillaInformeTecnico._meta.get_field(
            "estado_financiamiento"
        ).choices
        context["opciones_informe_complementario"] = (
            PlantillaInformeTecnico._meta.get_field(
                "informe_complementario_modifica_prestaciones"
            ).choices
        )
        return context


class PlantillaInformeTecnicoCreateView(GestorTemplatesPermissionMixin, CreateView):
    model = PlantillaInformeTecnico
    form_class = PlantillaInformeTecnicoForm
    template_name = "admisiones/templates_informes_tecnicos/form.html"

    def form_valid(self, form):
        plantilla, version = PlantillaInformeTecnicoService.crear_plantilla(
            form.cleaned_data,
            self.request.user,
        )
        messages.success(
            self.request,
            f"Template {plantilla.codigo} creado con su versión {version.numero} en preparación.",
        )
        return redirect("gestor_templates_detalle", pk=plantilla.pk)


class PlantillaInformeTecnicoDetailView(GestorTemplatesPermissionMixin, DetailView):
    model = PlantillaInformeTecnico
    template_name = "admisiones/templates_informes_tecnicos/detail.html"
    context_object_name = "plantilla"

    def get_queryset(self):
        return PlantillaInformeTecnico.objects.select_related(
            "tipo_convenio",
            "publicacion_vigente",
            "publicacion_vigente__version",
        ).prefetch_related("versiones")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        versiones = list(self.object.versiones.all())
        context["borrador_actual"] = next(
            (version for version in versiones if version.estado == "borrador"),
            None,
        )
        context["versiones_historial"] = [
            version for version in versiones if version.estado != "borrador"
        ]
        return context


class PlantillaInformeTecnicoVersionCreateView(GestorTemplatesPermissionMixin, View):
    def post(self, request, plantilla_pk):
        plantilla = PlantillaInformeTecnico.objects.filter(pk=plantilla_pk).first()
        if plantilla is None:
            messages.error(request, "No se encontró el template solicitado.")
            return redirect("gestor_templates_listar")

        origen = None
        origen_id = request.POST.get("origen_version_id")
        if origen_id:
            origen = plantilla.versiones.filter(pk=origen_id).first()
        elif hasattr(plantilla, "publicacion_vigente"):
            origen = plantilla.publicacion_vigente.version
        version, mensaje = PlantillaInformeTecnicoService.crear_version_borrador(
            plantilla,
            request.user,
            origen=origen,
        )
        if version is None:
            messages.error(request, mensaje)
            return redirect("gestor_templates_detalle", pk=plantilla.pk)
        messages.success(request, mensaje)
        return redirect(
            "gestor_templates_version_editar",
            plantilla_pk=plantilla.pk,
            version_pk=version.pk,
        )


class PlantillaInformeTecnicoVersionDiscardView(GestorTemplatesPermissionMixin, View):
    def post(self, request, plantilla_pk, version_pk):
        version = get_object_or_404(
            PlantillaInformeTecnicoVersion,
            pk=version_pk,
            plantilla_id=plantilla_pk,
        )
        exito, mensaje = PlantillaInformeTecnicoService.descartar_borrador(
            version,
            request.user,
        )
        if exito:
            messages.success(request, mensaje)
        else:
            messages.error(request, mensaje)
        return redirect("gestor_templates_detalle", pk=plantilla_pk)


class PlantillaInformeTecnicoVersionUpdateView(
    GestorTemplatesPermissionMixin,
    UpdateView,
):
    model = PlantillaInformeTecnicoVersion
    form_class = PlantillaInformeTecnicoVersionForm
    template_name = "admisiones/templates_informes_tecnicos/version_form.html"
    context_object_name = "version"
    pk_url_kwarg = "version_pk"

    def get_queryset(self):
        return PlantillaInformeTecnicoVersion.objects.select_related(
            "plantilla"
        ).filter(
            plantilla_id=self.kwargs["plantilla_pk"],
            estado="borrador",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["variables_template"] = VariableTemplateInformeTecnico.objects.filter(
            activo=True
        ).order_by("categoria", "orden", "nombre", "codigo")
        return context

    def form_valid(self, form):
        success, mensaje = PlantillaInformeTecnicoService.guardar_borrador(
            self.get_object(),
            form.cleaned_data,
            self.request.user,
        )
        if not success:
            form.add_error(None, mensaje)
            return self.form_invalid(form)
        messages.success(self.request, mensaje)
        return redirect("gestor_templates_detalle", pk=self.kwargs["plantilla_pk"])


class VariableTemplateInformeTecnicoListView(GestorTemplatesPermissionMixin, ListView):
    template_name = "admisiones/templates_informes_tecnicos/variables_list.html"
    context_object_name = "variables"
    paginate_by = 100

    def get_queryset(self):
        estado = (self.request.GET.get("estado") or "activas").strip().lower()
        queryset = VariableTemplateInformeTecnico.objects.all()
        if estado == "activas":
            queryset = queryset.filter(activo=True)
        elif estado == "inactivas":
            queryset = queryset.filter(activo=False)

        busqueda = (self.request.GET.get("q") or "").strip()
        if busqueda:
            queryset = queryset.filter(
                Q(nombre__icontains=busqueda)
                | Q(codigo__icontains=busqueda)
                | Q(categoria__icontains=busqueda)
                | Q(descripcion__icontains=busqueda)
            )
        return queryset.order_by("categoria", "orden", "nombre", "codigo")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["estado_filtro"] = (self.request.GET.get("estado") or "activas").strip()
        context["busqueda"] = (self.request.GET.get("q") or "").strip()
        return context


class VariableTemplateInformeTecnicoToggleView(GestorTemplatesPermissionMixin, View):
    def post(self, request, pk):
        variable = get_object_or_404(VariableTemplateInformeTecnico, pk=pk)
        variable.activo = not variable.activo
        variable.save(update_fields=["activo", "modificado"])
        estado = "activada" if variable.activo else "inactivada"
        messages.success(request, f"Variable {estado} correctamente.")
        return redirect(request.POST.get("next") or "gestor_templates_variables_listar")


class PlantillaInformeTecnicoVersionPreviewView(GestorTemplatesPermissionMixin, View):
    """Permite probar incluso un borrador con datos de un informe existente."""

    def get(self, request, plantilla_pk, version_pk):
        informe_id = request.GET.get("informe_id")
        if not informe_id:
            messages.error(
                request, "Indique el ID del Informe Técnico para la vista previa."
            )
            return redirect(
                "gestor_templates_version_editar",
                plantilla_pk=plantilla_pk,
                version_pk=version_pk,
            )
        version = get_object_or_404(
            PlantillaInformeTecnicoVersion.objects.select_related("plantilla"),
            pk=version_pk,
            plantilla_id=plantilla_pk,
        )
        informe = get_object_or_404(
            InformeTecnico.objects.select_related("admision", "admision__comedor"),
            pk=informe_id,
        )
        docx_content = InformeService.generar_docx_vista_previa(informe, version)
        if not docx_content:
            messages.error(request, "No se pudo generar la vista previa del template.")
            return redirect(
                "gestor_templates_version_editar",
                plantilla_pk=plantilla_pk,
                version_pk=version_pk,
            )
        return FileResponse(
            docx_content,
            as_attachment=True,
            filename=f"vista-previa-{version.plantilla.codigo}-v{version.numero}.docx",
            content_type=(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ),
        )


class PlantillaInformeTecnicoVersionPublishView(GestorTemplatesPermissionMixin, View):
    def post(self, request, plantilla_pk, version_pk):
        version = PlantillaInformeTecnicoVersion.objects.filter(
            pk=version_pk,
            plantilla_id=plantilla_pk,
        ).first()
        if version is None:
            messages.error(request, "No se encontró la versión solicitada.")
        else:
            success, mensaje = PlantillaInformeTecnicoService.publicar_version(
                version,
                request.user,
            )
            getattr(messages, "success" if success else "error")(request, mensaje)
        return redirect("gestor_templates_detalle", pk=plantilla_pk)


class PlantillaInformeTecnicoDeactivateView(GestorTemplatesPermissionMixin, View):
    def post(self, request, pk):
        plantilla = PlantillaInformeTecnico.objects.filter(pk=pk).first()
        if plantilla is None:
            messages.error(request, "No se encontró el template solicitado.")
            return redirect("gestor_templates_listar")
        success, mensaje = PlantillaInformeTecnicoService.inactivar_plantilla(
            plantilla,
            request.user,
        )
        getattr(messages, "success" if success else "error")(request, mensaje)
        return redirect("gestor_templates_detalle", pk=plantilla.pk)


class IncidenciaTemplateInformeTecnicoListView(
    GestorTemplatesPermissionMixin, ListView
):
    template_name = "admisiones/templates_informes_tecnicos/incidencias_list.html"
    context_object_name = "incidencias"
    paginate_by = 50

    def get_queryset(self):
        estado = (self.request.GET.get("estado") or "pendiente").strip().lower()
        queryset = IncidenciaTemplateInformeTecnico.objects.select_related(
            "plantilla",
            "incidencia_anterior",
        )
        if estado in {choice[0] for choice in IncidenciaTemplateInformeTecnico.ESTADOS}:
            queryset = queryset.filter(estado=estado)
        busqueda = (self.request.GET.get("q") or "").strip()
        if busqueda:
            queryset = queryset.filter(
                Q(codigo__icontains=busqueda)
                | Q(clave_condiciones__icontains=busqueda)
                | Q(casos__comedor_nombre__icontains=busqueda)
                | Q(casos__organizacion_nombre__icontains=busqueda)
            ).distinct()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["estado_filtro"] = (
            self.request.GET.get("estado") or "pendiente"
        ).strip()
        context["busqueda"] = (self.request.GET.get("q") or "").strip()
        context["estados"] = IncidenciaTemplateInformeTecnico.ESTADOS
        return context


class IncidenciaTemplateInformeTecnicoDetailView(
    GestorTemplatesPermissionMixin,
    DetailView,
):
    model = IncidenciaTemplateInformeTecnico
    template_name = "admisiones/templates_informes_tecnicos/incidencia_detail.html"
    context_object_name = "incidencia"

    def get_queryset(self):
        return IncidenciaTemplateInformeTecnico.objects.select_related(
            "plantilla",
            "incidencia_anterior",
        ).prefetch_related(
            "casos__admision__comedor",
            "casos__informe",
            "casos__reportado_por",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = kwargs.get("form") or IncidenciaTemplateInformeTecnicoForm(
            instance=self.object
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = IncidenciaTemplateInformeTecnicoForm(request.POST, instance=self.object)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        exito, mensaje = PlantillaInformeTecnicoService.gestionar_incidencia(
            self.object,
            form.cleaned_data,
            request.user,
        )
        if exito:
            messages.success(request, mensaje)
            return redirect("gestor_templates_incidencia_detalle", pk=self.object.pk)
        form.add_error(None, mensaje)
        return self.render_to_response(self.get_context_data(form=form))
