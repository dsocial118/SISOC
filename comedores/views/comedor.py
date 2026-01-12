import os
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.html import escape, format_html
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from admisiones.models.admisiones import Admision, EstadoAdmision
from comedores.forms.comedor_form import ComedorForm, ReferenteForm
from comedores.models import Comedor, HistorialValidacion, ImagenComedor
from comedores.services.comedor_service import ComedorService
from comedores.services.filter_config import get_filters_ui_config
from core.services.favorite_filters import SeccionesFiltrosFavoritos


class ComedorListView(LoginRequiredMixin, ListView):
    model = Comedor
    template_name = "comedor/comedor_list.html"
    context_object_name = "comedores"
    paginate_by = 10

    def get_queryset(self):
        return ComedorService.get_filtered_comedores(
            self.request, user=self.request.user
        )

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
                # Barra de busqueda
                "reset_url": reverse("comedores"),
                "add_url": reverse("comedor_crear"),
                "filters_mode": True,
                "filters_js": "custom/js/advanced_filters.js",
                "filters_action": reverse("comedores"),
                "filters_config": get_filters_ui_config(),
                "seccion_filtros_favoritos": SeccionesFiltrosFavoritos.COMEDORES,
            }
        )

        return context


class ComedorCreateView(LoginRequiredMixin, CreateView):
    model = Comedor
    form_class = ComedorForm
    template_name = "comedor/comedor_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

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
            try:
                with transaction.atomic():
                    # Asignar el referente al form.instance ANTES de guardar
                    form.instance.referente = referente_form.save()

                    # Ahora llamar a save() que ejecutará toda la lógica del formulario
                    # incluyendo _sync_estado_historial
                    self.object = form.save()

                    for imagen in imagenes:
                        ComedorService.create_imagenes(imagen, self.object.pk)
            except Exception as exc:  # noqa: BLE001
                form.add_error(None, f"Error al guardar el comedor: {exc}")
                return self.form_invalid(form)

            return super().form_valid(form)

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

    def get_relaciones_optimizadas(self):  # pylint: disable=too-many-locals
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

        relevamiento_actual = relevamientos[0] if relevamientos else None
        anexo = (
            getattr(relevamiento_actual, "anexo", None) if relevamiento_actual else None
        )
        actividades_comunitarias_count = 0
        if anexo:
            actividades_flags = [
                anexo.apoyo_escolar,
                anexo.promocion_salud,
                anexo.actividades_recreativas,
                anexo.actividades_religiosas,
                anexo.actividades_jardin_maternal,
                anexo.alfabetizacion_terminalidad,
                anexo.actividades_huerta,
                anexo.actividades_culturales,
            ]
            actividades_comunitarias_count = sum(
                1 for flag in actividades_flags if flag
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
            {"title": "Estado Actual"},
            {"title": "Fecha Estado"},
            {"title": "Activa"},
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
                                    a.estado_mostrar
                                    if hasattr(a, "estado_mostrar") and a.estado_mostrar
                                    else "-"
                                )
                            },
                            {
                                "content": (
                                    a.fecha_estado_mostrar.strftime("%d/%m/%Y")
                                    if hasattr(a, "fecha_estado_mostrar")
                                    and a.fecha_estado_mostrar
                                    else "-"
                                )
                            },
                            {
                                "content": (
                                    format_html(
                                        '<i class="bi bi-check-circle-fill text-success"></i>'
                                    )
                                    if getattr(a, "activa", True)
                                    else format_html(
                                        '<i class="bi bi-x-circle-fill text-danger"></i>'
                                    )
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
                        "activa": getattr(a, "activa", True),
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

        # Paginación para historial de validaciones
        validaciones_queryset = self.object.historial_validaciones.select_related(
            "usuario"
        ).order_by("-fecha_validacion")
        paginator = Paginator(validaciones_queryset, 10)  # 10 items por página
        page_number = self.request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)
        historial_validaciones = list(page_obj)

        # Preparar datos para el componente data_table
        validaciones_headers = [
            {"title": "Fecha"},
            {"title": "Usuario"},
            {"title": "¿Fue validado?"},
            {"title": "Opciones"},
            {"title": "Comentario"},
        ]

        validaciones_items = []
        for validacion in historial_validaciones:
            # Etiqueta para estado
            if validacion.estado_validacion == "Validado":
                estado_badge = format_html(
                    '<span class="badge bg-success">{}</span>', "Validado"
                )
            elif validacion.estado_validacion == "No Validado":
                estado_badge = format_html(
                    '<span class="badge bg-danger">{}</span>', "No Validado"
                )
            else:
                estado_badge = format_html(
                    '<span class="badge bg-warning">{}</span>', "Pendiente"
                )

            usuario_nombre = (
                validacion.usuario.get_full_name() or validacion.usuario.username
                if validacion.usuario
                else "Sin información"
            )

            # Mostrar opciones solo si es "No Validado"
            opciones_display = (
                validacion.get_opciones_display()
                if validacion.estado_validacion == "No Validado"
                else "-"
            )

            fecha_validacion = validacion.fecha_validacion
            if fecha_validacion:
                if timezone.is_naive(fecha_validacion):
                    fecha_validacion = timezone.make_aware(fecha_validacion)
                fecha_validacion = timezone.localtime(fecha_validacion)
                fecha_display = fecha_validacion.strftime("%d/%m/%Y %H:%M")
            else:
                fecha_display = "-"

            validaciones_items.append(
                {
                    "cells": [
                        {"content": fecha_display},
                        {"content": usuario_nombre},
                        {"content": estado_badge},
                        {"content": opciones_display},
                        {"content": escape(validacion.comentario or "-")},
                    ]
                }
            )

        return {
            "relevamientos": relevamientos,
            "observaciones": observaciones,
            "count_relevamientos": count_relevamientos,
            "actividades_comunitarias_count": actividades_comunitarias_count,
            "imagenes": imagenes,
            "comedor_categoria": comedor_categoria,
            "rendicion_cuentas_final_activo": True,  # rendiciones_mensuales >= 5, (esta validación se saca temporalmente)
            "admision": admision,
            "admisiones_headers": admisiones_headers,
            "admisiones_items": admisiones_items,
            "programa_history": programa_history,
            "historial_validaciones": historial_validaciones,
            "validaciones_headers": validaciones_headers,
            "validaciones_items": validaciones_items,
            "page_obj": page_obj,
            "is_paginated": page_obj.has_other_pages(),
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

        # Agregar opciones de validación

        context["opciones_no_validar"] = HistorialValidacion.get_opciones_no_validar()

        context.update({**presupuestos_data, **relaciones_data, **env_config})
        return context


# TODO: Sacar de la vista de comedores
class ComedorUpdateView(LoginRequiredMixin, UpdateView):
    model = Comedor
    form_class = ComedorForm
    template_name = "comedor/comedor_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

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
            try:
                with transaction.atomic():
                    # Asignar dupla y referente al form.instance ANTES de guardar
                    form.instance.dupla = dupla_original
                    form.instance.referente = referente_form.save()

                    # Ahora llamar a save() que ejecutará toda la lógica del formulario
                    # incluyendo _sync_estado_historial
                    self.object = form.save()

                    ComedorService.delete_images(self.request.POST)
                    ComedorService.delete_legajo_photo(self.request.POST, self.object)

                    for imagen in imagenes:
                        ComedorService.create_imagenes(imagen, self.object.pk)
            except Exception as exc:  # noqa: BLE001
                form.add_error(None, f"Error al actualizar el comedor: {exc}")
                return self.form_invalid(form)

            return super().form_valid(form)

        return self.form_invalid(form)


class ComedorDeleteView(LoginRequiredMixin, DeleteView):
    model = Comedor
    template_name = "comedor/comedor_confirm_delete.html"
    context_object_name = "comedor"
    success_url = reverse_lazy("comedores")

