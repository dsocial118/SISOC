import logging
import os
from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.conf import settings
from django.db.models.base import Model
from django.forms import BaseModelForm, ValidationError
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    TemplateView,
)

from admisiones.models.admisiones import Admision, EstadoAdmision
from comedores.forms.comedor_form import (
    ComedorForm,
    ReferenteForm,
    NominaForm,
    CiudadanoFormParaNomina,
    NominaExtraForm,
)
from comedores.forms.observacion_form import ObservacionForm
from comedores.models import (
    Comedor,
    ImagenComedor,
    Observacion,
    Nomina,
)
from comedores.services.comedor_service import ComedorService
from comedores.services.filter_config import get_filters_ui_config
from duplas.dupla_service import DuplaService
from relevamientos.service import RelevamientoService
from ciudadanos.models import EstadoIntervencion

logger = logging.getLogger("django")


@login_required
@require_POST
def relevamiento_crear_editar_ajax(request, pk):
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    response = None
    try:
        if "territorial" in request.POST:
            relevamiento = RelevamientoService.create_pendiente(request, pk)
            if is_ajax:
                url = reverse(
                    "relevamiento_detalle",
                    kwargs={
                        "pk": relevamiento.pk,
                        "comedor_pk": relevamiento.comedor.pk,
                    },
                )
                response = JsonResponse({"url": url}, status=200)
            else:
                messages.success(
                    request, "Relevamiento territorial creado correctamente."
                )
                response = redirect(
                    "relevamiento_detalle",
                    pk=relevamiento.pk,
                    comedor_pk=relevamiento.comedor.pk,
                )
        elif "territorial_editar" in request.POST:
            relevamiento = RelevamientoService.update_territorial(request)
            if is_ajax:
                response = JsonResponse(
                    {
                        "url": f"/comedores/{relevamiento.comedor.pk}/relevamiento/{relevamiento.pk}"
                    },
                    status=200,
                )
            else:
                messages.success(
                    request, "Relevamiento territorial actualizado correctamente."
                )
                response = redirect(
                    "relevamiento_detalle",
                    pk=relevamiento.pk,
                    comedor_pk=relevamiento.comedor.pk,
                )
        else:
            if is_ajax:
                response = JsonResponse({"error": "Acción no reconocida"}, status=400)
            else:
                messages.error(request, "Acción no reconocida.")
                response = redirect("comedor_detalle", pk=pk)
    except ValidationError as e:
        return JsonResponse({"error": e.message}, status=400)
    except Exception:
        logger.exception(
            f"Error procesando relevamiento {pk}",
            extra={
                "body": dict(request.POST),
            },
        )
        return JsonResponse({"error": "Error interno"}, status=500)
    return response


@login_required
def nomina_editar_ajax(request, pk):
    nomina = get_object_or_404(Nomina, pk=pk)
    if request.method == "POST":
        form = NominaForm(request.POST, instance=nomina)
        if form.is_valid():
            form.save()
            return JsonResponse(
                {"success": True, "message": "Datos modificados con éxito."}
            )
        else:

            return JsonResponse({"success": False, "errors": form.errors})
    else:  # GET
        form = NominaForm(instance=nomina)
        return render(request, "comedor/nomina_editar_ajax.html", {"form": form})


class NominaDetailView(LoginRequiredMixin, TemplateView):
    template_name = "comedor/nomina_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor_pk = self.kwargs["pk"]
        page = self.request.GET.get("page", 1)

        page_obj, nomina_m, nomina_f, espera, total = ComedorService.get_nomina_detail(
            comedor_pk, page
        )

        comedor = ComedorService.get_comedor(comedor_pk)

        context.update(
            {
                "nomina": page_obj,
                "nominaM": nomina_m,
                "nominaF": nomina_f,
                "espera": espera,
                "cantidad_nomina": total,
                "object": comedor,
            }
        )
        return context


class NominaCreateView(LoginRequiredMixin, CreateView):
    model = Nomina
    form_class = NominaForm
    template_name = "comedor/nomina_form.html"

    def get_success_url(self):
        return reverse_lazy("nomina_ver", kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = ComedorService.get_comedor(self.kwargs["pk"])

        query = self.request.GET.get("query", "")
        ciudadanos = (
            ComedorService.buscar_ciudadanos_por_documento(query) if query else []
        )

        context.update(
            {
                "ciudadanos": ciudadanos,
                "no_resultados": bool(query) and not ciudadanos,
                "form_ciudadano": kwargs.get("form_ciudadano")
                or CiudadanoFormParaNomina(),
                "form_nomina_extra": kwargs.get("form_nomina_extra")
                or NominaExtraForm(),
                "estados": EstadoIntervencion.objects.all(),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        ciudadano_id = request.POST.get("ciudadano_id")

        if ciudadano_id:
            # Agregar ciudadano existente
            form_nomina_extra = NominaExtraForm(request.POST)

            if not form_nomina_extra.is_valid():
                messages.error(
                    request,
                    "Datos inválidos para agregar ciudadano a la nómina.",
                )
                context = self.get_context_data(
                    form_nomina_extra=form_nomina_extra,
                )
                return self.render_to_response(context)

            estado = form_nomina_extra.cleaned_data.get("estado")
            estado_id = estado.id if estado else None
            observaciones = form_nomina_extra.cleaned_data.get("observaciones", "")

            ok, msg = ComedorService.agregar_ciudadano_a_nomina(
                comedor_id=self.kwargs["pk"],
                ciudadano_id=ciudadano_id,
                user=request.user,
                estado_id=estado_id,
                observaciones=observaciones,
            )

            if ok:
                messages.success(request, msg)
            else:
                messages.warning(request, msg)

            return redirect(self.get_success_url())
        else:
            # Crear ciudadano nuevo
            form_ciudadano = CiudadanoFormParaNomina(request.POST)
            form_nomina_extra = NominaExtraForm(request.POST)

            if form_ciudadano.is_valid() and form_nomina_extra.is_valid():
                estado = form_nomina_extra.cleaned_data.get("estado")
                estado_id = estado.id if estado else None
                observaciones = form_nomina_extra.cleaned_data.get("observaciones")

                ok, msg = ComedorService.crear_ciudadano_y_agregar_a_nomina(
                    ciudadano_data=form_ciudadano.cleaned_data,
                    comedor_id=self.kwargs["pk"],
                    user=request.user,
                    estado_id=estado_id,
                    observaciones=observaciones,
                )

                if ok:
                    messages.success(request, msg)
                    return redirect(self.get_success_url())
                else:
                    messages.warning(request, msg)
            else:
                messages.warning(request, "Errores en el formulario de ciudadano.")

            context = self.get_context_data(
                form_ciudadano=form_ciudadano,
                form_nomina_extra=form_nomina_extra,
            )
            return self.render_to_response(context)


class NominaDeleteView(LoginRequiredMixin, DeleteView):
    model = Nomina
    template_name = "comedor/nomina_confirm_delete.html"
    pk_url_kwarg = "pk2"

    def get_success_url(self):
        return reverse_lazy("nomina_ver", kwargs={"pk": self.kwargs["pk"]})

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Registro de nómina eliminado correctamente.")
        return super().delete(request, *args, **kwargs)


class ComedorListView(LoginRequiredMixin, ListView):
    model = Comedor
    template_name = "comedor/comedor_list.html"
    context_object_name = "comedores"
    paginate_by = 10

    def get_queryset(self):
        return ComedorService.get_filtered_comedores(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Datos para componentes reutilizables
        context.update(
            {
                # Breadcrumb
                "breadcrumb_items": [
                    {"text": "Comedores", "url": reverse("comedores")},
                    {"text": "Listar", "active": True},
                ],
                # Search bar
                "reset_url": reverse("comedores"),
                "add_url": reverse("comedor_crear"),
                "filters_mode": True,
                "filters_js": "custom/js/advanced_filters.js",
                "filters_action": reverse("comedores"),
                "filters_config": get_filters_ui_config(),
            }
        )

        return context


class ComedorCreateView(LoginRequiredMixin, CreateView):
    model = Comedor
    form_class = ComedorForm
    template_name = "comedor/comedor_form.html"

    def get_success_url(self):
        return reverse("comedor_detalle", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["referente_form"] = ReferenteForm(
            self.request.POST or None, prefix="referente"
        )
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        referente_form = context["referente_form"]
        imagenes = self.request.FILES.getlist("imagenes")

        if referente_form.is_valid():
            self.object = form.save(commit=False)
            self.object.referente = referente_form.save()
            self.object.save()
            for imagen in imagenes:
                try:
                    ComedorService.create_imagenes(imagen, self.object.pk)
                except Exception:
                    return self.form_invalid(form)

            return super().form_valid(form)
        else:
            return self.form_invalid(form)


class ComedorDetailView(LoginRequiredMixin, DetailView):
    model = Comedor
    template_name = "comedor/comedor_detail.html"
    context_object_name = "comedor"

    def get_object(self, queryset=None):
        return ComedorService.get_comedor_detail_object(self.kwargs["pk"])

    def get_presupuestos_data(self):
        """Obtiene datos de presupuestos usando cache y datos prefetched cuando sea posible."""
        if (
            hasattr(self.object, "relevamientos_optimized")
            and self.object.relevamientos_optimized
        ):
            cache_key = f"presupuestos_comedor_{self.object.id}"
            cached_presupuestos = cache.get(cache_key)

            if cached_presupuestos:
                presupuestos_tuple = cached_presupuestos
            else:
                presupuestos_tuple = ComedorService.get_presupuestos(
                    self.object.id,
                    relevamientos_prefetched=self.object.relevamientos_optimized,
                )
                cache.set(
                    cache_key,
                    presupuestos_tuple,
                    getattr(settings, "COMEDOR_CACHE_TIMEOUT", 300),
                )
        else:
            presupuestos_tuple = ComedorService.get_presupuestos(self.object.id)

        (
            count_beneficiarios,
            valor_cena,
            valor_desayuno,
            valor_almuerzo,
            valor_merienda,
        ) = presupuestos_tuple

        return {
            "count_beneficiarios": count_beneficiarios,
            "presupuesto_desayuno": valor_desayuno,
            "presupuesto_almuerzo": valor_almuerzo,
            "presupuesto_merienda": valor_merienda,
            "presupuesto_cena": valor_cena,
        }

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if "admision" in request.POST:
            return ComedorService.crear_admision_desde_comedor(request, self.object)

        if request.POST.get("action") == "descartar_expediente":
            if request.user.is_superuser:

                admision_id = request.POST.get("admision_id")
                motivo_descarte = request.POST.get("motivo_descarte")

                if admision_id and motivo_descarte:
                    try:
                        admision = Admision.objects.get(id=admision_id)

                        # Obtener o crear estado "Descartado"
                        estado_descartado, _ = EstadoAdmision.objects.get_or_create(
                            nombre="Descartado"
                        )

                        admision.enviada_a_archivo = True
                        admision.motivo_descarte_expediente = motivo_descarte
                        admision.fecha_descarte_expediente = timezone.now().date()
                        admision.estado = estado_descartado
                        admision.estado_legales = "Descartado"
                        admision.save()
                        messages.success(
                            request, "Expediente descartado correctamente."
                        )
                    except Admision.DoesNotExist:
                        messages.error(request, "Admisión no encontrada.")
                else:
                    messages.error(request, "Datos incompletos.")
            else:
                messages.error(request, "No tiene permisos para realizar esta acción.")

            return redirect("comedor_detalle", pk=self.object.pk)

        return ComedorService.post_comedor_relevamiento(request, self.object)

    def get_relaciones_optimizadas(self):
        """Obtiene datos de relaciones usando prefetch cuando sea posible."""
        relevamientos = (
            self.object.relevamientos_optimized[:1]
            if hasattr(self.object, "relevamientos_optimized")
            else []
        )
        observaciones = (
            self.object.observaciones_optimized
            if hasattr(self.object, "observaciones_optimized")
            else []
        )

        count_relevamientos = (
            len(self.object.relevamientos_optimized)
            if hasattr(self.object, "relevamientos_optimized")
            else self.object.relevamiento_set.count()
        )

        comedor_categoria = (
            self.object.clasificaciones_optimized[0]
            if hasattr(self.object, "clasificaciones_optimized")
            and self.object.clasificaciones_optimized
            else None
        )

        admision = (
            self.object.admisiones_optimized
            if hasattr(self.object, "admisiones_optimized")
            and self.object.admisiones_optimized
            else None
        )

        # Preparar datos para la tabla de admisiones
        admisiones_headers = [
            {"title": "Fecha"},
            {"title": "Expediente"},
            {"title": "Convenio"},
            {"title": "Tipo"},
            {"title": "Estado"},
        ]

        admisiones_items = []
        if admision:
            for a in admision:
                admisiones_items.append(
                    {
                        "cells": [
                            {
                                "content": (
                                    a.creado.strftime("%d/%m/%Y")
                                    if hasattr(a, "creado") and a.creado
                                    else "-"
                                )
                            },
                            {
                                "content": (
                                    a.num_expediente
                                    if hasattr(a, "num_expediente") and a.num_expediente
                                    else "-"
                                )
                            },
                            {
                                "content": (
                                    a.numero_convenio
                                    if hasattr(a, "numero_convenio")
                                    and a.numero_convenio
                                    else "-"
                                )
                            },
                            {
                                "content": (
                                    a.get_tipo_display()
                                    if hasattr(a, "tipo") and a.tipo
                                    else "-"
                                )
                            },
                            {
                                "content": (
                                    a.estado.nombre
                                    if hasattr(a, "estado") and a.estado
                                    else "-"
                                )
                            },
                        ],
                        "actions": [
                            {
                                "url": reverse(
                                    "admision_detalle",
                                    args=[self.object.id, a.id],
                                ),
                                "label": "Ver",
                                "type": "primary",
                            }
                        ],
                        "admision_id": a.id,
                        "enviada_a_archivo": getattr(a, "enviada_a_archivo", False),
                        "enviado_acompaniamiento": getattr(
                            a, "enviado_acompaniamiento", False
                        ),
                    }
                )

        # Optimización: Usar imágenes prefetched en lugar de .values()
        imagenes = (
            [{"imagen": img.imagen} for img in self.object.imagenes_optimized]
            if hasattr(self.object, "imagenes_optimized")
            else list(self.object.imagenes.values("imagen"))
        )
        programa_history = (
            self.object.programa_changes_optimized
            if hasattr(self.object, "programa_changes_optimized")
            else list(
                self.object.programa_changes.select_related(
                    "from_programa", "to_programa", "changed_by"
                ).order_by("-changed_at", "-id")
            )
        )

        return {
            "relevamientos": relevamientos,
            "observaciones": observaciones,
            "count_relevamientos": count_relevamientos,
            "imagenes": imagenes,
            "comedor_categoria": comedor_categoria,
            "rendicion_cuentas_final_activo": True,  # rendiciones_mensuales >= 5, (esta validación se saca temporalmente)
            "admision": admision,
            "admisiones_headers": admisiones_headers,
            "admisiones_items": admisiones_items,
            "programa_history": programa_history,
        }

    def _get_environment_config(self):
        """Obtiene configuración del entorno."""
        return {
            "GESTIONAR_API_KEY": os.getenv("GESTIONAR_API_KEY"),
            "GESTIONAR_API_CREAR_COMEDOR": os.getenv("GESTIONAR_API_CREAR_COMEDOR"),
        }

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        presupuestos_data = self.get_presupuestos_data()
        relaciones_data = self.get_relaciones_optimizadas()
        env_config = self._get_environment_config()
        context.update({**presupuestos_data, **relaciones_data, **env_config})
        return context


# TODO: Sacar de la vista de comedores
class AsignarDuplaListView(LoginRequiredMixin, ListView):
    model = Comedor
    template_name = "comedor/asignar_dupla_form.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        comedor = ComedorService.get_comedor(self.kwargs["pk"])
        duplas = DuplaService.get_duplas_by_estado_activo()
        data["comedor"] = comedor
        data["duplas"] = duplas
        return data

    def post(self, request, *args, **kwargs):
        dupla_id = request.POST.get("dupla_id")
        comedor_id = self.kwargs["pk"]

        if dupla_id:
            try:
                ComedorService.asignar_dupla_a_comedor(dupla_id, comedor_id)
                messages.success(request, "Dupla asignada correctamente.")
            except Exception as e:
                messages.error(request, f"Error al asignar la dupla: {e}")
        else:
            messages.error(request, "No se seleccionó ninguna dupla.")

        return redirect("comedor_detalle", pk=comedor_id)


class ComedorUpdateView(LoginRequiredMixin, UpdateView):
    model = Comedor
    form_class = ComedorForm
    template_name = "comedor/comedor_form.html"

    def get_success_url(self):
        return reverse("comedor_detalle", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        self.object = self.get_object()
        data["referente_form"] = ReferenteForm(
            self.request.POST if self.request.POST else None,
            instance=self.object.referente,
            prefix="referente",
        )
        data["imagenes_borrar"] = ImagenComedor.objects.filter(
            comedor=self.object.pk
        ).only("id", "imagen")
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        referente_form = context["referente_form"]
        imagenes = self.request.FILES.getlist("imagenes")
        dupla_original = self.object.dupla

        if referente_form.is_valid():
            self.object = form.save(commit=False)
            self.object.dupla = dupla_original
            self.object.referente = referente_form.save()
            self.object.save()

            ComedorService.delete_images(self.request.POST)
            ComedorService.delete_legajo_photo(self.request.POST, self.object)

            for imagen in imagenes:
                try:
                    ComedorService.create_imagenes(imagen, self.object.pk)
                except Exception:
                    return self.form_invalid(form)

            return super().form_valid(form)
        else:
            return self.form_invalid(form)


class ComedorDeleteView(LoginRequiredMixin, DeleteView):
    model = Comedor
    template_name = "comedor/comedor_confirm_delete.html"
    context_object_name = "comedor"
    success_url = reverse_lazy("comedores")


class ObservacionCreateView(LoginRequiredMixin, CreateView):
    model = Observacion
    form_class = ObservacionForm
    template_name = "observacion/observacion_form.html"
    context_object_name = "observacion"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "comedor": Comedor.objects.values("id", "nombre").get(
                    pk=self.kwargs["comedor_pk"]
                )
            }
        )

        return context

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form.instance.comedor_id = Comedor.objects.get(pk=self.kwargs["comedor_pk"]).id
        usuario = self.request.user
        form.instance.observador = f"{usuario.first_name} {usuario.last_name}"
        form.instance.fecha_visita = timezone.now()
        self.object = form.save()
        return redirect(
            "observacion_detalle",
            comedor_pk=int(self.kwargs["comedor_pk"]),
            pk=int(self.object.id),
        )


class ObservacionDetailView(LoginRequiredMixin, DetailView):
    model = Observacion
    template_name = "observacion/observacion_detail.html"
    context_object_name = "observacion"

    def get_object(self, queryset=None) -> Model:
        return (
            Observacion.objects.prefetch_related("comedor")
            .values(
                "id",
                "fecha_visita",
                "observacion",
                "comedor__id",
                "comedor__nombre",
                "observador",
            )
            .get(pk=self.kwargs["pk"])
        )


class ObservacionUpdateView(LoginRequiredMixin, UpdateView):
    model = Observacion
    form_class = ObservacionForm
    template_name = "observacion/observacion_form.html"
    context_object_name = "observacion"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        comedor = Comedor.objects.values("id", "nombre").get(
            pk=self.kwargs["comedor_pk"]
        )

        context.update({"comedor": comedor})

        return context

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form.instance.comedor_id = Comedor.objects.get(pk=self.kwargs["comedor_pk"]).id
        usuario = self.request.user
        form.instance.observador = f"{usuario.first_name} {usuario.last_name}"
        form.instance.fecha_visita = timezone.now()
        self.object = form.save()

        return redirect(
            "observacion_detalle",
            comedor_pk=int(self.kwargs["comedor_pk"]),
            pk=int(self.object.id),
        )


class ObservacionDeleteView(LoginRequiredMixin, DeleteView):
    model = Observacion
    template_name = "observacion/observacion_confirm_delete.html"
    context_object_name = "observacion"

    def get_success_url(self):
        comedor = self.object.comedor

        return reverse_lazy("comedor_detalle", kwargs={"pk": comedor.id})
