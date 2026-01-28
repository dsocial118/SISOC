import json
import os
from collections import defaultdict
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.html import escape, format_html, format_html_join
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from admisiones.models.admisiones import Admision, EstadoAdmision
from comedores.forms.comedor_form import ComedorForm, ReferenteForm
from comedores.models import Comedor, HistorialValidacion, ImagenComedor
from comedores.services.comedor_service import ComedorService
from comedores.services.filter_config import get_filters_ui_config
from core.services.favorite_filters import SeccionesFiltrosFavoritos
from intervenciones.models.intervenciones import Intervencion
from intervenciones.forms import IntervencionForm


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

        admisiones_qs = (
            Admision.objects.filter(comedor=self.object)
            .select_related("tipo_convenio", "estado")
            .order_by("-id")
        )
        admision = admisiones_qs
        timeline_context = ComedorService.get_admision_timeline_context(admisiones_qs)
        (
            _nomina_page_obj,
            nomina_m,
            nomina_f,
            _nomina_x,
            nomina_espera,
            nomina_total,
            nomina_rangos,
        ) = ComedorService.get_nomina_detail(self.object.pk, page=1, per_page=1)
        nomina_menores = (nomina_rangos.get("ninos") or 0) + (
            nomina_rangos.get("adolescentes") or 0
        )
        nomina_total_safe = nomina_total or 0
        nomina_activos = nomina_rangos.get("total_activos") or 0
        nomina_sin_dato = max(nomina_total_safe - nomina_activos, 0)

        def _pct(value):
            if not nomina_total_safe:
                return 0
            return int(round((value or 0) * 100 / nomina_total_safe))

        def _safe_cell(value):
            if value is None or value == "":
                return "-"
            return escape(value)

        intervenciones_qs = (
            Intervencion.objects.filter(comedor=self.object)
            .select_related("tipo_intervencion", "subintervencion", "destinatario")
            .order_by("-fecha")
        )
        intervenciones_paginator = Paginator(intervenciones_qs, 10)
        intervenciones_page_number = self.request.GET.get("intervenciones_page", 1)
        intervenciones_page_obj = intervenciones_paginator.get_page(
            intervenciones_page_number
        )
        intervenciones_page_range = intervenciones_paginator.get_elided_page_range(
            number=intervenciones_page_obj.number
        )
        intervenciones_headers = [
            {"title": "Intervención"},
            {"title": "Sub intervención"},
            {"title": "Fecha"},
            {"title": "Doc. adjunta"},
            {"title": "Destinatario"},
            {"title": "Estado"},
            {"title": "Acciones"},
        ]
        intervenciones_items = []
        for intervencion in intervenciones_page_obj:
            estado_badge = (
                format_html('<span class="badge bg-success">Completa</span>')
                if getattr(intervencion, "tiene_documentacion", False)
                else format_html(
                    '<span class="badge bg-warning text-dark">Pendiente</span>'
                )
            )
            doc_badge = (
                format_html('<span class="badge bg-success">Sí</span>')
                if getattr(intervencion, "tiene_documentacion", False)
                else format_html('<span class="badge bg-secondary">No</span>')
            )

            actions = [
                format_html(
                    '<a href="{}" class="btn btn-sm btn-primary">Ver</a>',
                    reverse("intervencion_detalle", args=[intervencion.id]),
                )
            ]
            if self.request.user.is_superuser:
                actions.append(
                    format_html(
                        '<a href="{}" class="btn btn-sm btn-danger">Eliminar</a>',
                        reverse(
                            "comedor_intervencion_borrar",
                            args=[self.object.id, intervencion.id],
                        ),
                    )
                )
            actions_html = format_html_join(
                " ", "{}", ((action,) for action in actions)
            )

            intervenciones_items.append(
                {
                    "cells": [
                        {
                            "content": _safe_cell(
                                str(intervencion.tipo_intervencion)
                                if intervencion.tipo_intervencion
                                else None
                            )
                        },
                        {
                            "content": _safe_cell(
                                str(intervencion.subintervencion)
                                if intervencion.subintervencion
                                else None
                            )
                        },
                        {
                            "content": _safe_cell(
                                intervencion.fecha.strftime("%d/%m/%Y")
                                if intervencion.fecha
                                else None
                            )
                        },
                        {"content": doc_badge},
                        {
                            "content": _safe_cell(
                                str(intervencion.destinatario)
                                if intervencion.destinatario
                                else None
                            )
                        },
                        {"content": estado_badge},
                        {"content": actions_html},
                    ]
                }
            )

        intervenciones_list = (
            Intervencion.objects.filter(comedor=self.object, fecha__isnull=False)
            .values_list("fecha", flat=True)
            .order_by("fecha")
        )

        mes_counter = defaultdict(int)
        for fecha in intervenciones_list:
            if fecha:
                mes_key = (fecha.year, fecha.month)
                mes_counter[mes_key] += 1

        meses_ordenados = sorted(mes_counter.keys())

        meses_es = [
            "Ene",
            "Feb",
            "Mar",
            "Abr",
            "May",
            "Jun",
            "Jul",
            "Ago",
            "Sep",
            "Oct",
            "Nov",
            "Dic",
        ]
        interacciones_labels = []
        interacciones_values = []
        for year, month in meses_ordenados:
            label = f"{meses_es[month - 1]} {year}"
            interacciones_labels.append(label)
            interacciones_values.append(mes_counter[(year, month)])

        # Preparar datos para la tabla de admisiones
        admisiones_headers = [
            {"title": "Fecha"},
            {"title": "Expediente"},
            {"title": "Convenio"},
            {"title": "Tipo"},
            {"title": "Estado Actual"},
            {"title": "Fecha Estado"},
            {"title": "N° Convenio"},
            {"title": "Activa"},
            {"title": "Acciones"},
        ]

        admisiones_paginator = Paginator(admisiones_qs, 5)
        admisiones_page_number = self.request.GET.get("admisiones_page", 1)
        admisiones_page_obj = admisiones_paginator.get_page(admisiones_page_number)
        admisiones_page_range = admisiones_paginator.get_elided_page_range(
            number=admisiones_page_obj.number
        )

        admisiones_items = []
        for a in admisiones_page_obj:
            actions = [
                format_html(
                    '<a href="{}" class="btn btn-primary btn-sm">Ver</a>',
                    reverse("admision_detalle", args=[self.object.id, a.id]),
                )
            ]
            if (
                self.request.user.is_superuser
                and getattr(a, "activa", True)
                and not getattr(a, "enviada_a_archivo", False)
                and not getattr(a, "enviado_acompaniamiento", False)
            ):
                actions.append(
                    format_html(
                        '<button class="btn btn-danger btn-sm" data-bs-toggle="modal" data-bs-target="#descartarModal" data-admision-id="{}">Descartar Expediente</button>',
                        a.id,
                    )
                )
            actions_html = format_html_join(
                " ", "{}", ((action,) for action in actions)
            )

            admisiones_items.append(
                {
                    "cells": [
                        {
                            "content": _safe_cell(
                                a.creado.strftime("%d/%m/%Y")
                                if hasattr(a, "creado") and a.creado
                                else None
                            )
                        },
                        {
                            "content": _safe_cell(
                                a.num_expediente
                                if hasattr(a, "num_expediente")
                                else None
                            )
                        },
                        {
                            "content": _safe_cell(
                                a.numero_convenio
                                if hasattr(a, "numero_convenio")
                                else None
                            )
                        },
                        {
                            "content": _safe_cell(
                                a.get_tipo_display()
                                if hasattr(a, "tipo") and a.tipo
                                else None
                            )
                        },
                        {
                            "content": _safe_cell(
                                a.estado_mostrar
                                if hasattr(a, "estado_mostrar")
                                else None
                            )
                        },
                        {
                            "content": _safe_cell(
                                a.fecha_estado_mostrar.strftime("%d/%m/%Y")
                                if hasattr(a, "fecha_estado_mostrar")
                                and a.fecha_estado_mostrar
                                else None
                            )
                        },
                        {
                            "content": _safe_cell(
                                a.convenio_numero
                                if hasattr(a, "convenio_numero")
                                and a.convenio_numero is not None
                                else None
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
                        {
                            "content": actions_html,
                        },
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
            {"title": "¿Fue Validado?"},
            {"title": "Detalle Validación"},
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
            **timeline_context,
            "nomina_total": nomina_total,
            "nomina_hombres": nomina_m,
            "nomina_mujeres": nomina_f,
            "nomina_menores": nomina_menores,
            "nomina_espera": nomina_espera,
            "nomina_pct_sin_dato": _pct(nomina_sin_dato),
            "nomina_pct_ninos": _pct(nomina_rangos.get("ninos")),
            "nomina_pct_adolescentes": _pct(nomina_rangos.get("adolescentes")),
            "nomina_pct_adultos": _pct(nomina_rangos.get("adultos")),
            "nomina_pct_adultos_mayores": _pct(nomina_rangos.get("adultos_mayores")),
            "nomina_pct_adulto_mayor_avanzado": _pct(
                nomina_rangos.get("adulto_mayor_avanzado")
            ),
            "intervenciones_headers": intervenciones_headers,
            "intervenciones_items": intervenciones_items,
            "intervenciones_page_obj": intervenciones_page_obj,
            "intervenciones_is_paginated": (intervenciones_page_obj.has_other_pages()),
            "intervenciones_page_range": intervenciones_page_range,
            "interacciones_labels": json.dumps(interacciones_labels),
            "interacciones_values": json.dumps(interacciones_values),
            "admisiones_headers": admisiones_headers,
            "admisiones_items": admisiones_items,
            "admisiones_page_obj": admisiones_page_obj,
            "admisiones_is_paginated": admisiones_page_obj.has_other_pages(),
            "admisiones_page_range": admisiones_page_range,
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
        intervencion_form = IntervencionForm()

        selected_admision_pk = None
        selected_param = self.request.GET.get("admision_id")
        if selected_param:
            try:
                selected_admision_pk = int(selected_param)
            except (TypeError, ValueError):
                selected_admision_pk = None

        admisiones_qs = presupuestos_data.get("admision")
        selected_admision = None
        if admisiones_qs and selected_admision_pk:
            selected_admision = admisiones_qs.filter(id=selected_admision_pk).first()

        if not selected_admision:
            selected_admision = presupuestos_data.get("admision_activa")

        # Agregar opciones de validación

        context["opciones_no_validar"] = HistorialValidacion.get_opciones_no_validar()

        context.update(
            {
                **presupuestos_data,
                **relaciones_data,
                **env_config,
                "intervencion_form": intervencion_form,
                "selected_admision": selected_admision,
                "selected_admision_id": getattr(selected_admision, "id", None),
            }
        )
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
