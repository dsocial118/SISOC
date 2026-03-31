# pylint: disable=too-many-lines
import logging
import os
from datetime import date, datetime

import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.html import escape, format_html, format_html_join
from django.utils.text import Truncator
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from auditlog.models import LogEntry
from ciudadanos.models import Ciudadano
from comedores.services.comedor_service import ComedorService
from core.decorators import permissions_any_required
from core.models import Nacionalidad, Sexo
from core.security import safe_redirect
from core.services.column_preferences import build_columns_context_from_fields
from core.soft_delete.view_helpers import SoftDeleteDeleteViewMixin
from iam.services import user_has_permission_code

from centrodeinfancia.access import (
    aplicar_filtro_provincia_usuario as _aplicar_filtro_provincia_usuario,
    get_object_scoped_por_provincia_or_404,
)
from centrodeinfancia.forms import (
    CentroDeInfanciaForm,
    IntervencionCentroInfanciaForm,
    NominaCentroInfanciaCreateForm,
    NominaCentroInfanciaForm,
    ObservacionCentroInfanciaForm,
    TrabajadorForm,
)
from centrodeinfancia.formulario_cdi_schema import CAMPOS_OPCIONES_MULTIPLES
from centrodeinfancia.models import (
    CentroDeInfancia,
    DepartamentoIpi,
    IntervencionCentroInfancia,
    NominaCentroInfancia,
    ObservacionCentroInfancia,
    Trabajador,
)
from centrodeinfancia.views_formulario_cdi import construir_resumenes_formularios
from intervenciones.constants import PROGRAMA_ALIASES_CENTRO_INFANCIA


CDI_LIST_HEADERS = [
    {"title": "Nombre"},
    {"title": "Organización"},
    {"title": "Tiene nómina"},
    {"title": "Provincia"},
    {"title": "Departamento"},
    {"title": "Municipio"},
    {"title": "Localidad"},
    {"title": "Calle"},
    {"title": "Teléfono"},
    {"title": "Referente"},
]

CDI_LIST_FIELDS = [
    {"name": "nombre"},
    {"name": "organizacion"},
    {"name": "tiene_nomina"},
    {"name": "provincia"},
    {"name": "departamento"},
    {"name": "municipio"},
    {"name": "localidad"},
    {"name": "calle"},
    {"name": "telefono"},
    {"name": "referente"},
]

logger = logging.getLogger(__name__)

DOCUMENTACION_INTERVENCION_MAX_SIZE_BYTES = 5 * 1024 * 1024
DOCUMENTACION_INTERVENCION_EXTS_PERMITIDAS = {".pdf", ".jpg", ".jpeg", ".png"}

MESES_FUNCIONAMIENTO_MAP = dict(CAMPOS_OPCIONES_MULTIPLES["meses_funcionamiento"])
DIAS_FUNCIONAMIENTO_MAP = dict(CAMPOS_OPCIONES_MULTIPLES["dias_funcionamiento"])


def _centros_cdi_queryset_detalle():
    return CentroDeInfancia.objects.select_related(
        "provincia",
        "departamento",
        "municipio",
        "localidad",
    ).prefetch_related("horarios_funcionamiento")


def _formatear_lista_opciones(valores, labels_map):
    if not valores:
        return "-"
    return ", ".join(labels_map.get(valor, valor) for valor in valores)


def _formatear_cuit(value):
    if not value:
        return "-"
    digits = "".join(ch for ch in str(value) if ch.isdigit())[:11]
    if len(digits) != 11:
        return value
    return f"{digits[:2]}-{digits[2:10]}-{digits[10:]}"


def _construir_horarios_detalle(centro):
    horarios = []
    for horario in centro.horarios_funcionamiento.all():
        horarios.append(
            {
                "dia": horario.get_dia_display(),
                "apertura": (
                    horario.hora_apertura.strftime("%H:%M")
                    if horario.hora_apertura
                    else "-"
                ),
                "cierre": (
                    horario.hora_cierre.strftime("%H:%M")
                    if horario.hora_cierre
                    else "-"
                ),
            }
        )
    return horarios


def _centros_cdi_queryset_scoped(user):
    return _aplicar_filtro_provincia_usuario(_centros_cdi_queryset_detalle(), user)


def _get_centro_cdi_scoped_or_404(user, **kwargs):
    return get_object_scoped_por_provincia_or_404(
        _centros_cdi_queryset_detalle(),
        user,
        provincia_lookup="provincia",
        **kwargs,
    )


def _aplicar_scope_provincia_centro_relacion(queryset, user):
    return _aplicar_filtro_provincia_usuario(
        queryset,
        user,
        provincia_lookup="centro__provincia",
    )


def _intervenciones_cdi_queryset_scoped(user):
    queryset = IntervencionCentroInfancia.objects.select_related("centro")
    return _aplicar_scope_provincia_centro_relacion(queryset, user)


def _nomina_cdi_queryset_scoped(user):
    queryset = NominaCentroInfancia.objects.select_related("centro")
    return _aplicar_scope_provincia_centro_relacion(queryset, user)


def _trabajadores_cdi_queryset_scoped(user):
    queryset = Trabajador.objects.select_related("centro")
    return _aplicar_scope_provincia_centro_relacion(queryset, user)


def _observaciones_cdi_queryset_scoped(user):
    queryset = ObservacionCentroInfancia.objects.select_related("centro")
    return _aplicar_scope_provincia_centro_relacion(queryset, user)


def _build_trabajadores_context(
    request,
    centro,
    form=None,
    *,
    modal=None,
):
    form = form or TrabajadorForm()
    modal = modal or {}
    return {
        "trabajadores": centro.trabajadores.order_by("apellido", "nombre"),
        "trabajador_form": form,
        "trabajador_modal_open": modal.get("open", False),
        "trabajador_modal_mode": modal.get("mode", "create"),
        "trabajador_form_action": modal.get("action")
        or reverse("centrodeinfancia_trabajador_crear", kwargs={"pk": centro.pk}),
        "puede_editar_trabajadores": request.user.has_perm(
            "centrodeinfancia.change_centrodeinfancia"
        ),
        "puede_eliminar_trabajadores": request.user.has_perm(
            "centrodeinfancia.delete_centrodeinfancia"
        ),
    }


def _validar_archivo_documentacion_intervencion(file_obj):
    if not file_obj:
        return "No se proporcionó un archivo."

    extension = os.path.splitext(getattr(file_obj, "name", "") or "")[1].lower()
    if extension not in DOCUMENTACION_INTERVENCION_EXTS_PERMITIDAS:
        return "Formato de archivo no permitido. Use PDF, JPG o PNG."

    if (getattr(file_obj, "size", 0) or 0) > DOCUMENTACION_INTERVENCION_MAX_SIZE_BYTES:
        return "El archivo supera el tamaño máximo permitido (5 MB)."

    return None


class CentroDeInfanciaListView(LoginRequiredMixin, ListView):
    model = CentroDeInfancia
    template_name = "centrodeinfancia/centrodeinfancia_list.html"
    context_object_name = "centros"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("busqueda")
        nomina_subquery = NominaCentroInfancia.objects.filter(centro_id=OuterRef("pk"))
        queryset = CentroDeInfancia.objects.select_related(
            "provincia",
            "departamento",
            "municipio",
            "localidad",
        ).annotate(tiene_nomina=Exists(nomina_subquery))
        queryset = _aplicar_filtro_provincia_usuario(queryset, self.request.user)
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query) | Q(organizacion__icontains=query)
            )
        return queryset.order_by("nombre")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        columns_context = build_columns_context_from_fields(
            self.request,
            "centrodeinfancia_list",
            CDI_LIST_HEADERS,
            CDI_LIST_FIELDS,
            default_keys=[
                "nombre",
                "organizacion",
                "tiene_nomina",
                "provincia",
                "departamento",
                "municipio",
            ],
            required_keys=["nombre"],
        )
        context["breadcrumb_items"] = [
            {
                "text": "Centro de Desarrollo Infantil",
                "url": reverse("centrodeinfancia"),
            },
            {"text": "Listar", "active": True},
        ]
        context["query"] = self.request.GET.get("busqueda", "")
        context["active_columns"] = columns_context.get("column_active_keys") or [
            field["name"] for field in CDI_LIST_FIELDS
        ]
        context.update(columns_context)
        return context


class CentroDeInfanciaCreateView(LoginRequiredMixin, CreateView):
    model = CentroDeInfancia
    form_class = CentroDeInfanciaForm
    template_name = "centrodeinfancia/centrodeinfancia_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["lock_provincia_from_user"] = True
        return kwargs

    def get_success_url(self):
        return reverse("centrodeinfancia_detalle", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get("form")
        context["horario_fields"] = [
            {
                "dia": dia,
                "etiqueta": etiqueta,
                "apertura": form[f"horario_{dia}_apertura"],
                "cierre": form[f"horario_{dia}_cierre"],
            }
            for dia, etiqueta in form.DIAS_SEMANA
        ]
        return context


class CentroDeInfanciaDetailView(LoginRequiredMixin, DetailView):
    model = CentroDeInfancia
    template_name = "centrodeinfancia/centrodeinfancia_detail.html"
    context_object_name = "centro"

    def get_queryset(self):
        return _centros_cdi_queryset_scoped(self.request.user)

    def get_context_data(  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        self, **kwargs
    ):
        context = super().get_context_data(**kwargs)
        nomina_qs = self.object.nominas.select_related(
            "ciudadano",
            "ciudadano__sexo",
        ).order_by("-fecha")
        intervenciones_qs = self.object.intervenciones.select_related(
            "tipo_intervencion", "subintervencion", "destinatario"
        ).order_by("-fecha")

        today = timezone.now().date()
        hombres = 0
        mujeres = 0
        menores = 0
        nomina_espera = 0

        def _safe_cell(value):
            if value is None or value == "":
                return "-"
            return escape(value)

        for registro in nomina_qs:
            ciudadano = registro.ciudadano
            sexo = str(
                registro.sexo or getattr(getattr(ciudadano, "sexo", None), "sexo", "") or ""
            ).lower()

            if registro.estado == NominaCentroInfancia.ESTADO_PENDIENTE:
                nomina_espera += 1

            if "mascul" in sexo or sexo == "m":
                hombres += 1
            elif "femen" in sexo or sexo == "f":
                mujeres += 1

            fecha_nacimiento = registro.fecha_nacimiento or getattr(
                ciudadano, "fecha_nacimiento", None
            )
            if fecha_nacimiento:
                edad = (
                    today.year
                    - fecha_nacimiento.year
                    - (
                        (today.month, today.day)
                        < (fecha_nacimiento.month, fecha_nacimiento.day)
                    )
                )
                if edad < 18:
                    menores += 1

        nomina_page = self.request.GET.get("nomina_page", 1)
        intervenciones_page = self.request.GET.get("intervenciones_page", 1)
        observaciones_page = self.request.GET.get("observaciones_page", 1)

        nomina_paginator = Paginator(nomina_qs, 10)
        intervenciones_paginator = Paginator(intervenciones_qs, 10)
        observaciones_qs = self.object.observaciones.order_by("-fecha_visita")
        observaciones_paginator = Paginator(observaciones_qs, 5)

        nomina_page_obj = nomina_paginator.get_page(nomina_page)
        intervenciones_page_obj = intervenciones_paginator.get_page(intervenciones_page)
        observaciones_page_obj = observaciones_paginator.get_page(observaciones_page)

        intervencion_ids = [intervencion.pk for intervencion in intervenciones_page_obj]
        creator_map = {}
        if intervencion_ids:
            content_type = ContentType.objects.get_for_model(IntervencionCentroInfancia)
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
                    reverse(
                        "centrodeinfancia_intervencion_detalle",
                        args=[intervencion.id],
                    ),
                ),
                format_html(
                    '<a href="{}" class="btn btn-sm btn-warning">Editar</a>',
                    reverse(
                        "centrodeinfancia_intervencion_editar",
                        args=[self.object.id, intervencion.id],
                    ),
                ),
            ]
            if self.request.user.is_superuser:
                actions.append(
                    format_html(
                        '<a href="{}" class="btn btn-sm btn-danger">Eliminar</a>',
                        reverse(
                            "centrodeinfancia_intervencion_borrar",
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

        intervenciones_page_range = intervenciones_paginator.get_elided_page_range(
            number=intervenciones_page_obj.number
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
                                reverse(
                                    "centrodeinfancia_observacion_detalle",
                                    kwargs={"pk": obs.id},
                                ),
                            )
                        },
                    ]
                }
            )

        context["nomina_page_obj"] = nomina_page_obj
        context["intervenciones_page_obj"] = intervenciones_page_obj
        context["nomina_total"] = nomina_qs.count()
        context["nomina_hombres"] = hombres
        context["nomina_mujeres"] = mujeres
        context["nomina_menores"] = menores
        context["nomina_espera"] = nomina_espera
        context["nomina_resumen"] = {
            "hombres": hombres,
            "mujeres": mujeres,
            "menores": menores,
        }
        context["intervenciones_total"] = intervenciones_qs.count()
        context["intervenciones_headers"] = intervenciones_headers
        context["intervenciones_items"] = intervenciones_items
        context["intervenciones_is_paginated"] = (
            intervenciones_page_obj.has_other_pages()
        )
        context["intervenciones_page_range"] = intervenciones_page_range
        context["observaciones_headers"] = observaciones_headers
        context["observaciones_items"] = observaciones_items
        context["observaciones_page_obj"] = observaciones_page_obj
        context["observaciones_is_paginated"] = observaciones_page_obj.has_other_pages()
        context["observaciones_page_range"] = observaciones_page_range
        context["centro_info_basica"] = {
            "organizacion": self.object.organizacion or "-",
            "cuit_organizacion_gestiona": _formatear_cuit(
                self.object.cuit_organizacion_gestiona
            ),
            "ambito": self.object.get_ambito_display() or "-",
            "mail": self.object.mail or "-",
            "fecha_inicio": (
                self.object.fecha_inicio.strftime("%d/%m/%Y")
                if self.object.fecha_inicio
                else "-"
            ),
        }
        context["centro_funcionamiento"] = {
            "meses_funcionamiento": _formatear_lista_opciones(
                self.object.meses_funcionamiento,
                MESES_FUNCIONAMIENTO_MAP,
            ),
            "dias_funcionamiento": _formatear_lista_opciones(
                self.object.dias_funcionamiento,
                DIAS_FUNCIONAMIENTO_MAP,
            ),
            "horarios": _construir_horarios_detalle(self.object),
            "tipo_jornada": (
                self.object.get_tipo_jornada_display()
                if self.object.tipo_jornada
                else "-"
            ),
            "tipo_jornada_otra": self.object.tipo_jornada_otra or "",
            "oferta_servicios": (
                self.object.get_oferta_servicios_display()
                if self.object.oferta_servicios
                else "-"
            ),
            "modalidad_gestion": (
                self.object.get_modalidad_gestion_display()
                if self.object.modalidad_gestion
                else "-"
            ),
            "modalidad_gestion_otra": self.object.modalidad_gestion_otra or "",
        }

        intervencion_form = IntervencionCentroInfanciaForm(
            destinatario_fijo_nombre="Centro",
            hide_destinatario=True,
        )
        context["intervencion_form"] = intervencion_form
        context["observacion_form"] = ObservacionCentroInfanciaForm()
        if user_has_permission_code(
            self.request.user, "centrodeinfancia.view_formulariocdi"
        ):
            formularios_qs = self.object.formularios.select_related(
                "created_by"
            ).order_by("-fecha_relevamiento", "-created_at", "-id")
            context["formularios_total"] = formularios_qs.count()
            context["formularios_recent"] = construir_resumenes_formularios(
                list(formularios_qs[:3])
            )
        else:
            context["formularios_total"] = 0
            context["formularios_recent"] = []

        tipo_intervencion_queryset = list(
            intervencion_form.fields["tipo_intervencion"].queryset
        )
        tipo_programas_map = {
            str(tipo.pk): (tipo.programa or "").strip()
            for tipo in tipo_intervencion_queryset
        }
        alias_list = list(PROGRAMA_ALIASES_CENTRO_INFANCIA)
        context["tipo_intervencion_programas"] = tipo_programas_map
        context["tipo_intervencion_programa_aliases"] = alias_list
        context["tipo_intervencion_programas_json"] = json.dumps(tipo_programas_map)
        context["tipo_intervencion_programa_aliases_json"] = json.dumps(alias_list)
        context.update(_build_trabajadores_context(self.request, self.object))
        return context


class CentroDeInfanciaUpdateView(LoginRequiredMixin, UpdateView):
    model = CentroDeInfancia
    form_class = CentroDeInfanciaForm
    template_name = "centrodeinfancia/centrodeinfancia_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["lock_provincia_from_user"] = False
        return kwargs

    def get_success_url(self):
        return reverse("centrodeinfancia_detalle", kwargs={"pk": self.object.pk})

    def get_queryset(self):
        return _centros_cdi_queryset_scoped(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get("form")
        context["horario_fields"] = [
            {
                "dia": dia,
                "etiqueta": etiqueta,
                "apertura": form[f"horario_{dia}_apertura"],
                "cierre": form[f"horario_{dia}_cierre"],
            }
            for dia, etiqueta in form.DIAS_SEMANA
        ]
        return context


class CentroDeInfanciaDeleteView(
    SoftDeleteDeleteViewMixin,
    LoginRequiredMixin,
    DeleteView,
):
    model = CentroDeInfancia
    template_name = "centrodeinfancia/centrodeinfancia_confirm_delete.html"
    context_object_name = "centro"
    success_url = reverse_lazy("centrodeinfancia")
    success_message = "Centro de Desarrollo Infantil dado de baja correctamente."

    def get_queryset(self):
        return _centros_cdi_queryset_scoped(self.request.user)


class TrabajadorCentroInfanciaCreateView(LoginRequiredMixin, CreateView):
    model = Trabajador
    form_class = TrabajadorForm

    def dispatch(self, request, *args, **kwargs):
        self.centro = _get_centro_cdi_scoped_or_404(request.user, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.centro = self.centro
        response = super().form_valid(form)
        messages.success(self.request, "Trabajador agregado correctamente.")
        return response

    def form_invalid(self, form):
        detail_view = CentroDeInfanciaDetailView()
        detail_view.setup(self.request, pk=self.centro.pk)
        detail_view.object = self.centro
        context = detail_view.get_context_data(object=self.centro)
        context.update(
            _build_trabajadores_context(
                self.request,
                self.centro,
                form=form,
                modal={
                    "open": True,
                    "mode": "create",
                    "action": self.request.path,
                },
            )
        )
        return render(
            self.request,
            "centrodeinfancia/centrodeinfancia_detail.html",
            context,
            status=400,
        )

    def get_success_url(self):
        return reverse("centrodeinfancia_detalle", kwargs={"pk": self.centro.pk})


class TrabajadorCentroInfanciaUpdateView(LoginRequiredMixin, UpdateView):
    model = Trabajador
    form_class = TrabajadorForm
    pk_url_kwarg = "trabajador_id"

    def get_queryset(self):
        return _trabajadores_cdi_queryset_scoped(self.request.user).filter(
            centro_id=self.kwargs["pk"]
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Trabajador actualizado correctamente.")
        return response

    def form_invalid(self, form):
        centro = self.object.centro
        detail_view = CentroDeInfanciaDetailView()
        detail_view.setup(self.request, pk=centro.pk)
        detail_view.object = centro
        context = detail_view.get_context_data(object=centro)
        context.update(
            _build_trabajadores_context(
                self.request,
                centro,
                form=form,
                modal={
                    "open": True,
                    "mode": "edit",
                    "action": self.request.path,
                },
            )
        )
        return render(
            self.request,
            "centrodeinfancia/centrodeinfancia_detail.html",
            context,
            status=400,
        )

    def get_success_url(self):
        return reverse(
            "centrodeinfancia_detalle",
            kwargs={"pk": self.object.centro_id},
        )


class TrabajadorCentroInfanciaDeleteView(
    SoftDeleteDeleteViewMixin,
    LoginRequiredMixin,
    DeleteView,
):
    model = Trabajador
    pk_url_kwarg = "trabajador_id"
    template_name = "centrodeinfancia/trabajador_confirm_delete.html"
    context_object_name = "trabajador"
    success_message = "Trabajador eliminado correctamente."

    def get_queryset(self):
        return _trabajadores_cdi_queryset_scoped(self.request.user).filter(
            centro_id=self.kwargs["pk"]
        )

    def get_success_url(self):
        return reverse("centrodeinfancia_detalle", kwargs={"pk": self.kwargs["pk"]})


@login_required
def centrodeinfancia_ajax(request):
    @permissions_any_required(["centrodeinfancia.view_centrodeinfancia"])
    def _centrodeinfancia_ajax(req):
        query = req.GET.get("busqueda", "")
        page = req.GET.get("page", 1)
        columns_context = build_columns_context_from_fields(
            req,
            "centrodeinfancia_list",
            CDI_LIST_HEADERS,
            CDI_LIST_FIELDS,
            default_keys=[
                "nombre",
                "organizacion",
                "provincia",
                "departamento",
                "municipio",
            ],
            required_keys=["nombre"],
        )
        active_columns = columns_context.get("column_active_keys") or [
            field["name"] for field in CDI_LIST_FIELDS
        ]

        queryset = CentroDeInfancia.objects.select_related(
            "provincia",
            "departamento",
            "municipio",
            "localidad",
        )
        queryset = _aplicar_filtro_provincia_usuario(queryset, req.user)
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query) | Q(organizacion__icontains=query)
            )
        queryset = queryset.order_by("nombre")

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page)
        html = render_to_string(
            "centrodeinfancia/partials/rows.html",
            {
                "centros": page_obj,
                "active_columns": active_columns,
            },
            request=req,
        )
        return JsonResponse(
            {
                "html": html,
                "count": paginator.count,
                "num_pages": paginator.num_pages,
                "current_page": page_obj.number,
            }
        )

    return _centrodeinfancia_ajax(request)


@login_required
@require_GET
def load_departamentos_ipi(request):
    departamentos = DepartamentoIpi.objects.none()

    try:
        provincia_id = int(request.GET.get("provincia_id", ""))
        departamentos = DepartamentoIpi.objects.filter(provincia_id=provincia_id)
    except (ValueError, TypeError):
        pass

    return JsonResponse(
        list(departamentos.order_by("nombre").values("id", "nombre", "decil_ipi")),
        safe=False,
    )


class NominaCentroInfanciaDetailView(LoginRequiredMixin, ListView):
    model = NominaCentroInfancia
    template_name = "centrodeinfancia/nomina_detail.html"
    context_object_name = "nomina"
    paginate_by = 100

    def _get_centro(self):
        if not hasattr(self, "_centro_cache"):
            self._centro_cache = _get_centro_cdi_scoped_or_404(
                self.request.user,
                pk=self.kwargs["pk"],
            )
        return self._centro_cache

    def get_queryset(self):
        centro = self._get_centro()
        return (
            NominaCentroInfancia.objects.select_related(
                "ciudadano",
                "ciudadano__sexo",
            )
            .filter(centro=centro)
            .order_by("-fecha")
        )

    @staticmethod
    def _build_nomina_stats(registros):
        today = timezone.now().date()
        resumen = {
            "nomina_m": 0,
            "nomina_f": 0,
            "nomina_x": 0,
            "espera": 0,
            "total": 0,
            "rangos": {
                "ninos": 0,
                "adolescentes": 0,
                "adultos": 0,
                "adultos_mayores": 0,
                "adulto_mayor_avanzado": 0,
                "total_activos": 0,
            },
        }

        for registro in registros:
            resumen["total"] += 1
            if registro.estado == NominaCentroInfancia.ESTADO_PENDIENTE:
                resumen["espera"] += 1

            sexo = str(
                registro.sexo
                or getattr(getattr(registro.ciudadano, "sexo", None), "sexo", "")
                or ""
            ).strip().lower()
            if "mascul" in sexo or sexo == "m":
                resumen["nomina_m"] += 1
            elif "femen" in sexo or sexo == "f":
                resumen["nomina_f"] += 1
            elif sexo == "x" or "no bin" in sexo:
                resumen["nomina_x"] += 1

            fecha_nacimiento = registro.fecha_nacimiento or getattr(
                registro.ciudadano, "fecha_nacimiento", None
            )
            if (
                registro.estado != NominaCentroInfancia.ESTADO_ACTIVO
                or not fecha_nacimiento
            ):
                continue

            edad = (
                today.year
                - fecha_nacimiento.year
                - (
                    (today.month, today.day)
                    < (fecha_nacimiento.month, fecha_nacimiento.day)
                )
            )
            resumen["rangos"]["total_activos"] += 1

            if edad <= 13:
                resumen["rangos"]["ninos"] += 1
            elif edad <= 17:
                resumen["rangos"]["adolescentes"] += 1
            elif edad <= 49:
                resumen["rangos"]["adultos"] += 1
            elif edad <= 65:
                resumen["rangos"]["adultos_mayores"] += 1
            else:
                resumen["rangos"]["adulto_mayor_avanzado"] += 1

        total_activos = resumen["rangos"]["total_activos"] or 0

        def _pct(value):
            if not total_activos:
                return 0
            return int(round((value or 0) * 100 / total_activos))

        resumen["rangos"].update(
            {
                "pct_ninos": _pct(resumen["rangos"]["ninos"]),
                "pct_adolescentes": _pct(resumen["rangos"]["adolescentes"]),
                "pct_adultos": _pct(resumen["rangos"]["adultos"]),
                "pct_adultos_mayores": _pct(resumen["rangos"]["adultos_mayores"]),
                "pct_adulto_mayor_avanzado": _pct(
                    resumen["rangos"]["adulto_mayor_avanzado"]
                ),
            }
        )
        return resumen

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        centro = self._get_centro()
        stats = self._build_nomina_stats(self.object_list)
        page_obj = context.get("page_obj")

        context["object"] = centro
        context["nomina"] = page_obj
        context["nominaM"] = stats["nomina_m"]
        context["nominaF"] = stats["nomina_f"]
        context["nominaX"] = stats["nomina_x"]
        context["espera"] = stats["espera"]
        context["cantidad_nomina"] = stats["total"]
        context["menores"] = stats["rangos"]["ninos"] + stats["rangos"]["adolescentes"]
        context["nomina_rangos"] = stats["rangos"]
        context["ejecucion_inicio"] = centro.fecha_inicio
        context["ejecucion_fin"] = None
        context["plazo_ejecucion"] = "-"
        return context


class NominaCentroInfanciaCreateView(LoginRequiredMixin, CreateView):
    model = NominaCentroInfancia
    form_class = NominaCentroInfanciaCreateForm
    template_name = "centrodeinfancia/nomina_form.html"

    def _get_centro(self):
        if not hasattr(self, "_centro_cache"):
            self._centro_cache = _get_centro_cdi_scoped_or_404(
                self.request.user,
                pk=self.kwargs["pk"],
            )
        return self._centro_cache

    @staticmethod
    def _crear_nomina_con_bloqueo(centro, ciudadano, cleaned_data):
        CentroDeInfancia.objects.select_for_update().filter(pk=centro.pk).exists()
        existente = NominaCentroInfancia.objects.filter(
            centro=centro,
            ciudadano=ciudadano,
            deleted_at__isnull=True,
        ).exists()
        if existente:
            return False

        nomina_data = {
            field_name: cleaned_data.get(field_name)
            for field_name in NominaCentroInfanciaCreateForm.Meta.fields
            if field_name != "edad_calculada"
        }
        nomina = NominaCentroInfancia(
            centro=centro,
            ciudadano=ciudadano,
            **nomina_data,
        )
        nomina.clean()
        nomina.save()
        return True

    def get_success_url(self):
        return reverse("centrodeinfancia_nomina_ver", kwargs={"pk": self.kwargs["pk"]})

    @staticmethod
    def _build_nomina_initial_from_ciudadano(ciudadano):
        return {
            "dni": ciudadano.documento,
            "apellido": ciudadano.apellido,
            "nombre": ciudadano.nombre,
            "fecha_nacimiento": ciudadano.fecha_nacimiento,
            "sexo": getattr(getattr(ciudadano, "sexo", None), "sexo", None),
            "nacionalidad": getattr(
                getattr(ciudadano, "nacionalidad", None), "nacionalidad", None
            ),
            "calle_domicilio": ciudadano.calle,
            "altura_domicilio": (
                int(ciudadano.altura) if str(ciudadano.altura or "").isdigit() else None
            ),
            "provincia_domicilio": ciudadano.provincia_id,
            "municipio_domicilio": ciudadano.municipio_id,
            "localidad_domicilio": ciudadano.localidad_id,
        }

    @staticmethod
    def _resolve_sexo_nombre(sexo_value):
        if not sexo_value:
            return None
        if sexo_value in dict(NominaCentroInfancia.SexoChoices.choices):
            return sexo_value
        sexo_obj = Sexo.objects.filter(pk=sexo_value).first()
        return getattr(sexo_obj, "sexo", None)

    @staticmethod
    def _resolve_nacionalidad_nombre(nacionalidad_value, datos_api=None):
        if nacionalidad_value:
            nacionalidad_obj = Nacionalidad.objects.filter(pk=nacionalidad_value).first()
            if nacionalidad_obj:
                return nacionalidad_obj.nacionalidad
        return (datos_api or {}).get("pais") or None

    @staticmethod
    def _get_selected_ciudadano_from_request(request):
        ciudadano_id = request.GET.get("ciudadano_id") or request.POST.get("ciudadano_id")
        if not str(ciudadano_id or "").isdigit():
            return None
        return Ciudadano.objects.filter(pk=ciudadano_id).first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self._get_centro()
        query = (self.request.GET.get("query") or "").strip()
        form = kwargs.get("form")
        ciudadanos = []
        renaper_data = None
        selected_ciudadano = self._get_selected_ciudadano_from_request(self.request)

        if query and len(query) >= 4:
            ciudadanos = Ciudadano.buscar_por_documento(query, max_results=50)
            if not ciudadanos and query.isdigit() and len(query) >= 7 and not form:
                renaper_result = ComedorService.obtener_datos_ciudadano_desde_renaper(
                    query
                )
                if renaper_result.get("success"):
                    renaper_data = self._build_nomina_initial_from_renaper(
                        renaper_result
                    )
                    mensaje = renaper_result.get("message")
                    if mensaje:
                        messages.info(self.request, mensaje)
                elif renaper_result.get("message"):
                    messages.warning(self.request, renaper_result["message"])

        if not form:
            if selected_ciudadano:
                form = self.form_class(
                    initial=self._build_nomina_initial_from_ciudadano(selected_ciudadano)
                )
            elif renaper_data:
                form = self.form_class(initial=renaper_data)
            elif query and not ciudadanos:
                form = self.form_class(
                    initial={"dni": query if query.isdigit() else None}
                )
            else:
                form = self.form_class()

        context["query"] = query
        context["ciudadanos"] = ciudadanos
        context["selected_ciudadano"] = selected_ciudadano
        context["no_resultados"] = bool(query) and not ciudadanos
        context["form"] = form
        context["renaper_precarga"] = bool(renaper_data) or (
            self.request.POST.get("origen_dato") == "renaper"
        )
        context["mostrar_formulario"] = bool(
            selected_ciudadano or context["no_resultados"] or form.is_bound
        )
        return context

    @staticmethod
    def _parse_fecha_renaper(fecha_raw):
        if not fecha_raw:
            return None
        if isinstance(fecha_raw, date):
            return fecha_raw
        if isinstance(fecha_raw, datetime):
            return fecha_raw.date()

        value = str(fecha_raw).strip()
        formatos = ("%Y-%m-%d", "%d/%m/%Y", "%Y%m%d")
        for fmt in formatos:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue

        try:
            value_iso = value.replace("Z", "")
            return datetime.fromisoformat(value_iso).date()
        except ValueError:
            return None

    @staticmethod
    def _build_nomina_initial_from_renaper(renaper_result):
        renaper_data = dict(renaper_result.get("data") or {})
        datos_api = renaper_result.get("datos_api") or {}
        if not renaper_data:
            return renaper_data

        fecha_raw = renaper_data.get("fecha_nacimiento") or datos_api.get(
            "fechaNacimiento"
        )
        fecha_nacimiento = NominaCentroInfanciaCreateView._parse_fecha_renaper(
            fecha_raw
        )

        return {
            "dni": renaper_data.get("documento") or renaper_data.get("dni"),
            "apellido": renaper_data.get("apellido"),
            "nombre": renaper_data.get("nombre"),
            "fecha_nacimiento": fecha_nacimiento,
            "sexo": NominaCentroInfanciaCreateView._resolve_sexo_nombre(
                renaper_data.get("sexo")
            ),
            "nacionalidad": (
                NominaCentroInfanciaCreateView._resolve_nacionalidad_nombre(
                    renaper_data.get("nacionalidad"),
                    datos_api=datos_api,
                )
            ),
            "calle_domicilio": renaper_data.get("calle"),
            "altura_domicilio": renaper_data.get("altura"),
            "piso_domicilio": renaper_data.get("piso_vivienda"),
            "departamento_domicilio": renaper_data.get("departamento_vivienda"),
            "provincia_domicilio": renaper_data.get("provincia"),
            "municipio_domicilio": renaper_data.get("municipio"),
            "localidad_domicilio": renaper_data.get("localidad"),
        }

    @staticmethod
    def _build_piso_departamento_value(cleaned_data):
        pieces = []
        if cleaned_data.get("piso_domicilio"):
            pieces.append(f'Piso {cleaned_data["piso_domicilio"]}')
        if cleaned_data.get("departamento_domicilio"):
            pieces.append(
                f'Departamento {cleaned_data["departamento_domicilio"]}'
            )
        return " / ".join(pieces) or None

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.form_class(request.POST)
        centro = self._get_centro()
        ciudadano_id = request.POST.get("ciudadano_id")
        origen_dato = request.POST.get("origen_dato") or "manual"

        if not form.is_valid():
            messages.warning(request, "Hay errores en la ficha de la nómina.")
            context = self.get_context_data(form=form)
            return self.render_to_response(context)

        ciudadano = None
        if str(ciudadano_id or "").isdigit():
            ciudadano = Ciudadano.objects.filter(pk=ciudadano_id).first()
            if not ciudadano:
                messages.error(request, "No se encontró el ciudadano seleccionado.")
                context = self.get_context_data(form=form)
                return self.render_to_response(context)

            # Validar que el DNI informado coincida con el del ciudadano seleccionado
            form_dni = form.cleaned_data.get("dni")
            if form_dni and str(form_dni) != str(ciudadano.documento):
                form.add_error(
                    "dni",
                    "El DNI no coincide con el del ciudadano seleccionado.",
                )
                messages.error(
                    request,
                    "El DNI informado no coincide con el del ciudadano seleccionado.",
                )
                context = self.get_context_data(form=form)
                return self.render_to_response(context)
        try:
            with transaction.atomic():
                if ciudadano is None:
                    sexo_obj = Sexo.objects.filter(
                        sexo=form.cleaned_data.get("sexo")
                    ).first()
                    nacionalidad_obj = ComedorService._match_nacionalidad(
                        form.cleaned_data.get("nacionalidad")
                    )
                    ciudadano = Ciudadano.objects.filter(
                        tipo_documento=Ciudadano.DOCUMENTO_DNI,
                        documento=form.cleaned_data.get("dni"),
                    ).first()
                    if ciudadano is None:
                        ciudadano = Ciudadano.objects.create(
                            apellido=form.cleaned_data.get("apellido"),
                            nombre=form.cleaned_data.get("nombre"),
                            fecha_nacimiento=form.cleaned_data.get("fecha_nacimiento"),
                            tipo_documento=Ciudadano.DOCUMENTO_DNI,
                            documento=form.cleaned_data.get("dni"),
                            sexo=sexo_obj,
                            nacionalidad=nacionalidad_obj,
                            calle=form.cleaned_data.get("calle_domicilio"),
                            altura=(
                                str(form.cleaned_data.get("altura_domicilio"))
                                if form.cleaned_data.get("altura_domicilio") is not None
                                else None
                            ),
                            piso_departamento=self._build_piso_departamento_value(
                                form.cleaned_data
                            ),
                            provincia=form.cleaned_data.get("provincia_domicilio"),
                            municipio=form.cleaned_data.get("municipio_domicilio"),
                            localidad=form.cleaned_data.get("localidad_domicilio"),
                            origen_dato=origen_dato,
                            creado_por=request.user,
                            modificado_por=request.user,
                        )

                creado = self._crear_nomina_con_bloqueo(
                    centro=centro,
                    ciudadano=ciudadano,
                    cleaned_data=form.cleaned_data,
                )
        except Exception:  # noqa: BLE001
            logger.exception(
                "Error al guardar ficha en nómina de CDI",
                extra={
                    "centro_id": centro.id,
                    "ciudadano_id": getattr(ciudadano, "id", None),
                    "user_id": getattr(request.user, "id", None),
                },
            )
            messages.error(request, "No se pudo guardar la ficha en la nómina.")
            context = self.get_context_data(form=form)
            return self.render_to_response(context)

        if not creado:
            messages.warning(
                request,
                "El ciudadano ya se encuentra en la nómina de este centro.",
            )
            return redirect(self.get_success_url())

        messages.success(request, "Ficha creada y agregada a la nómina.")
        return redirect(self.get_success_url())


class NominaCentroInfanciaDeleteView(
    SoftDeleteDeleteViewMixin,
    LoginRequiredMixin,
    DeleteView,
):
    model = NominaCentroInfancia
    template_name = "centrodeinfancia/nomina_confirm_delete.html"
    pk_url_kwarg = "pk2"
    success_message = "Registro de nómina dado de baja correctamente."

    def get_queryset(self):
        queryset = _nomina_cdi_queryset_scoped(self.request.user)
        return queryset.filter(centro_id=self.kwargs["pk"])

    def get_success_url(self):
        return reverse("centrodeinfancia_nomina_ver", kwargs={"pk": self.kwargs["pk"]})


@login_required
def nomina_centrodeinfancia_editar_ajax(request, pk):
    nomina = get_object_or_404(_nomina_cdi_queryset_scoped(request.user), pk=pk)
    if request.method == "POST":
        form = NominaCentroInfanciaForm(request.POST, instance=nomina)
        if form.is_valid():
            form.save()
            return JsonResponse(
                {"success": True, "message": "Datos modificados con éxito."}
            )
        return JsonResponse({"success": False, "errors": form.errors})

    form = NominaCentroInfanciaForm(instance=nomina)
    return render(
        request,
        "centrodeinfancia/nomina_editar_ajax.html",
        {"form": form},
    )


class IntervencionCentroInfanciaCreateView(LoginRequiredMixin, CreateView):
    model = IntervencionCentroInfancia
    form_class = IntervencionCentroInfanciaForm
    template_name = "centrodeinfancia/intervencion_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["destinatario_fijo_nombre"] = "Centro"
        kwargs["hide_destinatario"] = True
        return kwargs

    def form_valid(self, form):
        centro = _get_centro_cdi_scoped_or_404(self.request.user, pk=self.kwargs["pk"])
        form.instance.centro = centro
        if form.destinatario_fijo_instance:
            form.instance.destinatario = form.destinatario_fijo_instance
        messages.success(self.request, "Intervención creada correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("centrodeinfancia_detalle", kwargs={"pk": self.kwargs["pk"]})


class IntervencionCentroInfanciaUpdateView(LoginRequiredMixin, UpdateView):
    model = IntervencionCentroInfancia
    form_class = IntervencionCentroInfanciaForm
    pk_url_kwarg = "pk2"
    template_name = "centrodeinfancia/intervencion_form.html"

    def get_queryset(self):
        return _intervenciones_cdi_queryset_scoped(self.request.user).filter(
            centro_id=self.kwargs["pk"]
        )

    def get_success_url(self):
        return reverse("centrodeinfancia_detalle", kwargs={"pk": self.kwargs["pk"]})


class IntervencionCentroInfanciaDeleteView(
    SoftDeleteDeleteViewMixin,
    LoginRequiredMixin,
    DeleteView,
):
    model = IntervencionCentroInfancia
    template_name = "centrodeinfancia/intervencion_confirm_delete.html"
    pk_url_kwarg = "intervencion_id"
    success_message = "Intervención dada de baja correctamente."

    def get_queryset(self):
        return _intervenciones_cdi_queryset_scoped(self.request.user).filter(
            centro_id=self.kwargs["pk"]
        )

    def get_success_url(self):
        return reverse("centrodeinfancia_detalle", kwargs={"pk": self.kwargs["pk"]})


class IntervencionCentroInfanciaDetailView(LoginRequiredMixin, DetailView):
    # TODO: Unificar modelo de intervenciones (Intervencion para comedores e IntervencionCentroInfancia para CDI)
    # para evitar duplicación de vistas y templates de detalle.
    model = IntervencionCentroInfancia
    template_name = "centrodeinfancia/intervencion_detail_view.html"
    context_object_name = "intervencion"

    def get_queryset(self):
        return _intervenciones_cdi_queryset_scoped(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        centro = getattr(self.object, "centro", None)
        if centro:
            context["centro"] = {"id": centro.id, "nombre": centro.nombre}
        return context


class ObservacionCentroInfanciaCreateView(LoginRequiredMixin, CreateView):
    model = ObservacionCentroInfancia
    form_class = ObservacionCentroInfanciaForm
    template_name = "centrodeinfancia/observacion_form.html"
    context_object_name = "observacion"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        centro = _get_centro_cdi_scoped_or_404(self.request.user, pk=self.kwargs["pk"])
        context["centro"] = {"id": centro.id, "nombre": centro.nombre}
        return context

    def form_valid(self, form):
        centro = _get_centro_cdi_scoped_or_404(self.request.user, pk=self.kwargs["pk"])
        form.instance.centro = centro
        usuario = self.request.user
        form.instance.observador = f"{usuario.first_name} {usuario.last_name}".strip()
        if not form.instance.observador:
            form.instance.observador = getattr(usuario, "username", "")
        form.instance.fecha_visita = timezone.now()
        self.object = form.save()
        return safe_redirect(
            self.request,
            default=reverse(
                "centrodeinfancia_observacion_detalle",
                kwargs={"pk": self.object.id},
            ),
        )


class ObservacionCentroInfanciaDetailView(LoginRequiredMixin, DetailView):
    model = ObservacionCentroInfancia
    template_name = "centrodeinfancia/observacion_detail.html"
    context_object_name = "observacion"

    def get_queryset(self):
        return _observaciones_cdi_queryset_scoped(self.request.user)


class ObservacionCentroInfanciaUpdateView(LoginRequiredMixin, UpdateView):
    model = ObservacionCentroInfancia
    form_class = ObservacionCentroInfanciaForm
    template_name = "centrodeinfancia/observacion_form.html"
    context_object_name = "observacion"

    def get_queryset(self):
        return _observaciones_cdi_queryset_scoped(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        centro = getattr(self.object, "centro", None)
        if centro:
            context["centro"] = {"id": centro.id, "nombre": centro.nombre}
        return context

    def form_valid(self, form):
        form.instance.centro = self.object.centro
        self.object = form.save()
        return redirect(
            "centrodeinfancia_observacion_detalle",
            pk=self.object.id,
        )


class ObservacionCentroInfanciaDeleteView(
    SoftDeleteDeleteViewMixin,
    LoginRequiredMixin,
    DeleteView,
):
    model = ObservacionCentroInfancia
    template_name = "centrodeinfancia/observacion_confirm_delete.html"
    context_object_name = "observacion"
    success_message = "Observación dada de baja correctamente."

    def get_queryset(self):
        return _observaciones_cdi_queryset_scoped(self.request.user)

    def get_success_url(self):
        return reverse_lazy(
            "centrodeinfancia_detalle",
            kwargs={"pk": self.object.centro_id},
        )


@login_required
@require_POST
def subir_archivo_intervencion_centrodeinfancia(request, intervencion_id):
    intervencion = get_object_or_404(
        _intervenciones_cdi_queryset_scoped(request.user),
        id=intervencion_id,
    )
    archivo = request.FILES.get("documentacion")
    error = _validar_archivo_documentacion_intervencion(archivo)
    if error:
        return JsonResponse({"success": False, "message": error}, status=400)

    intervencion.documentacion = archivo
    intervencion.tiene_documentacion = True
    intervencion.save(update_fields=["documentacion", "tiene_documentacion"])
    return JsonResponse({"success": True, "message": "Archivo subido correctamente."})


@login_required
@require_POST
def eliminar_archivo_intervencion_centrodeinfancia(request, intervencion_id):
    intervencion = get_object_or_404(
        _intervenciones_cdi_queryset_scoped(request.user),
        id=intervencion_id,
    )
    if intervencion.documentacion:
        intervencion.documentacion.delete(save=False)
        intervencion.documentacion = None
        intervencion.tiene_documentacion = False
        intervencion.save(update_fields=["documentacion", "tiene_documentacion"])
        messages.success(request, "El archivo fue eliminado correctamente.")
    else:
        messages.error(request, "No hay archivo para eliminar.")
    return redirect("centrodeinfancia_detalle", pk=intervencion.centro_id)
