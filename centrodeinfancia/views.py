from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.html import escape, format_html, format_html_join
from django.utils.text import Truncator
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from auditlog.models import LogEntry
from datetime import date, datetime
from ciudadanos.models import Ciudadano
from comedores.forms.comedor_form import CiudadanoFormParaNomina, NominaExtraForm
from comedores.services.comedor_service import ComedorService
from core.decorators import group_required
from core.security import safe_redirect
from core.soft_delete_views import SoftDeleteDeleteViewMixin

from centrodeinfancia.forms import (
    CentroDeInfanciaForm,
    IntervencionCentroInfanciaForm,
    NominaCentroInfanciaCreateForm,
    NominaCentroInfanciaForm,
    ObservacionCentroInfanciaForm,
)
from centrodeinfancia.models import (
    CentroDeInfancia,
    IntervencionCentroInfancia,
    NominaCentroInfancia,
    ObservacionCentroInfancia,
)


class CentroDeInfanciaListView(LoginRequiredMixin, ListView):
    model = CentroDeInfancia
    template_name = "centrodeinfancia/centrodeinfancia_list.html"
    context_object_name = "centros"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("busqueda")
        queryset = CentroDeInfancia.objects.select_related("organizacion").order_by(
            "nombre"
        )
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query) | Q(organizacion__nombre__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"text": "Centro de Infancia", "url": reverse("centrodeinfancia")},
            {"text": "Listar", "active": True},
        ]
        context["query"] = self.request.GET.get("busqueda", "")
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


class CentroDeInfanciaDetailView(LoginRequiredMixin, DetailView):
    model = CentroDeInfancia
    template_name = "centrodeinfancia/centrodeinfancia_detail.html"
    context_object_name = "centro"

    def get_queryset(self):
        return CentroDeInfancia.objects.select_related(
            "organizacion", "provincia", "municipio", "localidad"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        nomina_qs = self.object.nominas.select_related("ciudadano").order_by("-fecha")
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
                getattr(getattr(ciudadano, "sexo", None), "sexo", "") or ""
            ).lower()

            if registro.estado == NominaCentroInfancia.ESTADO_PENDIENTE:
                nomina_espera += 1

            if "mascul" in sexo or sexo == "m":
                hombres += 1
            elif "femen" in sexo or sexo == "f":
                mujeres += 1

            fecha_nacimiento = getattr(ciudadano, "fecha_nacimiento", None)
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
                    '<a href="{}" class="btn btn-sm btn-warning">Editar</a>',
                    reverse(
                        "centrodeinfancia_intervencion_editar",
                        args=[self.object.id, intervencion.id],
                    ),
                )
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
        context["intervencion_form"] = IntervencionCentroInfanciaForm()
        context["observacion_form"] = ObservacionCentroInfanciaForm()
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


class CentroDeInfanciaDeleteView(
    SoftDeleteDeleteViewMixin,
    LoginRequiredMixin,
    DeleteView,
):
    model = CentroDeInfancia
    template_name = "centrodeinfancia/centrodeinfancia_confirm_delete.html"
    context_object_name = "centro"
    success_url = reverse_lazy("centrodeinfancia")
    success_message = "Centro de infancia dado de baja correctamente."


@login_required
def centrodeinfancia_ajax(request):
    @group_required(["Centro de Infancia Listar"])
    def _centrodeinfancia_ajax(req):
        query = req.GET.get("busqueda", "")
        page = req.GET.get("page", 1)
        queryset = CentroDeInfancia.objects.select_related("organizacion").order_by(
            "nombre"
        )
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query) | Q(organizacion__nombre__icontains=query)
            )

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page)
        html = render_to_string(
            "centrodeinfancia/partials/rows.html",
            {"centros": page_obj},
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


class NominaCentroInfanciaDetailView(LoginRequiredMixin, ListView):
    model = NominaCentroInfancia
    template_name = "centrodeinfancia/nomina_detail.html"
    context_object_name = "nomina"
    paginate_by = 20

    def get_queryset(self):
        return NominaCentroInfancia.objects.select_related("ciudadano").filter(
            centro_id=self.kwargs["pk"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = get_object_or_404(CentroDeInfancia, pk=self.kwargs["pk"])
        return context


class NominaCentroInfanciaCreateView(LoginRequiredMixin, CreateView):
    model = NominaCentroInfancia
    form_class = NominaCentroInfanciaCreateForm
    template_name = "centrodeinfancia/nomina_form.html"

    def get_success_url(self):
        return reverse("centrodeinfancia_nomina_ver", kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = get_object_or_404(CentroDeInfancia, pk=self.kwargs["pk"])
        query = (self.request.GET.get("query") or "").strip()
        form_ciudadano = kwargs.get("form_ciudadano")
        ciudadanos = []
        renaper_data = None

        if query and len(query) >= 4:
            ciudadanos = Ciudadano.buscar_por_documento(query, max_results=50)
            if (
                not ciudadanos
                and query.isdigit()
                and len(query) >= 7
                and not form_ciudadano
            ):
                renaper_result = ComedorService.obtener_datos_ciudadano_desde_renaper(
                    query
                )
                if renaper_result.get("success"):
                    renaper_data = self._prepare_renaper_initial_data(renaper_result)
                    mensaje = renaper_result.get("message")
                    if mensaje:
                        messages.info(self.request, mensaje)
                elif renaper_result.get("message"):
                    messages.warning(self.request, renaper_result["message"])

        if not form_ciudadano:
            if renaper_data:
                form_ciudadano = CiudadanoFormParaNomina(initial=renaper_data)
            else:
                form_ciudadano = CiudadanoFormParaNomina()

        renaper_precarga = bool(renaper_data) or (
            self.request.POST.get("origen_dato") == "renaper"
        )

        context["query"] = query
        context["ciudadanos"] = ciudadanos
        context["no_resultados"] = bool(query) and not ciudadanos
        context["estados"] = NominaCentroInfancia.ESTADO_CHOICES
        context["form_ciudadano"] = form_ciudadano
        context["form_nomina_extra"] = (
            kwargs.get("form_nomina_extra") or NominaExtraForm()
        )
        context["renaper_precarga"] = renaper_precarga
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
    def _prepare_renaper_initial_data(renaper_result):
        renaper_data = dict(renaper_result.get("data") or {})
        if not renaper_data:
            return renaper_data

        fecha_raw = renaper_data.get("fecha_nacimiento")
        if not fecha_raw:
            datos_api = renaper_result.get("datos_api") or {}
            fecha_raw = datos_api.get("fechaNacimiento")

        if fecha_raw:
            parsed_fecha = NominaCentroInfanciaCreateView._parse_fecha_renaper(
                fecha_raw
            )
            if parsed_fecha:
                renaper_data["fecha_nacimiento"] = parsed_fecha.isoformat()

        return renaper_data

    def post(self, request, *args, **kwargs):
        self.object = None
        ciudadano_id = request.POST.get("ciudadano_id")

        if ciudadano_id:
            form_nomina_extra = NominaExtraForm(request.POST)
            if not form_nomina_extra.is_valid():
                messages.error(
                    request, "Datos inválidos para agregar ciudadano a la nómina."
                )
                context = self.get_context_data()
                return self.render_to_response(context)

            estado = form_nomina_extra.cleaned_data.get("estado")
            observaciones = form_nomina_extra.cleaned_data.get("observaciones", "")

            ciudadano = Ciudadano.objects.filter(pk=ciudadano_id).first()
            if not ciudadano:
                messages.error(request, "No se encontró el ciudadano seleccionado.")
                context = self.get_context_data()
                return self.render_to_response(context)

            centro = get_object_or_404(CentroDeInfancia, pk=self.kwargs["pk"])
            existente = NominaCentroInfancia.objects.filter(
                centro=centro,
                ciudadano=ciudadano,
                deleted_at__isnull=True,
            ).exists()
            if existente:
                messages.warning(
                    request,
                    "El ciudadano ya se encuentra en la nómina de este centro.",
                )
                return redirect(self.get_success_url())

            NominaCentroInfancia.objects.create(
                centro=centro,
                ciudadano=ciudadano,
                estado=estado,
                observaciones=observaciones,
            )
            messages.success(request, "Persona agregada a la nómina.")
            return redirect(self.get_success_url())

        form_ciudadano = CiudadanoFormParaNomina(request.POST)
        form_nomina_extra = NominaExtraForm(request.POST)

        if form_ciudadano.is_valid() and form_nomina_extra.is_valid():
            estado = form_nomina_extra.cleaned_data.get("estado")
            observaciones = form_nomina_extra.cleaned_data.get("observaciones")
            centro = get_object_or_404(CentroDeInfancia, pk=self.kwargs["pk"])

            try:
                with transaction.atomic():
                    ciudadano = form_ciudadano.save(commit=False)
                    if request.POST.get("origen_dato") == "renaper":
                        ciudadano.origen_dato = "renaper"
                    ciudadano.creado_por = request.user
                    ciudadano.modificado_por = request.user
                    ciudadano.save()

                    NominaCentroInfancia.objects.create(
                        centro=centro,
                        ciudadano=ciudadano,
                        estado=estado,
                        observaciones=observaciones,
                    )
            except Exception as exc:  # noqa: BLE001
                messages.error(
                    request,
                    f"No se pudo crear el ciudadano y agregarlo a la nómina: {exc}",
                )
                context = self.get_context_data(
                    form_ciudadano=form_ciudadano,
                    form_nomina_extra=form_nomina_extra,
                )
                return self.render_to_response(context)

            messages.success(request, "Ciudadano creado y agregado a la nómina.")
            return redirect(self.get_success_url())

        messages.warning(request, "Errores en el formulario de ciudadano.")
        context = self.get_context_data(
            form_ciudadano=form_ciudadano,
            form_nomina_extra=form_nomina_extra,
        )
        return self.render_to_response(context)


class NominaCentroInfanciaDeleteView(
    SoftDeleteDeleteViewMixin,
    LoginRequiredMixin,
    DeleteView,
):
    model = NominaCentroInfancia
    template_name = "centrodeinfancia/nomina_confirm_delete.html"
    pk_url_kwarg = "pk2"
    success_message = "Registro de nómina dado de baja correctamente."

    def get_success_url(self):
        return reverse("centrodeinfancia_nomina_ver", kwargs={"pk": self.kwargs["pk"]})


def nomina_centrodeinfancia_editar_ajax(request, pk):
    nomina = get_object_or_404(NominaCentroInfancia, pk=pk)
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

    def form_valid(self, form):
        form.instance.centro_id = self.kwargs["pk"]
        messages.success(self.request, "Intervención creada correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("centrodeinfancia_detalle", kwargs={"pk": self.kwargs["pk"]})


class IntervencionCentroInfanciaUpdateView(LoginRequiredMixin, UpdateView):
    model = IntervencionCentroInfancia
    form_class = IntervencionCentroInfanciaForm
    pk_url_kwarg = "pk2"
    template_name = "centrodeinfancia/intervencion_form.html"

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

    def get_success_url(self):
        return reverse("centrodeinfancia_detalle", kwargs={"pk": self.kwargs["pk"]})


class ObservacionCentroInfanciaCreateView(LoginRequiredMixin, CreateView):
    model = ObservacionCentroInfancia
    form_class = ObservacionCentroInfanciaForm
    template_name = "centrodeinfancia/observacion_form.html"
    context_object_name = "observacion"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["centro"] = get_object_or_404(
            CentroDeInfancia.objects.values("id", "nombre"),
            pk=self.kwargs["pk"],
        )
        return context

    def form_valid(self, form):
        form.instance.centro_id = self.kwargs["pk"]
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


class ObservacionCentroInfanciaUpdateView(LoginRequiredMixin, UpdateView):
    model = ObservacionCentroInfancia
    form_class = ObservacionCentroInfanciaForm
    template_name = "centrodeinfancia/observacion_form.html"
    context_object_name = "observacion"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        centro = getattr(self.object, "centro", None)
        if centro:
            context["centro"] = {"id": centro.id, "nombre": centro.nombre}
        return context

    def form_valid(self, form):
        form.instance.centro = self.object.centro
        usuario = self.request.user
        form.instance.observador = f"{usuario.first_name} {usuario.last_name}".strip()
        if not form.instance.observador:
            form.instance.observador = getattr(usuario, "username", "")
        form.instance.fecha_visita = timezone.now()
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

    def get_success_url(self):
        return reverse_lazy(
            "centrodeinfancia_detalle",
            kwargs={"pk": self.object.centro_id},
        )


@login_required
@require_POST
def subir_archivo_intervencion_centrodeinfancia(request, intervencion_id):
    intervencion = get_object_or_404(IntervencionCentroInfancia, id=intervencion_id)
    if request.method == "POST" and request.FILES.get("documentacion"):
        intervencion.documentacion = request.FILES["documentacion"]
        intervencion.tiene_documentacion = True
        intervencion.save()
        return JsonResponse(
            {"success": True, "message": "Archivo subido correctamente."}
        )
    return JsonResponse({"success": False, "message": "No se proporcionó un archivo."})


@login_required
@require_POST
def eliminar_archivo_intervencion_centrodeinfancia(request, intervencion_id):
    intervencion = get_object_or_404(IntervencionCentroInfancia, id=intervencion_id)
    if intervencion.documentacion:
        intervencion.documentacion.delete()
        intervencion.tiene_documentacion = False
        intervencion.save()
        messages.success(request, "El archivo fue eliminado correctamente.")
    else:
        messages.error(request, "No hay archivo para eliminar.")
    return redirect("centrodeinfancia_detalle", pk=intervencion.centro_id)
