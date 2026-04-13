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
from core.soft_delete.preview import build_delete_preview
from core.soft_delete.view_helpers import (
    SoftDeleteDeleteViewMixin,
    is_soft_deletable_instance,
)
from iam.services import user_has_permission_code
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


class RendicionCuentaMensualGlobalListView(LoginRequiredMixin, ListView):
    model = RendicionCuentaMensual
    template_name = "rendicioncuentasmensual_global_list.html"
    context_object_name = "rendiciones_cuentas_mensuales"
    paginate_by = 25

    def get_queryset(self):
        """Retorna todas las rendiciones activas para el listado global."""
        return (
            RendicionCuentaMensualService.obtener_todas_rendiciones_cuentas_mensuales()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo_listado"] = "Rendiciones"
        context["breadcrumb_items"] = [
            {"text": "Comedores", "url": reverse_lazy("comedores")},
            {"text": "Rendiciones", "active": True},
        ]
        return context


class RendicionCuentaMensualDetailView(LoginRequiredMixin, DetailView):
    model = RendicionCuentaMensual
    template_name = "rendicioncuentasmensual_detail.html"
    context_object_name = "rendicion_cuenta_mensual"
    REVIEW_PERMISSION_CODE = "rendicioncuentasmensual.change_rendicioncuentamensual"

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
    def _user_can_review_documentos(cls, user):
        return user_has_permission_code(user, cls.REVIEW_PERMISSION_CODE)

    def post(self, request, *args, **kwargs):
        rendicion = self.get_object()
        documento_id = request.POST.get("documento_id")
        estado = (request.POST.get("estado") or "").strip()
        observaciones = request.POST.get("observaciones")
        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
        if not self._user_can_review_documentos(request.user):
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
            self.request.user
        )
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

        filename = f"rendicion-{rendicion.numero_rendicion or rendicion.id}.pdf"
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
    form_class = RendicionCuentaMensualForm

    def form_valid(self, form):
        rendicion = self.get_object()
        form.instance.comedor = rendicion.comedor
        form.instance.usuario_creador = rendicion.usuario_creador
        if self.request.user.is_authenticated:
            form.instance.usuario_ultima_modificacion = self.request.user
        form.instance.ultima_modificacion = rendicion.ultima_modificacion
        form.instance.fecha_creacion = rendicion.fecha_creacion
        rendicion = form.save()

        archivos = self.request.FILES.getlist("archivo")
        for archivo in archivos:
            doc_adjunta = DocumentacionAdjunta.objects.create(
                nombre=archivo.name,
                archivo=archivo,
            )
            rendicion.archivos_adjuntos.add(doc_adjunta)

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
        context["archivos_adjuntos"] = self.object.archivos_adjuntos.all()
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
