from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.http import FileResponse, JsonResponse
from django.urls import reverse, reverse_lazy
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponseRedirect
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from comedores.models import Comedor
from core.services.advanced_filters import AdvancedFilterEngine
from core.services.favorite_filters import SeccionesFiltrosFavoritos
from core.mixins import CSVExportMixin
from core.soft_delete.preview import build_delete_preview
from core.soft_delete.view_helpers import (
    SoftDeleteDeleteViewMixin,
    is_soft_deletable_instance,
)
from iam.services import user_has_permission_code
from rendicioncuentasmensual.models import RendicionCuentaMensual, DocumentacionAdjunta
from rendicioncuentasmensual.services import RendicionCuentaMensualService
from rendicioncuentasmensual.services import RendicionProcesoService
from rendicioncuentasmensual.forms import (
    RendicionCuentaMensualForm,
    DocumentacionAdjuntaForm,
    RendicionProcesoForm,
    RendicionDatosForm,
)
from rendicioncuentasmensual.filter_config import (
    BOOL_OPS,
    CHOICE_OPS,
    DATE_OPS,
    FIELD_MAP,
    FIELD_TYPES,
    NUM_OPS,
    TEXT_OPS,
    get_filters_ui_config,
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


class RendicionCuentaMensualGlobalListView(
    LoginRequiredMixin, CSVExportMixin, ListView
):
    model = RendicionCuentaMensual
    template_name = "rendicioncuentasmensual_global_list.html"
    context_object_name = "rendiciones_cuentas_mensuales"
    paginate_by = 25
    export_filename = "listado_rendiciones.csv"

    def get_export_columns(self):
        return [
            ("Proyecto", "comedor.codigo_de_proyecto"),
            ("Organización", "comedor.organizacion.nombre"),
            ("Convenio", "convenio"),
            ("Rendición", "numero_rendicion"),
            ("Período inicio", "periodo_inicio"),
            ("Período fin", "periodo_fin"),
            ("Estado", "get_estado_display"),
            ("Etapa", "get_etapa_proceso_display"),
        ]

    def get(self, request, *args, **kwargs):
        if request.GET.get("export") == "csv":
            return self.export_csv(self.get_queryset())
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """Retorna todas las rendiciones activas para el listado global."""
        queryset = (
            RendicionCuentaMensualService.obtener_todas_rendiciones_cuentas_mensuales()
        )
        engine = AdvancedFilterEngine(
            field_map=FIELD_MAP,
            field_types=FIELD_TYPES,
            allowed_ops={
                "text": TEXT_OPS,
                "number": NUM_OPS,
                "date": DATE_OPS,
                "choice": CHOICE_OPS,
                "boolean": BOOL_OPS,
            },
        )
        return engine.filter_queryset(queryset, self.request.GET)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo_listado"] = "Rendiciones"
        context["reset_url"] = "rendicioncuentasmensual_global_list"
        context["filters_mode"] = True
        context["filters_action"] = reverse("rendicioncuentasmensual_global_list")
        request_export_url = (
            self.request.get_full_path()
            if hasattr(self.request, "get_full_path")
            else reverse("rendicioncuentasmensual_global_list")
        )
        separator = "&" if "?" in request_export_url else "?"
        context["export_url"] = f"{request_export_url}{separator}export=csv"
        context["filters_config"] = get_filters_ui_config()
        context["filters_js"] = "custom/js/advanced_filters.js"
        context["seccion_filtros_favoritos"] = SeccionesFiltrosFavoritos.RENDICIONES
        context["columnas_configurables"] = [
            ("proyecto", "Proyecto"),
            ("convenio", "Convenio"),
            ("etapa", "Etapa"),
            ("estado", "Estado"),
        ]
        context["breadcrumb_items"] = [
            {"text": "Organizaciones", "url": reverse_lazy("organizaciones")},
            {"text": "Rendiciones", "active": True},
        ]
        return context


class RendicionCuentaMensualDetailView(LoginRequiredMixin, DetailView):
    model = RendicionCuentaMensual
    template_name = "rendicioncuentasmensual_detail.html"
    context_object_name = "rendicion_cuenta_mensual"
    REVIEW_PERMISSION_CODE = "rendicioncuentasmensual.change_rendicioncuentamensual"
    GRUPO_TERRITORIAL = "Rendición Territorial"
    GRUPO_AUDITORIA = "Rendición Auditoría"
    GRUPO_ADMIN_AUDITORIA = "Administrador Auditoría"

    @staticmethod
    def format_validation_error(error):
        if hasattr(error, "message_dict"):
            messages_list = []
            for value in error.message_dict.values():
                if isinstance(value, (list, tuple)):
                    messages_list.extend(str(item) for item in value)
                else:
                    messages_list.append(str(value))
            return " ".join(messages_list)
        if hasattr(error, "messages"):
            return " ".join(str(item) for item in error.messages)
        return str(error)

    @classmethod
    def _user_can_review_documentos(cls, user, rendicion=None):
        if not user_has_permission_code(user, cls.REVIEW_PERMISSION_CODE):
            return False
        if rendicion is None:
            return True
        if rendicion.subestado_proceso != RendicionCuentaMensual.SUBESTADO_EN_CURSO:
            return False
        if (
            rendicion.etapa_proceso
            == RendicionCuentaMensual.ETAPA_REVISION_DOCUMENTACION
        ):
            return cls._user_can_territorial(user)
        if rendicion.etapa_proceso == RendicionCuentaMensual.ETAPA_REVISION_AUDITORIA:
            return cls._user_can_auditoria(user)
        return False

    @classmethod
    def _user_can_territorial(cls, user):
        return (
            getattr(user, "is_superuser", False)
            or getattr(user, "groups", None)
            and user.groups.filter(
                name__in=[cls.GRUPO_TERRITORIAL, cls.GRUPO_ADMIN_AUDITORIA]
            ).exists()
        )

    @classmethod
    def _user_can_auditoria(cls, user):
        return (
            getattr(user, "is_superuser", False)
            or getattr(user, "groups", None)
            and user.groups.filter(
                name__in=[cls.GRUPO_AUDITORIA, cls.GRUPO_ADMIN_AUDITORIA]
            ).exists()
        )

    def post(  # pylint: disable=too-many-return-statements,too-many-branches,too-many-locals
        self, request, *args, **kwargs
    ):
        rendicion = self.get_object()
        solicitar_categoria = (request.POST.get("solicitar_categoria") or "").strip()
        if solicitar_categoria:
            puede_solicitar = user_has_permission_code(
                request.user, self.REVIEW_PERMISSION_CODE
            ) and (
                (
                    rendicion.etapa_proceso
                    == RendicionCuentaMensual.ETAPA_REVISION_DOCUMENTACION
                    and self._user_can_territorial(request.user)
                )
                or (
                    rendicion.etapa_proceso
                    == RendicionCuentaMensual.ETAPA_REVISION_AUDITORIA
                    and self._user_can_auditoria(request.user)
                )
            )
            if not puede_solicitar:
                raise PermissionDenied
            try:
                RendicionCuentaMensualService.solicitar_documento_faltante(
                    rendicion=rendicion,
                    categoria=solicitar_categoria,
                    observaciones=request.POST.get("observaciones_faltante"),
                    actor=request.user,
                )
            except ValidationError as exc:
                messages.error(request, self.format_validation_error(exc))
            else:
                messages.success(request, "Solicitud de documento faltante registrada.")
            return HttpResponseRedirect(
                reverse("rendicioncuentasmensual_detail", kwargs={"pk": rendicion.pk})
            )
        accion_proceso = (request.POST.get("accion_proceso") or "").strip()
        if accion_proceso:
            acciones_territoriales = {
                RendicionProcesoService.ACCION_INICIAR_TERRITORIAL,
                RendicionProcesoService.ACCION_FINALIZAR_TERRITORIAL,
            }
            permitido = (
                self._user_can_territorial(request.user)
                if accion_proceso in acciones_territoriales
                else self._user_can_auditoria(request.user)
            )
            if not permitido:
                raise PermissionDenied
            form = RendicionProcesoForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    RendicionProcesoService.ejecutar(
                        rendicion=rendicion,
                        accion=accion_proceso,
                        datos=form.cleaned_data,
                        actor=request.user,
                    )
                except ValidationError as exc:
                    messages.error(request, self.format_validation_error(exc))
                else:
                    messages.success(request, "Estado de la rendición actualizado.")
            else:
                messages.error(
                    request,
                    " ".join(
                        error for errores in form.errors.values() for error in errores
                    ),
                )
            return HttpResponseRedirect(
                reverse("rendicioncuentasmensual_detail", kwargs={"pk": rendicion.pk})
            )

        documento_id = request.POST.get("documento_id")
        estado = (request.POST.get("estado") or "").strip()
        observaciones = request.POST.get("observaciones")
        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
        if not self._user_can_review_documentos(request.user, rendicion):
            if is_ajax:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "No tiene permisos para revisar documentos.",
                    },
                    status=403,
                )
            raise PermissionDenied

        documento = rendicion.archivos_adjuntos.filter(
            id=documento_id,
            deleted_at__isnull=True,
        ).first()
        if not documento:
            if is_ajax:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "El documento seleccionado no existe.",
                    },
                    status=404,
                )
            messages.error(request, "El documento seleccionado no existe.")
            return HttpResponseRedirect(
                reverse("rendicioncuentasmensual_detail", kwargs={"pk": rendicion.pk})
            )

        try:
            RendicionCuentaMensualService.actualizar_estado_documento_revision(
                documento=documento,
                estado=estado,
                observaciones=observaciones,
                actor=request.user,
            )
        except ValidationError as exc:
            if is_ajax:
                return JsonResponse(
                    {
                        "success": False,
                        "message": self.format_validation_error(exc),
                    },
                    status=400,
                )
            messages.error(request, self.format_validation_error(exc))
        else:
            if is_ajax:
                documento.refresh_from_db()
                rendicion.refresh_from_db()
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Estado del documento actualizado correctamente.",
                        "documento": {
                            "id": documento.id,
                            "estado": documento.estado,
                            "estado_display": documento.get_estado_display(),
                            "estado_visual": documento.get_estado_visual(),
                            "estado_visual_display": documento.get_estado_visual_display(),
                            "observaciones": documento.observaciones or "",
                        },
                        "rendicion": {
                            "estado": rendicion.estado,
                            "estado_display": rendicion.get_estado_display(),
                            "puede_descargar_pdf": (
                                RendicionCuentaMensualService.rendicion_esta_completamente_validada(
                                    rendicion
                                )
                            ),
                            "download_url": (
                                reverse(
                                    "rendicioncuentasmensual_detail",
                                    kwargs={"pk": rendicion.pk},
                                )
                                + "descargar-pdf/"
                            ),
                        },
                    }
                )
            messages.success(request, "Estado del documento actualizado correctamente.")

        return HttpResponseRedirect(
            reverse("rendicioncuentasmensual_detail", kwargs={"pk": rendicion.pk})
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rendicion = RendicionCuentaMensualService.obtener_rendicion_cuenta_mensual(
            self.kwargs.get("pk")
        )
        context["rendicion"] = rendicion
        context["documentacion_por_categoria"] = (
            RendicionCuentaMensualService.obtener_documentacion_para_detalle(rendicion)
        )
        context["scope_proyecto"] = (
            RendicionCuentaMensualService.obtener_scope_proyecto(rendicion)
        )
        context["puede_descargar_pdf"] = (
            RendicionCuentaMensualService.rendicion_esta_completamente_validada(
                rendicion
            )
        )
        context["puede_revisar_documentos"] = self._user_can_review_documentos(
            self.request.user, rendicion
        )
        context["puede_solicitar_faltantes"] = user_has_permission_code(
            self.request.user, self.REVIEW_PERMISSION_CODE
        ) and (
            (
                rendicion.etapa_proceso
                == RendicionCuentaMensual.ETAPA_REVISION_DOCUMENTACION
                and self._user_can_territorial(self.request.user)
            )
            or (
                rendicion.etapa_proceso
                == RendicionCuentaMensual.ETAPA_REVISION_AUDITORIA
                and self._user_can_auditoria(self.request.user)
            )
        )
        context["puede_revision_territorial"] = self._user_can_territorial(
            self.request.user
        )
        context["puede_revision_auditoria"] = self._user_can_auditoria(
            self.request.user
        )
        context["puede_editar_datos"] = user_has_permission_code(
            self.request.user, "rendicioncuentasmensual.edit_rendicion_data"
        )
        context["proceso_form"] = RendicionProcesoForm()
        return context


class RendicionCuentaMensualDownloadPdfView(LoginRequiredMixin, DetailView):
    model = RendicionCuentaMensual

    def get(self, request, *args, **kwargs):
        rendicion = RendicionCuentaMensualService.obtener_rendicion_cuenta_mensual(
            self.kwargs.get("pk")
        )
        try:
            pdf_buffer = RendicionCuentaMensualService.generar_pdf_descarga_rendicion(
                rendicion
            )
        except ValidationError as exc:
            messages.error(
                request,
                RendicionCuentaMensualDetailView.format_validation_error(exc),
            )
            return HttpResponseRedirect(
                reverse("rendicioncuentasmensual_detail", kwargs={"pk": rendicion.pk})
            )

        proyecto = (
            getattr(getattr(rendicion, "proyecto", None), "codigo", "")
            or getattr(getattr(rendicion, "comedor", None), "codigo_de_proyecto", "")
            or "sin-proyecto"
        )
        periodo_inicio = getattr(rendicion, "periodo_inicio", None)
        anio = getattr(rendicion, "anio", "sin-anio")
        mes = getattr(rendicion, "mes", 0)
        periodo = (
            periodo_inicio.strftime("%Y-%m") if periodo_inicio else f"{anio}-{mes:02d}"
        )
        if not hasattr(rendicion, "periodo_inicio") and not hasattr(rendicion, "anio"):
            filename = f"rendicion-{rendicion.numero_rendicion or rendicion.id}.pdf"
        else:
            convenio = getattr(rendicion, "convenio", None) or "sin-convenio"
            numero = rendicion.numero_rendicion or rendicion.id
            filename = f"{proyecto}_{convenio}_rendicion-{numero}_{periodo}.pdf"
        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=filename,
            content_type="application/pdf",
        )


class RendicionCuentaMensualCreateView(LoginRequiredMixin, CreateView):
    model = RendicionCuentaMensual
    template_name = "rendicioncuentasmensual_form.html"
    form_class = RendicionCuentaMensualForm

    def form_valid(self, form):
        comedor_id = self.kwargs.get("comedor_id")
        comedor = Comedor.objects.get(id=comedor_id)

        rendicion = form.save(commit=False)
        rendicion.comedor = comedor
        if self.request.user.is_authenticated:
            rendicion.usuario_creador = self.request.user
            rendicion.usuario_ultima_modificacion = self.request.user
        rendicion.save()

        archivos = self.request.FILES.getlist("archivo")
        for archivo_enviado in archivos:
            doc_adjunta = DocumentacionAdjunta.objects.create(
                nombre=archivo_enviado.name,
                archivo=archivo_enviado,
            )
            rendicion.archivos_adjuntos.add(doc_adjunta)

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
    form_class = RendicionDatosForm

    def dispatch(self, request, *args, **kwargs):
        if not user_has_permission_code(
            request.user, "rendicioncuentasmensual.edit_rendicion_data"
        ):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        rendicion = self.get_object()
        form.instance.comedor = rendicion.comedor
        form.instance.usuario_creador = rendicion.usuario_creador
        if self.request.user.is_authenticated:
            form.instance.usuario_ultima_modificacion = self.request.user
        form.instance.ultima_modificacion = rendicion.ultima_modificacion
        form.instance.fecha_creacion = rendicion.fecha_creacion
        form.instance.mes = form.cleaned_data["periodo_inicio"].month
        form.instance.anio = form.cleaned_data["periodo_inicio"].year
        form.save()

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "rendicioncuentasmensual_detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor_id = self.object.comedor.id
        context["comedorid"] = comedor_id
        context["form"] = RendicionDatosForm(instance=self.object)
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
