import json
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.http import FileResponse, JsonResponse
from django.urls import reverse, reverse_lazy
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
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
from core.services.column_preferences import build_columns_context_from_fields
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
    COLUMN_LIST_KEY = "rendiciones_global_list"
    COLUMN_DEFINITIONS = (
        ("proyecto", "Proyecto", "comedor.codigo_de_proyecto"),
        ("organizacion", "Organización", "comedor.organizacion.nombre"),
        ("convenio", "Convenio", "convenio"),
        ("numero_rendicion", "Rendición", "numero_rendicion"),
        ("periodo", "Período", "periodo_exportacion"),
        ("etapa", "Etapa", "get_etapa_proceso_display"),
        ("estado", "Estado", "estado_proceso_display"),
        ("ultima_modificacion", "Última modificación", "ultima_modificacion"),
    )

    def _get_columns_context(self):
        return build_columns_context_from_fields(
            self.request,
            self.COLUMN_LIST_KEY,
            [{"title": title} for _key, title, _field in self.COLUMN_DEFINITIONS],
            [{"name": key} for key, _title, _field in self.COLUMN_DEFINITIONS],
            required_keys=["proyecto"],
        )

    def get_export_columns(self):
        active_keys = self._get_columns_context()["column_active_keys"]
        definitions = {
            key: (title, field) for key, title, field in self.COLUMN_DEFINITIONS
        }
        return [definitions[key] for key in active_keys]

    def resolve_field(self, obj, field_path):
        if field_path == "periodo_exportacion":
            if obj.periodo_inicio and obj.periodo_fin:
                return f"{obj.periodo_inicio:%d/%m/%Y} - {obj.periodo_fin:%d/%m/%Y}"
            return f"{obj.mes}/{obj.anio}"
        return super().resolve_field(obj, field_path)

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
        queryset = engine.filter_queryset(queryset, self.request.GET)
        return self._filter_estado_proceso(queryset)

    def _filter_estado_proceso(self, queryset):
        """Filtra por el valor compuesto que se muestra en la columna Estado."""
        try:
            payload = json.loads(self.request.GET.get("filters") or "{}")
        except (TypeError, json.JSONDecodeError):
            return queryset

        estado_q = Q()
        tiene_estado_valido = False
        for item in payload.get("items", []):
            if (
                not isinstance(item, dict)
                or item.get("field") != "estado_proceso"
                or item.get("op") not in {"eq", "ne"}
            ):
                continue
            estado = str(item.get("value"))
            try:
                etapa, subestado = estado.split(":", 1)
            except ValueError:
                continue
            etapas_validas = dict(RendicionCuentaMensual.ETAPA_PROCESO_CHOICES)
            subestados_validos = dict(RendicionCuentaMensual.SUBESTADO_PROCESO_CHOICES)
            if etapa not in etapas_validas or subestado not in subestados_validos:
                continue
            item_q = Q(etapa_proceso=etapa, subestado_proceso=subestado)
            estado_q |= ~item_q if item["op"] == "ne" else item_q
            tiene_estado_valido = True

        return queryset.filter(estado_q) if tiene_estado_valido else queryset

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
        context.update(self._get_columns_context())
        context["active_columns"] = context["column_active_keys"]
        context["breadcrumb_items"] = [
            {"text": "Organizaciones", "url": reverse_lazy("organizaciones")},
            {"text": "Rendiciones", "active": True},
        ]
        return context


class RendicionCuentaMensualDetailView(LoginRequiredMixin, DetailView):
    model = RendicionCuentaMensual
    template_name = "rendicioncuentasmensual_detail.html"
    context_object_name = "rendicion_cuenta_mensual"
    PERMISSION_TERRITORIAL = "rendicioncuentasmensual.manage_territorial_stage"
    PERMISSION_REVISION_AUDITORIA = (
        "rendicioncuentasmensual.manage_auditoria_review_stage"
    )
    PERMISSION_AUDITORIA = "rendicioncuentasmensual.manage_auditoria_stage"
    PERMISSION_REGULARIZACION = "rendicioncuentasmensual.manage_regularizacion_stage"

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
        puede_territorial = cls._user_can_territorial(user)
        puede_revision_auditoria = cls._user_can_revision_auditoria(user)
        if not puede_territorial and not puede_revision_auditoria:
            return False
        if rendicion is None:
            return True
        if rendicion.subestado_proceso != RendicionCuentaMensual.SUBESTADO_EN_CURSO:
            return False
        if (
            rendicion.etapa_proceso
            == RendicionCuentaMensual.ETAPA_REVISION_DOCUMENTACION
        ):
            return puede_territorial
        if rendicion.etapa_proceso == RendicionCuentaMensual.ETAPA_REVISION_AUDITORIA:
            return puede_revision_auditoria
        return False

    @classmethod
    def _user_can_territorial(cls, user):
        return user_has_permission_code(user, cls.PERMISSION_TERRITORIAL)

    @classmethod
    def _user_can_revision_auditoria(cls, user):
        return user_has_permission_code(user, cls.PERMISSION_REVISION_AUDITORIA)

    @classmethod
    def _user_can_auditoria(cls, user):
        return user_has_permission_code(user, cls.PERMISSION_AUDITORIA)

    @classmethod
    def _user_can_regularizacion(cls, user):
        return user_has_permission_code(user, cls.PERMISSION_REGULARIZACION)

    @classmethod
    def _permission_for_action(cls, accion):
        action_permissions = {
            RendicionProcesoService.ACCION_INICIAR_TERRITORIAL: cls.PERMISSION_TERRITORIAL,
            RendicionProcesoService.ACCION_FINALIZAR_TERRITORIAL: cls.PERMISSION_TERRITORIAL,
            RendicionProcesoService.ACCION_INICIAR_REVISION_AUDITORIA: cls.PERMISSION_REVISION_AUDITORIA,
            RendicionProcesoService.ACCION_FINALIZAR_REVISION_AUDITORIA: cls.PERMISSION_REVISION_AUDITORIA,
            RendicionProcesoService.ACCION_INICIAR_AUDITORIA: cls.PERMISSION_AUDITORIA,
            RendicionProcesoService.ACCION_FINALIZAR_SIN_OBSERVACIONES: cls.PERMISSION_AUDITORIA,
            RendicionProcesoService.ACCION_FINALIZAR_CON_OBSERVACIONES: cls.PERMISSION_AUDITORIA,
            RendicionProcesoService.ACCION_INICIAR_REGULARIZACION: cls.PERMISSION_REGULARIZACION,
            RendicionProcesoService.ACCION_FINALIZAR_REGULARIZACION: cls.PERMISSION_REGULARIZACION,
        }
        return action_permissions.get(accion)

    @classmethod
    def _user_can_run_action(cls, user, accion):
        return user_has_permission_code(
            user,
            cls._permission_for_action(accion),
        )

    def post(  # pylint: disable=too-many-return-statements,too-many-branches,too-many-locals
        self, request, *args, **kwargs
    ):
        rendicion = self.get_object()
        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
        solicitar_categoria = (request.POST.get("solicitar_categoria") or "").strip()
        if solicitar_categoria:
            puede_solicitar = (
                rendicion.subestado_proceso == RendicionCuentaMensual.SUBESTADO_EN_CURSO
                and (
                    (
                        rendicion.etapa_proceso
                        == RendicionCuentaMensual.ETAPA_REVISION_DOCUMENTACION
                        and self._user_can_territorial(request.user)
                    )
                    or (
                        rendicion.etapa_proceso
                        == RendicionCuentaMensual.ETAPA_REVISION_AUDITORIA
                        and self._user_can_revision_auditoria(request.user)
                    )
                )
            )
            if not puede_solicitar:
                raise PermissionDenied
            try:
                solicitud = RendicionCuentaMensualService.solicitar_documento_faltante(
                    rendicion=rendicion,
                    categoria=solicitar_categoria,
                    observaciones=request.POST.get("observaciones_faltante"),
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
                    return JsonResponse(
                        {
                            "success": True,
                            "message": "Solicitud de documento faltante registrada.",
                            "solicitud": {
                                "categoria": solicitud.categoria,
                                "observaciones": solicitud.observaciones,
                            },
                        }
                    )
                messages.success(request, "Solicitud de documento faltante registrada.")
            return HttpResponseRedirect(
                reverse("rendicioncuentasmensual_detail", kwargs={"pk": rendicion.pk})
            )
        accion_proceso = (request.POST.get("accion_proceso") or "").strip()
        if accion_proceso:
            if not self._user_can_run_action(request.user, accion_proceso):
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
        context["puede_solicitar_faltantes"] = (
            rendicion.subestado_proceso == RendicionCuentaMensual.SUBESTADO_EN_CURSO
            and (
                (
                    rendicion.etapa_proceso
                    == RendicionCuentaMensual.ETAPA_REVISION_DOCUMENTACION
                    and self._user_can_territorial(self.request.user)
                )
                or (
                    rendicion.etapa_proceso
                    == RendicionCuentaMensual.ETAPA_REVISION_AUDITORIA
                    and self._user_can_revision_auditoria(self.request.user)
                )
            )
        )
        context["puede_revision_territorial"] = self._user_can_territorial(
            self.request.user
        )
        context["puede_revision_auditoria"] = self._user_can_revision_auditoria(
            self.request.user
        )
        context["puede_auditoria"] = self._user_can_auditoria(self.request.user)
        context["puede_regularizacion"] = self._user_can_regularizacion(
            self.request.user
        )
        context["puede_editar_datos"] = user_has_permission_code(
            self.request.user, "rendicioncuentasmensual.edit_rendicion_data"
        )
        context["proceso_form"] = RendicionProcesoForm()
        return context


class RendicionCuentaMensualDownloadPdfView(LoginRequiredMixin, DetailView):
    model = RendicionCuentaMensual
    MESES_ARCHIVO = (
        "",
        "ENE",
        "FEB",
        "MAR",
        "ABR",
        "MAY",
        "JUN",
        "JUL",
        "AGO",
        "SEP",
        "OCT",
        "NOV",
        "DIC",
    )

    @staticmethod
    def _normalizar_parte_nombre(value, fallback):
        value = str(value or "").strip()
        normalizado = re.sub(r"[^A-Za-z0-9.]+", "_", value).strip("_.")
        return normalizado or fallback

    @classmethod
    def construir_nombre_archivo(cls, rendicion):
        if not hasattr(rendicion, "periodo_inicio") and not hasattr(rendicion, "anio"):
            return f"rendicion-{rendicion.numero_rendicion or rendicion.id}.pdf"

        proyecto = getattr(
            getattr(rendicion, "proyecto", None), "codigo", ""
        ) or getattr(getattr(rendicion, "comedor", None), "codigo_de_proyecto", "")
        proyecto = cls._normalizar_parte_nombre(proyecto, "SIN_PROYECTO")
        convenio = cls._normalizar_parte_nombre(
            getattr(rendicion, "convenio", None), "SIN_CONVENIO"
        )
        numero = rendicion.numero_rendicion or rendicion.id
        periodo_inicio = getattr(rendicion, "periodo_inicio", None)
        mes = periodo_inicio.month if periodo_inicio else getattr(rendicion, "mes", 0)
        anio = (
            periodo_inicio.year
            if periodo_inicio
            else getattr(rendicion, "anio", "SIN-ANIO")
        )
        mes_archivo = cls.MESES_ARCHIVO[mes] if mes in range(1, 13) else "MES"
        return f"{proyecto}-{convenio}-RENDICION_{numero}-{mes_archivo}{anio}.pdf"

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

        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=self.construir_nombre_archivo(rendicion),
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
    template_name = "rendicioncuentasmensual_datos_form.html"
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
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "rendicioncuentasmensual_detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = context.get("form") or RendicionDatosForm(
            instance=self.object
        )
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
