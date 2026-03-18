import json
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
from core.soft_delete.view_helpers import SoftDeleteDeleteViewMixin
from core.utils import convert_string_to_int
from intervenciones.models.intervenciones import Intervencion
from intervenciones.forms import IntervencionForm, build_programa_aliases

MESES_ES_CORTOS = [
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


def _safe_cell_content(value):
    if value is None or value == "":
        return "-"
    return escape(value)


def _count_actividades_comunitarias(anexo) -> int:
    if not anexo:
        return 0

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
    return sum(1 for flag in actividades_flags if flag)


def _build_nomina_metrics(nomina_total, nomina_rangos):
    nomina_total_safe = nomina_total or 0
    nomina_activos = nomina_rangos.get("total_activos") or 0
    nomina_sin_dato = max(nomina_total_safe - nomina_activos, 0)
    nomina_menores = (nomina_rangos.get("ninos") or 0) + (
        nomina_rangos.get("adolescentes") or 0
    )

    def _pct(value):
        if not nomina_total_safe:
            return 0
        return int(round((value or 0) * 100 / nomina_total_safe))

    return {
        "nomina_menores": nomina_menores,
        "nomina_pct_sin_dato": _pct(nomina_sin_dato),
        "nomina_pct_ninos": _pct(nomina_rangos.get("ninos")),
        "nomina_pct_adolescentes": _pct(nomina_rangos.get("adolescentes")),
        "nomina_pct_adultos": _pct(nomina_rangos.get("adultos")),
        "nomina_pct_adultos_mayores": _pct(nomina_rangos.get("adultos_mayores")),
        "nomina_pct_adulto_mayor_avanzado": _pct(
            nomina_rangos.get("adulto_mayor_avanzado")
        ),
    }


def _build_interacciones_chart_data(fechas):
    mes_counter = defaultdict(int)
    for fecha in fechas:
        if fecha:
            mes_counter[(fecha.year, fecha.month)] += 1

    meses_ordenados = sorted(mes_counter.keys())
    interacciones_labels = []
    interacciones_values = []
    for year, month in meses_ordenados:
        interacciones_labels.append(f"{MESES_ES_CORTOS[month - 1]} {year}")
        interacciones_values.append(mes_counter[(year, month)])

    return interacciones_labels, interacciones_values


def _build_intervencion_creator_map(intervencion_ids):
    creator_map: dict[int, Any] = {}
    if not intervencion_ids:
        return creator_map

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

    return creator_map


def _build_intervenciones_table_context(comedor_obj, request):
    intervenciones_qs = (
        Intervencion.objects.filter(comedor=comedor_obj)
        .select_related("tipo_intervencion", "subintervencion", "destinatario")
        .order_by("-fecha")
    )
    intervenciones_paginator = Paginator(intervenciones_qs, 10)
    intervenciones_page_number = request.GET.get("intervenciones_page", 1)
    intervenciones_page_obj = intervenciones_paginator.get_page(
        intervenciones_page_number
    )
    intervenciones_page_range = intervenciones_paginator.get_elided_page_range(
        number=intervenciones_page_obj.number
    )
    intervencion_ids = [
        intervencion.pk for intervencion in intervenciones_page_obj if intervencion.pk
    ]
    creator_map = _build_intervencion_creator_map(intervencion_ids)

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
        if request.user.is_superuser:
            actions.append(
                format_html(
                    '<a href="{}" class="btn btn-sm btn-danger">Eliminar</a>',
                    reverse(
                        "comedor_intervencion_borrar",
                        args=[comedor_obj.id, intervencion.id],
                    ),
                )
            )
        actions_html = format_html_join(" ", "{}", ((action,) for action in actions))

        intervenciones_items.append(
            {
                "cells": [
                    {"content": _safe_cell_content(fecha_display)},
                    {
                        "content": _safe_cell_content(
                            str(intervencion.tipo_intervencion)
                            if intervencion.tipo_intervencion
                            else None
                        )
                    },
                    {
                        "content": _safe_cell_content(
                            str(intervencion.subintervencion)
                            if intervencion.subintervencion
                            else None
                        )
                    },
                    {"content": doc_badge},
                    {
                        "content": _safe_cell_content(
                            str(intervencion.destinatario)
                            if intervencion.destinatario
                            else None
                        )
                    },
                    {"content": _safe_cell_content(usuario_creador)},
                    {"content": actions_html},
                ]
            }
        )

    return {
        "intervenciones_headers": intervenciones_headers,
        "intervenciones_items": intervenciones_items,
        "intervenciones_page_obj": intervenciones_page_obj,
        "intervenciones_is_paginated": intervenciones_page_obj.has_other_pages(),
        "intervenciones_page_range": intervenciones_page_range,
    }


def _build_observaciones_table_context(comedor_obj, request):
    observaciones_qs = (
        Observacion.objects.filter(comedor=comedor_obj)
        .order_by("-fecha_visita")
        .select_related("comedor")
    )
    observaciones_paginator = Paginator(observaciones_qs, 5)
    observaciones_page_number = request.GET.get("observaciones_page", 1)
    observaciones_page_obj = observaciones_paginator.get_page(observaciones_page_number)
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
                    {"content": _safe_cell_content(obs.observador or "Sin observador")},
                    {
                        "content": _safe_cell_content(
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

    return {
        "observaciones_headers": observaciones_headers,
        "observaciones_items": observaciones_items,
        "observaciones_page_obj": observaciones_page_obj,
        "observaciones_is_paginated": observaciones_page_obj.has_other_pages(),
        "observaciones_page_range": observaciones_page_range,
    }


def _build_validaciones_table_context(comedor_obj, request):
    validaciones_queryset = comedor_obj.historial_validaciones.select_related(
        "usuario"
    ).order_by("-fecha_validacion")
    paginator = Paginator(validaciones_queryset, 10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    historial_validaciones = list(page_obj)

    validaciones_headers = [
        {"title": "Fecha"},
        {"title": "Usuario"},
        {"title": "¿Fue Validado?"},
        {"title": "Detalle Validación"},
        {"title": "Comentario"},
    ]

    validaciones_items = []
    for validacion in historial_validaciones:
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
        "historial_validaciones": historial_validaciones,
        "validaciones_headers": validaciones_headers,
        "validaciones_items": validaciones_items,
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
    }


def _build_admisiones_table_context(comedor_id, admisiones_qs, request):
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
    admisiones_page_number = request.GET.get("admisiones_page", 1)
    admisiones_page_obj = admisiones_paginator.get_page(admisiones_page_number)
    admisiones_page_range = admisiones_paginator.get_elided_page_range(
        number=admisiones_page_obj.number
    )

    admisiones_items = []
    for a in admisiones_page_obj:
        actions = [
            format_html(
                '<a href="{}" class="btn btn-primary btn-sm">Ver</a>',
                reverse("admision_detalle", args=[comedor_id, a.id]),
            )
        ]
        if (
            request.user.is_superuser
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
        actions_html = format_html_join(" ", "{}", ((action,) for action in actions))

        admisiones_items.append(
            {
                "cells": [
                    {
                        "content": _safe_cell_content(
                            a.creado.strftime("%d/%m/%Y")
                            if hasattr(a, "creado") and a.creado
                            else None
                        )
                    },
                    {
                        "content": _safe_cell_content(
                            a.num_expediente if hasattr(a, "num_expediente") else None
                        )
                    },
                    {
                        "content": _safe_cell_content(
                            a.numero_convenio if hasattr(a, "numero_convenio") else None
                        )
                    },
                    {
                        "content": _safe_cell_content(
                            a.get_tipo_display()
                            if hasattr(a, "tipo") and a.tipo
                            else None
                        )
                    },
                    {
                        "content": _safe_cell_content(
                            a.estado_mostrar if hasattr(a, "estado_mostrar") else None
                        )
                    },
                    {
                        "content": _safe_cell_content(
                            a.fecha_estado_mostrar.strftime("%d/%m/%Y")
                            if hasattr(a, "fecha_estado_mostrar")
                            and a.fecha_estado_mostrar
                            else None
                        )
                    },
                    {
                        "content": _safe_cell_content(
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
                "enviado_acompaniamiento": getattr(a, "enviado_acompaniamiento", False),
            }
        )

    return {
        "admisiones_headers": admisiones_headers,
        "admisiones_items": admisiones_items,
        "admisiones_page_obj": admisiones_page_obj,
        "admisiones_is_paginated": admisiones_page_obj.has_other_pages(),
        "admisiones_page_range": admisiones_page_range,
    }


def _build_interacciones_context(comedor_obj):
    intervenciones_list = (
        Intervencion.objects.filter(comedor=comedor_obj, fecha__isnull=False)
        .values_list("fecha", flat=True)
        .order_by("fecha")
    )
    interacciones_labels, interacciones_values = _build_interacciones_chart_data(
        intervenciones_list
    )
    return {
        "interacciones_labels": json.dumps(interacciones_labels),
        "interacciones_values": json.dumps(interacciones_values),
    }


def _build_imagenes_y_programa_history_context(comedor_obj):
    imagenes = (
        [{"imagen": img.imagen} for img in comedor_obj.imagenes_optimized]
        if hasattr(comedor_obj, "imagenes_optimized")
        else list(comedor_obj.imagenes.values("imagen"))
    )
    programa_history = (
        comedor_obj.programa_changes_optimized
        if hasattr(comedor_obj, "programa_changes_optimized")
        else list(
            comedor_obj.programa_changes.select_related(
                "from_programa", "to_programa", "changed_by"
            ).order_by("-changed_at", "-id")
        )
    )
    return {
        "imagenes": imagenes,
        "programa_history": programa_history,
    }


def _build_admisiones_y_nomina_context(comedor_obj):
    admisiones_qs = (
        Admision.objects.filter(comedor=comedor_obj)
        .select_related("tipo_convenio", "estado")
        .order_by("-id")
    )
    timeline_context = ComedorService.get_admision_timeline_context(admisiones_qs)
    admision_activa = timeline_context.get("admision_activa")
    admision_activa_id = getattr(admision_activa, "id", None)
    if admision_activa_id:
        (
            _,
            nomina_hombres,
            nomina_mujeres,
            _,
            nomina_espera,
            nomina_total,
            nomina_rangos,
        ) = ComedorService.get_nomina_detail(admision_activa_id, page=1, per_page=1)
    else:
        nomina_hombres = nomina_mujeres = nomina_espera = nomina_total = 0
        nomina_rangos = {}
    nomina_metrics = _build_nomina_metrics(nomina_total, nomina_rangos)
    return {
        "admisiones_qs": admisiones_qs,
        "timeline_context": timeline_context,
        "nomina_total": nomina_total,
        "nomina_hombres": nomina_hombres,
        "nomina_mujeres": nomina_mujeres,
        "nomina_espera": nomina_espera,
        **nomina_metrics,
    }


def _parse_selected_admision_pk(raw_value):
    if raw_value in (None, ""):
        return None
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return None


def _get_selected_admision_from_queryset(admisiones_qs, selected_admision_pk):
    if admisiones_qs is None or not selected_admision_pk:
        return None
    return admisiones_qs.filter(id=selected_admision_pk).first()


def _resolve_selected_admision(relaciones_data, selected_admision_pk):
    admisiones_qs = relaciones_data.get("admision")
    selected_admision = _get_selected_admision_from_queryset(
        admisiones_qs, selected_admision_pk
    )
    if not selected_admision:
        selected_admision = relaciones_data.get("admision_activa")
    if not selected_admision and admisiones_qs is not None:
        selected_admision = admisiones_qs.order_by("-id").first()
    return admisiones_qs, selected_admision


def _get_informe_tecnico_finalizado_from_admision(selected_admision):
    if not selected_admision:
        return None
    return (
        InformeTecnico.objects.filter(
            admision=selected_admision, estado_formulario="finalizado"
        )
        .order_by("-id")
        .first()
    )


def _resolve_selected_convenio_numero(selected_admision):
    if not selected_admision:
        return None
    selected_convenio_numero = getattr(selected_admision, "convenio_numero", None)
    if selected_convenio_numero in ("", None):
        return convert_string_to_int(getattr(selected_admision, "numero_convenio", ""))
    return selected_convenio_numero


def _build_prestaciones_aprobadas_context(informe_tecnico):
    if not informe_tecnico:
        return {
            "prestaciones_aprobadas_total": None,
            "monto_prestacion_mensual_aprobadas": None,
        }

    prestaciones_por_tipo = ComedorService.get_prestaciones_aprobadas_por_tipo(
        informe_tecnico
    )
    if prestaciones_por_tipo is None:
        return {
            "prestaciones_aprobadas_total": None,
            "monto_prestacion_mensual_aprobadas": None,
        }

    return {
        "prestaciones_aprobadas_total": sum(prestaciones_por_tipo.values()),
        "monto_prestacion_mensual_aprobadas": ComedorService.calcular_monto_prestacion_mensual_por_aprobadas(
            prestaciones_por_tipo
        ),
    }


def _build_selected_admision_context(relaciones_data, request_get):
    selected_admision_pk = _parse_selected_admision_pk(request_get.get("admision_id"))
    admisiones_qs, selected_admision = _resolve_selected_admision(
        relaciones_data, selected_admision_pk
    )
    informe_tecnico = _get_informe_tecnico_finalizado_from_admision(selected_admision)
    selected_convenio_numero = _resolve_selected_convenio_numero(selected_admision)
    prestaciones_context = _build_prestaciones_aprobadas_context(informe_tecnico)
    total_admisiones = admisiones_qs.count() if admisiones_qs is not None else 0

    return {
        "admisiones_qs": admisiones_qs,
        "selected_admision": selected_admision,
        "informe_tecnico": informe_tecnico,
        "selected_convenio_numero": selected_convenio_numero,
        "total_admisiones": total_admisiones,
        "prestaciones_aprobadas_total": prestaciones_context[
            "prestaciones_aprobadas_total"
        ],
        "monto_prestacion_mensual_aprobadas": prestaciones_context[
            "monto_prestacion_mensual_aprobadas"
        ],
    }


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
        return ComedorService.get_comedor_detail_object(
            self.kwargs["pk"], user=self.request.user
        )

    def get_presupuestos_data(self):
        """Obtiene datos de presupuestos usando cache y datos prefetched cuando sea posible."""
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

    def _build_relaciones_relevamiento_base_context(self):
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
        actividades_comunitarias_count = _count_actividades_comunitarias(anexo)
        comedor_categoria = (
            self.object.clasificaciones_optimized[0]
            if hasattr(self.object, "clasificaciones_optimized")
            and self.object.clasificaciones_optimized
            else None
        )
        return {
            "relevamientos": relevamientos,
            "observaciones": observaciones,
            "count_relevamientos": count_relevamientos,
            "actividades_comunitarias_count": actividades_comunitarias_count,
            "comedor_categoria": comedor_categoria,
        }

    def _build_relaciones_table_contexts(self, admisiones_qs):
        intervenciones_context = _build_intervenciones_table_context(
            comedor_obj=self.object,
            request=self.request,
        )
        observaciones_context = _build_observaciones_table_context(
            comedor_obj=self.object,
            request=self.request,
        )
        interacciones_context = _build_interacciones_context(self.object)
        admisiones_context = _build_admisiones_table_context(
            comedor_id=self.object.id,
            admisiones_qs=admisiones_qs,
            request=self.request,
        )
        validaciones_context = _build_validaciones_table_context(
            comedor_obj=self.object,
            request=self.request,
        )
        return {
            **intervenciones_context,
            **observaciones_context,
            **interacciones_context,
            **admisiones_context,
            **validaciones_context,
        }

    def _redirect_to_detail(self):
        return redirect("comedor_detalle", pk=self.object.pk)

    def _descartar_admision(self, admision, motivo_descarte):
        estado_descartado, _ = EstadoAdmision.objects.get_or_create(nombre="Descartado")
        admision.enviada_a_archivo = True
        admision.motivo_descarte_expediente = motivo_descarte
        admision.fecha_descarte_expediente = timezone.now().date()
        admision.estado = estado_descartado
        admision.estado_legales = "Descartado"
        admision.save()

    def _handle_descartar_expediente_post(self, request):
        if request.POST.get("action") != "descartar_expediente":
            return None

        if not request.user.is_superuser:
            messages.error(request, "No tiene permisos para realizar esta acción.")
            return self._redirect_to_detail()

        admision_id = request.POST.get("admision_id")
        motivo_descarte = request.POST.get("motivo_descarte")

        if not (admision_id and motivo_descarte):
            messages.error(request, "Datos incompletos.")
            return self._redirect_to_detail()

        try:
            admision = Admision.objects.get(id=admision_id)
        except Admision.DoesNotExist:
            messages.error(request, "Admisión no encontrada.")
            return self._redirect_to_detail()

        self._descartar_admision(admision, motivo_descarte)
        messages.success(request, "Expediente descartado correctamente.")
        return self._redirect_to_detail()

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if "admision" in request.POST:
            return ComedorService.crear_admision_desde_comedor(request, self.object)

        response = self._handle_descartar_expediente_post(request)
        if response is not None:
            return response

        return ComedorService.post_comedor_relevamiento(request, self.object)

    def get_relaciones_optimizadas(self):  # pylint: disable=too-many-locals
        """Obtiene datos de relaciones usando prefetch cuando sea posible."""
        base_context = self._build_relaciones_relevamiento_base_context()

        admisiones_nomina_context = _build_admisiones_y_nomina_context(self.object)
        admisiones_qs = admisiones_nomina_context["admisiones_qs"]
        table_contexts = self._build_relaciones_table_contexts(admisiones_qs)
        media_programa_context = _build_imagenes_y_programa_history_context(self.object)

        return {
            **base_context,
            **media_programa_context,
            "rendicion_cuentas_final_activo": True,  # rendiciones_mensuales >= 5, (esta validación se saca temporalmente)
            "admision": admisiones_qs,
            **admisiones_nomina_context["timeline_context"],
            **table_contexts,
        }

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        presupuestos_data = self.get_presupuestos_data()
        relaciones_data = self.get_relaciones_optimizadas()
        programa_nombre = getattr(
            getattr(self.object, "programa", None), "nombre", None
        )
        intervencion_form = IntervencionForm(
            programa_aliases=build_programa_aliases(programa_nombre)
        )
        selected_admision_context = _build_selected_admision_context(
            relaciones_data, self.request.GET
        )
        selected_admision = selected_admision_context["selected_admision"]
        informe_tecnico = selected_admision_context["informe_tecnico"]

        # Nómina del convenio seleccionado
        selected_admision_pk = getattr(selected_admision, "pk", None)
        if selected_admision_pk is not None:
            (
                _,
                nomina_m,
                nomina_f,
                _,
                nomina_espera,
                nomina_total,
                nomina_rangos,
            ) = ComedorService.get_nomina_detail(
                selected_admision_pk, page=1, per_page=1
            )
        else:
            nomina_m = nomina_f = nomina_espera = nomina_total = 0
            nomina_rangos = {}

        nomina_metrics = _build_nomina_metrics(nomina_total, nomina_rangos)

        # Agregar opciones de validación

        context["opciones_no_validar"] = HistorialValidacion.get_opciones_no_validar()

        context.update(
            {
                **presupuestos_data,
                **relaciones_data,
                **nomina_metrics,
                "nomina_total": nomina_total,
                "nomina_hombres": nomina_m,
                "nomina_mujeres": nomina_f,
                "nomina_espera": nomina_espera,
                "intervencion_form": intervencion_form,
                "observacion_form": ObservacionForm(),
                "selected_admision": selected_admision,
                "selected_admision_id": getattr(selected_admision, "id", None),
                "admisiones_informetecnico": informe_tecnico,
                "selected_convenio_numero": selected_admision_context[
                    "selected_convenio_numero"
                ],
                "total_admisiones": selected_admision_context["total_admisiones"],
                "prestaciones_aprobadas_total": selected_admision_context[
                    "prestaciones_aprobadas_total"
                ],
                "monto_prestacion_mensual": selected_admision_context[
                    "monto_prestacion_mensual_aprobadas"
                ],
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

    def get_queryset(self):
        return ComedorService.get_scoped_comedor_queryset(self.request.user)

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

    def get_queryset(self):
        return ComedorService.get_scoped_comedor_queryset(self.request.user)
