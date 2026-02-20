import json
import os
from collections import defaultdict
from typing import Any

from auditlog.models import LogEntry
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.html import escape, format_html, format_html_join
from django.utils.text import Truncator
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from django.views.decorators.csrf import ensure_csrf_cookie

from admisiones.models.admisiones import Admision, EstadoAdmision, InformeTecnico
from comedores.forms.comedor_form import ComedorForm, ReferenteForm
from comedores.forms.observacion_form import ObservacionForm
from comedores.models import Comedor, HistorialValidacion, ImagenComedor, Observacion
from comedores.services.comedor_service import ComedorService
from comedores.services.filter_config import get_filters_ui_config
from core.services.column_preferences import build_columns_context_from_fields
from core.services.favorite_filters import SeccionesFiltrosFavoritos
from core.soft_delete_views import SoftDeleteDeleteViewMixin
from core.utils import convert_string_to_int
from intervenciones.models.intervenciones import Intervencion
from intervenciones.forms import IntervencionForm


@method_decorator(ensure_csrf_cookie, name="dispatch")
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

        headers = [
            {"title": "ID"},
            {"title": "Nombre"},
            {"title": "Tipo"},
            {"title": "Organización"},
            {"title": "Programa"},
            {"title": "Dupla"},
            {"title": "Estado general"},
            {"title": "Estado actividad"},
            {"title": "Estado proceso"},
            {"title": "Estado detalle"},
            {"title": "Provincia"},
            {"title": "Municipio"},
            {"title": "Localidad"},
            {"title": "Barrio"},
            {"title": "Partido"},
            {"title": "Calle"},
            {"title": "Número"},
            {"title": "Ubicación"},
            {"title": "Dirección"},
            {"title": "Referente"},
            {"title": "Referente celular"},
            {"title": "Validación"},
            {"title": "Fecha validación"},
        ]
        fields = [
            {"name": "id"},
            {"name": "nombre"},
            {"name": "tipo"},
            {"name": "organizacion"},
            {"name": "programa"},
            {"name": "dupla"},
            {"name": "estado_general"},
            {"name": "estado_actividad"},
            {"name": "estado_proceso"},
            {"name": "estado_detalle"},
            {"name": "provincia"},
            {"name": "municipio"},
            {"name": "localidad"},
            {"name": "barrio"},
            {"name": "partido"},
            {"name": "calle"},
            {"name": "numero"},
            {"name": "ubicacion"},
            {"name": "direccion"},
            {"name": "referente"},
            {"name": "referente_celular"},
            {"name": "validacion"},
            {"name": "fecha_validado"},
        ]
        columns_context = build_columns_context_from_fields(
            self.request,
            "comedores_list",
            headers,
            fields,
            default_keys=[
                "nombre",
                "tipo",
                "ubicacion",
                "direccion",
                "referente",
                "validacion",
            ],
            required_keys=["nombre"],
        )
        active_columns = columns_context.get("column_active_keys") or [
            field["name"] for field in fields
        ]

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
                "column_keys_all": [field["name"] for field in fields],
                "active_columns": active_columns,
            }
        )
        context.update(columns_context)

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
        programa_nombre = (
            self.object.programa.nombre if self.object.programa else None
        )
        if (
            hasattr(self.object, "relevamientos_optimized")
            and self.object.relevamientos_optimized
        ):
            cache_key = f"presupuestos_comedor_{self.object.id}_v2"
            cached_presupuestos = cache.get(cache_key)

            if cached_presupuestos:
                presupuestos_tuple = cached_presupuestos
            else:
                presupuestos_tuple = ComedorService.get_presupuestos(
                    self.object.id,
                    relevamientos_prefetched=self.object.relevamientos_optimized,
                    programa_nombre=programa_nombre,
                )
                cache.set(
                    cache_key,
                    presupuestos_tuple,
                    getattr(settings, "COMEDOR_CACHE_TIMEOUT", 300),
                )
        else:
            presupuestos_tuple = ComedorService.get_presupuestos(
                self.object.id, programa_nombre=programa_nombre
            )

        (
            count_beneficiarios,
            valor_cena,
            valor_desayuno,
            valor_almuerzo,
            valor_merienda,
            monto_prestacion_mensual,
        ) = presupuestos_tuple

        return {
            "count_beneficiarios": count_beneficiarios,
            "presupuesto_desayuno": valor_desayuno,
            "presupuesto_almuerzo": valor_almuerzo,
            "presupuesto_merienda": valor_merienda,
            "presupuesto_cena": valor_cena,
            "monto_prestacion_mensual": monto_prestacion_mensual,
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
        relevamientos_prefetched = (
            self.object.relevamientos_optimized
            if hasattr(self.object, "relevamientos_optimized")
            else None
        )
        relevamiento_actual = ComedorService.get_relevamiento_resumen(
            relevamientos_prefetched or []
        )
        relevamientos = [relevamiento_actual] if relevamiento_actual else []
        observaciones = (
            self.object.observaciones_optimized
            if hasattr(self.object, "observaciones_optimized")
            else []
        )

        count_relevamientos = (
            len(relevamientos_prefetched)
            if relevamientos_prefetched is not None
            else self.object.relevamiento_set.count()
        )

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
        intervencion_ids = [
            intervencion.pk
            for intervencion in intervenciones_page_obj
            if intervencion.pk
        ]
        creator_map: dict[int, Any] = {}
        if intervencion_ids:
            content_type = ContentType.objects.get_for_model(Intervencion)
            logs_qs = (
                LogEntry.objects.filter(
                    content_type=content_type,
                    object_pk__in=[str(pk) for pk in intervencion_ids],
                    action=LogEntry.Action.CREATE,
                )
                .select_related("actor")
                .order_by("timestamp")
            )
            for log in logs_qs:
                try:
                    object_pk = int(log.object_pk)
                except (TypeError, ValueError):
                    continue
                creator_map.setdefault(object_pk, log.actor)

        intervenciones_headers = [
            {"title": "Fecha"},
            {"title": "Intervención"},
            {"title": "Sub intervención"},
            {"title": "Doc. adjunta"},
            {"title": "Destinatario"},
            {"title": "Usuario creador"},
            {"title": "Acciones"},
        ]
        intervenciones_items = []
        for intervencion in intervenciones_page_obj:
            doc_badge = (
                format_html('<span class="badge bg-success">Sí</span>')
                if getattr(intervencion, "tiene_documentacion", False)
                else format_html('<span class="badge bg-secondary">No</span>')
            )
            fecha_display = (
                intervencion.fecha.strftime("%d/%m/%Y") if intervencion.fecha else None
            )
            actor = creator_map.get(intervencion.pk)
            usuario_creador = "-"
            if actor:
                full_name = actor.get_full_name()
                usuario_creador = full_name or getattr(actor, "username", None) or "-"

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
                        {"content": _safe_cell(fecha_display)},
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
                        {"content": doc_badge},
                        {
                            "content": _safe_cell(
                                str(intervencion.destinatario)
                                if intervencion.destinatario
                                else None
                            )
                        },
                        {"content": _safe_cell(usuario_creador)},
                        {"content": actions_html},
                    ]
                }
            )

        observaciones_qs = (
            Observacion.objects.filter(comedor=self.object)
            .order_by("-fecha_visita")
            .select_related("comedor")
        )
        observaciones_paginator = Paginator(observaciones_qs, 5)
        observaciones_page_number = self.request.GET.get("observaciones_page", 1)
        observaciones_page_obj = observaciones_paginator.get_page(
            observaciones_page_number
        )
        observaciones_page_range = observaciones_paginator.get_elided_page_range(
            number=observaciones_page_obj.number
        )
        observaciones_headers = [
            {"title": "Fecha"},
            {"title": "Observador"},
            {"title": "Observación"},
            {"title": "Acciones"},
        ]
        observaciones_items = []
        for obs in observaciones_page_obj:
            fecha_obs = "-"
            if obs.fecha_visita:
                fecha_visita = obs.fecha_visita
                if timezone.is_naive(fecha_visita):
                    fecha_visita = timezone.make_aware(fecha_visita)
                fecha_visita = timezone.localtime(fecha_visita)
                fecha_obs = fecha_visita.strftime("%d/%m/%Y %H:%M")

            observaciones_items.append(
                {
                    "cells": [
                        {"content": fecha_obs},
                        {"content": _safe_cell(obs.observador or "Sin observador")},
                        {
                            "content": _safe_cell(
                                Truncator(obs.observacion or "").chars(80)
                            )
                        },
                        {
                            "content": format_html(
                                '<a href="{}" class="btn btn-sm btn-primary">Ver</a>',
                                reverse("observacion_detalle", kwargs={"pk": obs.id}),
                            )
                        },
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
            "observaciones_headers": observaciones_headers,
            "observaciones_items": observaciones_items,
            "observaciones_page_obj": observaciones_page_obj,
            "observaciones_is_paginated": observaciones_page_obj.has_other_pages(),
            "observaciones_page_range": observaciones_page_range,
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

        admisiones_qs = relaciones_data.get("admision")
        selected_admision = None
        if admisiones_qs and selected_admision_pk:
            selected_admision = admisiones_qs.filter(id=selected_admision_pk).first()

        if not selected_admision:
            selected_admision = relaciones_data.get("admision_activa")

        informe_tecnico = None
        if selected_admision:
            informe_tecnico = (
                InformeTecnico.objects.filter(
                    admision=selected_admision, estado_formulario="finalizado"
                )
                .order_by("-id")
                .first()
            )

        selected_convenio_numero = None
        if selected_admision:
            selected_convenio_numero = getattr(
                selected_admision, "convenio_numero", None
            )
            if selected_convenio_numero in ("", None):
                selected_convenio_numero = convert_string_to_int(
                    getattr(selected_admision, "numero_convenio", "")
                )

        prestaciones_aprobadas_total = None
        monto_prestacion_mensual_aprobadas = None
        if informe_tecnico:
            prestaciones_por_tipo = ComedorService.get_prestaciones_aprobadas_por_tipo(
                informe_tecnico
            )
            if prestaciones_por_tipo is not None:
                prestaciones_aprobadas_total = sum(prestaciones_por_tipo.values())
                programa_nombre = (
                    self.object.programa.nombre if self.object.programa else None
                )
                monto_prestacion_mensual_aprobadas = (
                    ComedorService.calcular_monto_prestacion_mensual_por_aprobadas(
                        prestaciones_por_tipo, programa_nombre=programa_nombre
                    )
                )

        total_admisiones = admisiones_qs.count() if admisiones_qs is not None else 0

        # Agregar opciones de validación

        context["opciones_no_validar"] = HistorialValidacion.get_opciones_no_validar()

        context.update(
            {
                **presupuestos_data,
                **relaciones_data,
                **env_config,
                "intervencion_form": intervencion_form,
                "observacion_form": ObservacionForm(),
                "selected_admision": selected_admision,
                "selected_admision_id": getattr(selected_admision, "id", None),
                "admisiones_informetecnico": informe_tecnico,
                "selected_convenio_numero": selected_convenio_numero,
                "total_admisiones": total_admisiones,
                "prestaciones_aprobadas_total": prestaciones_aprobadas_total,
                "monto_prestacion_mensual": monto_prestacion_mensual_aprobadas,
            }
        )
        timeline_selected = ComedorService.get_admision_timeline_context_from_admision(
            selected_admision
        )
        context.update(timeline_selected)
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


class ComedorDeleteView(SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView):
    model = Comedor
    template_name = "comedor/comedor_confirm_delete.html"
    context_object_name = "comedor"
    success_url = reverse_lazy("comedores")
    success_message = "Comedor dado de baja correctamente."
