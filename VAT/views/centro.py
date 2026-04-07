from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db import transaction
from django.db.models import Count, Prefetch, Q
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, JsonResponse

from VAT.models import (
    Centro,
    Curso,
    ComisionCurso,
    Comision,
    InstitucionIdentificadorHist,
    InstitucionUbicacion,
    PlanVersionCurricular,
    VoucherParametria,
)
from VAT.cache_utils import get_planes_centro_cache_version
from VAT.services.centro_filter_config import (
    FIELD_MAP as CENTRO_FILTER_MAP,
    FIELD_TYPES as CENTRO_FIELD_TYPES,
    TEXT_OPS as CENTRO_TEXT_OPS,
    NUM_OPS as CENTRO_NUM_OPS,
    BOOL_OPS as CENTRO_BOOL_OPS,
    get_filters_ui_config as get_centro_filters_ui_config,
)
from VAT.forms import (
    CentroAltaForm,
    InstitucionContactoAltaFormSet,
    InstitucionContactoForm,
    InstitucionIdentificadorHistForm,
    InstitucionUbicacionForm,
    CursoForm,
    ComisionCursoForm,
)
from VAT.services.access_scope import (
    can_user_access_centro,
    can_user_add_vat_entities,
    can_user_create_centro,
    can_user_edit_centro,
    filter_centros_queryset_for_user,
    is_vat_referente,
)
from core.models import Localidad
from core.services.advanced_filters import AdvancedFilterEngine
from core.services.favorite_filters import SeccionesFiltrosFavoritos
from core.soft_delete.view_helpers import SoftDeleteDeleteViewMixin


BOOL_ADVANCED_FILTER = AdvancedFilterEngine(
    field_map=CENTRO_FILTER_MAP,
    field_types=CENTRO_FIELD_TYPES,
    allowed_ops={
        "text": CENTRO_TEXT_OPS,
        "number": CENTRO_NUM_OPS,
        "boolean": CENTRO_BOOL_OPS,
    },
)


PLANES_CENTRO_PAGE_SIZE = 5
PLANES_CENTRO_PAGE_SIZE_OPTIONS = (5, 10, 15, 20, 50, 100)
CURSOS_PANEL_CACHE_TTL_SECONDS = 60


def _get_centro_detail_queryset():
    return Centro.objects.select_related(
        "referente",
        "provincia",
        "municipio",
        "localidad",
    )


def _get_localidades_queryset_for_centro(centro):
    queryset = Localidad.objects.order_by("nombre")
    if centro.municipio_id:
        return queryset.filter(municipio_id=centro.municipio_id)
    if centro.provincia_id:
        return queryset.filter(municipio__provincia_id=centro.provincia_id)
    return queryset


def _scope_centro_field_to_current_centro(form, centro):
    centro_field = form.fields.get("centro")
    if centro_field is None:
        return form

    centro_field.queryset = Centro.objects.filter(pk=centro.pk)
    centro_field.initial = centro.pk
    return form


def _build_contacto_form(centro):
    form = InstitucionContactoForm(initial={"centro": centro})
    return _scope_centro_field_to_current_centro(form, centro)


def _build_identificador_form(centro):
    form = InstitucionIdentificadorHistForm(
        initial={"centro": centro, "es_actual": True}
    )
    return _scope_centro_field_to_current_centro(form, centro)


def _build_ubicacion_form(centro):
    form = InstitucionUbicacionForm(initial={"centro": centro})
    form.fields["localidad"].queryset = _get_localidades_queryset_for_centro(centro)
    return _scope_centro_field_to_current_centro(form, centro)


def _parse_planes_centro_page_size(raw_value):
    try:
        page_size = int(raw_value)
    except (TypeError, ValueError):
        return PLANES_CENTRO_PAGE_SIZE

    if page_size in PLANES_CENTRO_PAGE_SIZE_OPTIONS:
        return page_size

    return PLANES_CENTRO_PAGE_SIZE


def _build_planes_centro_queryset(
    centro,
    search_query,
    sector_id=None,
    subsector_id=None,
    modalidad_id=None,
):
    queryset = (
        PlanVersionCurricular.objects.filter(
            activo=True,
            provincia_id=centro.provincia_id,
        )
        .select_related("sector", "subsector", "modalidad_cursada")
        .prefetch_related("titulos")
    )

    if search_query:
        queryset = queryset.filter(
            Q(nombre__icontains=search_query)
            | Q(titulos__nombre__icontains=search_query)
            | Q(sector__nombre__icontains=search_query)
            | Q(subsector__nombre__icontains=search_query)
            | Q(modalidad_cursada__nombre__icontains=search_query)
            | Q(normativa__icontains=search_query)
        ).distinct()

    if sector_id:
        queryset = queryset.filter(sector_id=sector_id)

    if subsector_id:
        queryset = queryset.filter(subsector_id=subsector_id)

    if modalidad_id:
        queryset = queryset.filter(modalidad_cursada_id=modalidad_id)

    return queryset.order_by("sector__nombre", "subsector__nombre", "id")


def _build_planes_centro_cache_key(
    centro,
    search_query,
    page_number,
    sector_id=None,
    subsector_id=None,
    modalidad_id=None,
    page_size=PLANES_CENTRO_PAGE_SIZE,
):
    provincia_key = centro.provincia_id or "sin-provincia"
    normalized_search = (search_query or "").strip().lower()
    sector_key = sector_id or "todos"
    subsector_key = subsector_id or "todos"
    modalidad_key = modalidad_id or "todas"
    cache_version = get_planes_centro_cache_version()
    return (
        "vat:centro:cursos:planes:"
        f"{cache_version}:{provincia_key}:{normalized_search}:{sector_key}:"
        f"{subsector_key}:{modalidad_key}:{page_size}:"
        f"{page_number}:"
        f"{page_size}"
    )


def _get_planes_centro_page(
    centro,
    search_query,
    page_number,
    sector_id=None,
    subsector_id=None,
    modalidad_id=None,
    page_size=PLANES_CENTRO_PAGE_SIZE,
    bypass_cache=False,
):
    normalized_search = (search_query or "").strip()
    normalized_page = page_number or 1
    cache_key = _build_planes_centro_cache_key(
        centro,
        normalized_search,
        normalized_page,
        sector_id,
        subsector_id,
        modalidad_id,
        page_size,
    )
    cached = None if bypass_cache else cache.get(cache_key)

    if cached is not None:
        paginator = Paginator(range(cached["total_count"]), page_size)
        page_obj = paginator.get_page(normalized_page)
        plans_by_id = {
            plan.pk: plan
            for plan in PlanVersionCurricular.objects.filter(pk__in=cached["plan_ids"])
            .select_related("sector", "subsector", "modalidad_cursada")
            .prefetch_related("titulos")
        }
        ordered_plans = [
            plans_by_id[plan_id]
            for plan_id in cached["plan_ids"]
            if plan_id in plans_by_id
        ]
        return ordered_plans, cached["total_count"], page_obj

    queryset = _build_planes_centro_queryset(
        centro,
        normalized_search,
        sector_id,
        subsector_id,
        modalidad_id,
    )
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(normalized_page)
    plans = list(page_obj.object_list)

    cache.set(
        cache_key,
        {
            "plan_ids": [plan.pk for plan in plans],
            "total_count": paginator.count,
        },
        CURSOS_PANEL_CACHE_TTL_SECONDS,
    )
    return plans, paginator.count, page_obj


def _build_cursos_panel_context(request, centro):
    search_query = (request.GET.get("busqueda") or "").strip()
    sector_id_raw = request.GET.get("sector_id")
    subsector_id_raw = request.GET.get("subsector_id")
    modalidad_id_raw = request.GET.get("modalidad_id")
    sector_id = int(sector_id_raw) if sector_id_raw and sector_id_raw.isdigit() else None
    subsector_id = (
        int(subsector_id_raw)
        if subsector_id_raw and subsector_id_raw.isdigit()
        else None
    )
    modalidad_id = (
        int(modalidad_id_raw)
        if modalidad_id_raw and modalidad_id_raw.isdigit()
        else None
    )
    page_size = _parse_planes_centro_page_size(request.GET.get("planes_per_page"))
    page_number = request.GET.get("planes_page") or 1
    planes_queryset = _build_planes_centro_queryset(
        centro,
        search_query,
        sector_id,
        subsector_id,
        modalidad_id,
    )
    planes_centro, total_filtrados, page_obj = _get_planes_centro_page(
        centro,
        search_query,
        page_number,
        sector_id=sector_id,
        subsector_id=subsector_id,
        modalidad_id=modalidad_id,
        page_size=page_size,
        bypass_cache=request.GET.get("refresh") == "1",
    )
    from VAT.models import ModalidadCursada, Sector, Subsector

    sectores = Sector.objects.all().order_by("nombre")
    modalidades = ModalidadCursada.objects.filter(activo=True).order_by("nombre")
    subsectores = Subsector.objects.select_related("sector").order_by(
        "sector__nombre", "nombre"
    )
    if sector_id:
        subsectores = subsectores.filter(sector_id=sector_id)
    elif subsector_id:
        subsectores = subsectores.filter(pk=subsector_id)
    else:
        subsectores = subsectores.none()

    planes_por_sector = list(
        planes_queryset.values("sector__nombre")
        .annotate(total=Count("id"))
        .order_by("sector__nombre")
    )
    planes_query_params = request.GET.copy()
    planes_query_params.pop("planes_page", None)
    planes_query_params.pop("refresh", None)
    cursos = list(
        Curso.objects.filter(centro=centro)
        .select_related("modalidad", "plan_estudio")
        .annotate(comisiones_count=Count("comisiones"))
        .prefetch_related(
            Prefetch(
                "voucher_parametrias",
                queryset=VoucherParametria.objects.select_related("programa").order_by(
                    "nombre"
                ),
            )
        )
        .order_by("-fecha_creacion")
    )
    comisiones_curso = list(
        ComisionCurso.objects.filter(curso__centro=centro)
        .select_related("curso", "ubicacion__localidad")
        .order_by("codigo_comision")
    )
    curso_form = _scope_centro_field_to_current_centro(
        CursoForm(initial={"centro": centro}),
        centro,
    )
    comision_curso_form = ComisionCursoForm()
    comision_curso_form.fields["curso"].queryset = centro.cursos.order_by("nombre")
    comision_curso_form.fields[
        "ubicacion"
    ].queryset = centro.ubicaciones.select_related("localidad").order_by(
        "es_principal",
        "rol_ubicacion",
    )

    return {
        "planes_centro": planes_centro,
        "planes_centro_search_query": search_query,
        "planes_centro_sector_id": int(sector_id) if sector_id else None,
        "planes_centro_subsector_id": int(subsector_id) if subsector_id else None,
        "planes_centro_modalidad_id": int(modalidad_id) if modalidad_id else None,
        "planes_centro_page_size": page_size,
        "planes_centro_page_size_options": PLANES_CENTRO_PAGE_SIZE_OPTIONS,
        "planes_centro_total_filtrados": total_filtrados,
        "planes_centro_page_obj": page_obj,
        "planes_centro_is_paginated": page_obj.has_other_pages(),
        "planes_centro_querystring": planes_query_params.urlencode(),
        "planes_centro_total_sectores": len(planes_por_sector),
        "planes_centro_por_sector": planes_por_sector,
        "cursos": cursos,
        "comisiones_curso": comisiones_curso,
        "curso_form": curso_form,
        "comision_curso_form": comision_curso_form,
        "planes_centro_sectores": sectores,
        "planes_centro_subsectores": subsectores,
        "planes_centro_modalidades": modalidades,
    }


def _build_responsable_principal_data(contacto):
    nombre_completo = (contacto.nombre_contacto or "").strip()
    correo = contacto.email_contacto or ""
    telefono = contacto.telefono_contacto or ""
    return {
        "nombre_contacto": nombre_completo,
        "rol_area": contacto.rol_area or "Responsable institucional",
        "documento": contacto.documento or "",
        "telefono_contacto": telefono,
        "email_contacto": correo,
        "tipo": "email" if correo else "telefono",
        "valor": correo or telefono,
        "es_principal": True,
    }


def _sync_responsable_principal(centro):
    principal = (
        centro.contactos_adicionales.filter(es_principal=True).order_by("id").first()
    )
    if principal is None:
        principal = centro.contactos_adicionales.order_by("id").first()
    if principal is None:
        return None

    defaults = _build_responsable_principal_data(principal)
    for field_name, value in defaults.items():
        setattr(principal, field_name, value)
    principal.save(
        update_fields=[
            "nombre_contacto",
            "rol_area",
            "documento",
            "telefono_contacto",
            "email_contacto",
            "tipo",
            "valor",
            "es_principal",
        ]
    )
    centro.contactos_adicionales.exclude(pk=principal.pk).filter(
        es_principal=True
    ).update(es_principal=False)
    centro.nombre_referente = principal.nombre_contacto or ""
    centro.apellido_referente = ""
    centro.telefono_referente = principal.telefono_contacto or ""
    centro.correo_referente = principal.email_contacto or ""
    centro.save(
        update_fields=[
            "nombre_referente",
            "apellido_referente",
            "telefono_referente",
            "correo_referente",
        ]
    )
    return principal


def _submitted_contact_matches_existing(data, contacto_existente):
    submitted_es_principal = data.get("contactos-0-es_principal") in {
        "1",
        "true",
        "True",
        "on",
    }
    submitted_values = {
        "nombre_contacto": (data.get("contactos-0-nombre_contacto", "") or "").strip(),
        "rol_area": (data.get("contactos-0-rol_area", "") or "").strip(),
        "documento": (data.get("contactos-0-documento", "") or "").strip(),
        "telefono_contacto": (
            data.get("contactos-0-telefono_contacto", "") or ""
        ).strip(),
        "email_contacto": (data.get("contactos-0-email_contacto", "") or "").strip(),
        "es_principal": submitted_es_principal,
    }
    existing_values = {
        "nombre_contacto": (contacto_existente.nombre_contacto or "").strip(),
        "rol_area": (contacto_existente.rol_area or "").strip(),
        "documento": (contacto_existente.documento or "").strip(),
        "telefono_contacto": (contacto_existente.telefono_contacto or "").strip(),
        "email_contacto": (contacto_existente.email_contacto or "").strip(),
        "es_principal": bool(contacto_existente.es_principal),
    }
    return submitted_values == existing_values


class CentroListView(LoginRequiredMixin, ListView):
    model = Centro
    template_name = "vat/centros/centro_list.html"
    context_object_name = "centros"
    paginate_by = 10

    def get_queryset(self):
        base_qs = Centro.objects.select_related("referente").order_by("nombre")

        user = self.request.user
        busq = self.request.GET.get("busqueda", "").strip()
        base_qs = filter_centros_queryset_for_user(base_qs, user)

        if busq:
            base_qs = base_qs.filter(Q(nombre__icontains=busq))

        return BOOL_ADVANCED_FILTER.filter_queryset(base_qs, self.request.GET)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        ctx.update(
            {
                "filters_mode": True,
                "filters_js": "custom/js/advanced_filters.js",
                "filters_action": reverse("vat_centro_list"),
                "filters_config": get_centro_filters_ui_config(),
                "seccion_filtros_favoritos": SeccionesFiltrosFavoritos.VAT_CENTROS,
                "add_url": reverse("vat_centro_create"),
            }
        )

        ctx["can_add"] = can_user_create_centro(user)

        ctx["table_headers"] = [
            {"title": "Nombre", "sortable": True, "sort_key": "nombre"},
            {"title": "Dirección", "sortable": True, "sort_key": "calle"},
            {"title": "Teléfono", "sortable": True, "sort_key": "telefono"},
            {"title": "Estado", "sortable": True, "sort_key": "activo"},
            {"title": "Acciones"},
        ]

        return ctx


class CentroAccessMixin:
    model = Centro
    context_object_name = "centro"

    def get_queryset(self):
        return _get_centro_detail_queryset()

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not can_user_access_centro(self.request.user, obj):
            raise PermissionDenied
        return obj


class CentroDetailView(CentroAccessMixin, LoginRequiredMixin, DetailView):
    template_name = "vat/centros/centro_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        centro = self.object

        # Evaluar listas una sola vez para reutilizar en los counts
        ctx["identificadores"] = list(
            centro.identificadores_hist.select_related("ubicacion__localidad")
            .all()
            .order_by("-es_actual", "-vigencia_desde")
        )
        ctx["contactos"] = list(
            centro.contactos_adicionales.all().order_by(
                "-es_principal", "nombre_contacto"
            )
        )
        ctx["ubicaciones"] = list(centro.ubicaciones.select_related("localidad").all())
        ctx["count_ofertas"] = centro.ofertas_institucionales.count()
        ctx["count_comisiones"] = Comision.objects.filter(
            oferta__centro_id=centro.pk
        ).count()
        ctx["count_cursos"] = Curso.objects.filter(centro_id=centro.pk).count()
        ctx["count_identificadores"] = len(ctx["identificadores"])
        ctx["count_contactos"] = len(ctx["contactos"])

        ctx["contacto_form"] = _build_contacto_form(centro)
        ctx["identificador_form"] = _build_identificador_form(centro)
        ctx["ubicacion_form"] = _build_ubicacion_form(centro)
        ctx["cursos_panel_url"] = reverse(
            "vat_centro_cursos_panel",
            kwargs={"pk": centro.pk},
        )
        ctx["can_edit_centro"] = can_user_edit_centro(self.request.user, centro)

        return ctx


class CentroCursosPanelView(CentroAccessMixin, LoginRequiredMixin, DetailView):
    template_name = "vat/centros/partials/centro_cursos_panel.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_build_cursos_panel_context(self.request, self.object))
        return ctx


class CentroCreateView(LoginRequiredMixin, CreateView):
    model = Centro
    form_class = CentroAltaForm
    template_name = "vat/centros/centro_create_form.html"
    success_url = reverse_lazy("vat_centro_list")

    def _get_creator_provincia(self):
        profile = getattr(self.request.user, "profile", None)
        return getattr(profile, "provincia", None)

    def _should_hide_provincia_field(self):
        return self._get_creator_provincia() is not None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        creator_provincia = self._get_creator_provincia()
        kwargs["hide_provincia"] = self._should_hide_provincia_field()
        kwargs["provincia_inicial"] = creator_provincia

        data = kwargs.get("data")
        if data is not None and creator_provincia is not None:
            data = data.copy()
            data["provincia"] = str(creator_provincia.pk)
            kwargs["data"] = data

        return kwargs

    def dispatch(self, request, *args, **kwargs):
        if not can_user_create_centro(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        contacto_formset = kwargs.get("contacto_formset")
        if contacto_formset is None:
            contacto_formset = InstitucionContactoAltaFormSet(prefix="contactos")
        ctx.update(
            {
                "contacto_formset": contacto_formset,
                "page_title": "Alta de Centro de Formacion",
                "page_description": (
                    "Registro inicial del centro VAT con datos institucionales, "
                    "ubicación y contactos institucionales unificados."
                ),
                "show_provincia_field": not self._should_hide_provincia_field(),
                "cancel_url": reverse("vat_centro_list"),
                "submit_text": "Guardar",
                "submit_continue_text": "Guardar y continuar",
                "show_save_continue": True,
            }
        )
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        creator_provincia = self._get_creator_provincia()
        contacto_formset = InstitucionContactoAltaFormSet(
            self.request.POST,
            prefix="contactos",
        )

        if creator_provincia is not None:
            form.instance.provincia = creator_provincia

        if form.is_valid() and contacto_formset.is_valid():
            return self.form_valid(form, contacto_formset)
        return self.form_invalid(form, contacto_formset)

    def form_valid(self, form, contacto_formset):  # pylint: disable=arguments-differ
        with transaction.atomic():
            form.instance.activo = True
            self.object = form.save()

            contacto_formset.instance = self.object
            contacto_formset.save()
            _sync_responsable_principal(self.object)

            InstitucionIdentificadorHist.objects.create(
                centro=self.object,
                tipo_identificador="cue",
                valor_identificador=form.cleaned_data["codigo"],
                rol_institucional="sede",
                es_actual=True,
            )

            InstitucionUbicacion.objects.create(
                centro=self.object,
                localidad=form.cleaned_data["localidad"],
                rol_ubicacion="sede_principal",
                domicilio=form.cleaned_data["domicilio_actividad"],
                es_principal=True,
            )

        messages.success(self.request, "Centro creado exitosamente.")
        return super().form_valid(form)

    def form_invalid(self, form, contacto_formset):  # pylint: disable=arguments-differ
        return self.render_to_response(
            self.get_context_data(
                form=form,
                contacto_formset=contacto_formset,
            )
        )

    def get_success_url(self):
        if self.request.POST.get("save_continue"):
            return reverse("vat_centro_detail", kwargs={"pk": self.object.pk})
        return super().get_success_url()


class CentroUpdateView(LoginRequiredMixin, UpdateView):
    model = Centro
    form_class = CentroAltaForm
    template_name = "vat/centros/centro_create_form.html"

    def dispatch(self, request, *args, **kwargs):
        centro = self.get_object()
        if not can_user_edit_centro(request.user, centro):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        responsable = (
            self.object.contactos_adicionales.filter(es_principal=True)
            .order_by("id")
            .first()
        )
        if responsable:
            initial["autoridad_dni"] = responsable.documento
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["hide_provincia"] = True
        kwargs["provincia_inicial"] = self.object.provincia

        data = kwargs.get("data")
        if data is not None and self.object.provincia_id is not None:
            data = data.copy()
            data["provincia"] = str(self.object.provincia_id)
            kwargs["data"] = data

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contacto_formset = kwargs.get("contacto_formset")
        if contacto_formset is None:
            contacto_formset = InstitucionContactoAltaFormSet(
                instance=self.object,
                prefix="contactos",
            )
        context.update(
            {
                "contacto_formset": contacto_formset,
                "page_title": "Editar Centro de Formacion",
                "page_description": (
                    "Actualizá los datos institucionales, la ubicación y los "
                    "contactos institucionales del centro VAT."
                ),
                "cancel_url": reverse(
                    "vat_centro_detail", kwargs={"pk": self.object.pk}
                ),
                "submit_text": "Guardar",
                "show_provincia_field": False,
                "show_save_continue": False,
            }
        )
        return context

    def _normalize_contacto_formset_data(self, data):
        if data is None:
            return data, None

        total_forms = int(data.get("contactos-TOTAL_FORMS", 0) or 0)
        initial_forms = int(data.get("contactos-INITIAL_FORMS", 0) or 0)
        if total_forms == 0 or initial_forms != 0:
            return data, None

        if any(data.get(f"contactos-{index}-id") for index in range(total_forms)):
            return data, None

        contactos_existentes = list(self.object.contactos_adicionales.order_by("id"))
        if total_forms == 1 and len(contactos_existentes) == 1:
            contacto_existente = contactos_existentes[0]
            if _submitted_contact_matches_existing(data, contacto_existente):
                normalized_data = data.copy()
                normalized_data["contactos-INITIAL_FORMS"] = "1"
                normalized_data["contactos-0-id"] = str(contacto_existente.pk)
                normalized_data["contactos-0-centro"] = str(self.object.pk)
                return normalized_data, None

        if contactos_existentes:
            return (
                data,
                (
                    "No se pudo guardar la edición de contactos porque faltan los "
                    "identificadores de filas existentes. Recargá la página e intentá "
                    "nuevamente."
                ),
            )

        return data, None

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        mutable_post, contacto_formset_error = self._normalize_contacto_formset_data(
            request.POST
        )
        if mutable_post is not request.POST:
            request.POST = mutable_post
        form = self.get_form()
        contacto_formset = InstitucionContactoAltaFormSet(
            request.POST,
            instance=self.object,
            prefix="contactos",
        )
        form.instance.provincia = self.object.provincia
        if contacto_formset_error:
            form.add_error(None, contacto_formset_error)
        if form.is_valid() and contacto_formset.is_valid():
            return self.form_valid(form, contacto_formset)
        return self.form_invalid(form, contacto_formset)

    def form_valid(self, form, contacto_formset):  # pylint: disable=arguments-differ
        with transaction.atomic():
            was_active = (
                type(self.object)
                .objects.filter(pk=self.object.pk)
                .values_list("activo", flat=True)
                .first()
            )
            centro = form.save(commit=False)
            if not was_active:
                centro.activo = False
            centro.save()
            form.save_m2m()
            self.object = centro

            contacto_formset.instance = self.object
            contacto_formset.save()
            _sync_responsable_principal(self.object)

            ubicacion_principal = (
                self.object.ubicaciones.filter(rol_ubicacion="sede_principal")
                .order_by("-es_principal", "-vigencia_desde", "-id")
                .first()
                or self.object.ubicaciones.order_by(
                    "-es_principal", "-vigencia_desde", "-id"
                ).first()
            )
            if ubicacion_principal is None:
                ubicacion_principal = InstitucionUbicacion(
                    centro=self.object,
                    rol_ubicacion="sede_principal",
                )
            ubicacion_principal.localidad = form.cleaned_data["localidad"]
            ubicacion_principal.domicilio = form.cleaned_data["domicilio_actividad"]
            ubicacion_principal.es_principal = True
            ubicacion_principal.save()

            identificador_cue = (
                self.object.identificadores_hist.filter(tipo_identificador="cue")
                .order_by("-es_actual", "-vigencia_desde", "-id")
                .first()
            )
            if identificador_cue is None:
                identificador_cue = InstitucionIdentificadorHist(
                    centro=self.object,
                    tipo_identificador="cue",
                )
            identificador_cue.valor_identificador = form.cleaned_data["codigo"]
            identificador_cue.rol_institucional = "sede"
            identificador_cue.ubicacion = ubicacion_principal
            identificador_cue.es_actual = True
            identificador_cue.save()

        messages.success(self.request, "Centro actualizado correctamente.")
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, contacto_formset):  # pylint: disable=arguments-differ
        return self.render_to_response(
            self.get_context_data(
                form=form,
                contacto_formset=contacto_formset,
            )
        )

    def get_success_url(self):
        return reverse("vat_centro_detail", kwargs={"pk": self.object.pk})


class CentroDeleteView(SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView):
    model = Centro
    success_url = reverse_lazy("vat_centro_list")
    template_name = "vat/centros/centro_confirm_delete.html"
    success_message = "Centro dado de baja correctamente."

    def dispatch(self, request, *args, **kwargs):
        centro = self.get_object()
        if not (
            can_user_add_vat_entities(request.user)
            or (
                is_vat_referente(request.user)
                and centro.referente_id == request.user.id
            )
        ):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


def centros_ajax(request):
    from django.template.loader import render_to_string

    def _centros_ajax(request):
        query = request.GET.get("busqueda", "")
        page = request.GET.get("page", 1)
        user = request.user

        qs = Centro.objects.select_related("referente")
        qs = filter_centros_queryset_for_user(qs, user)

        busq = query.strip()
        if busq:
            qs = qs.filter(Q(nombre__icontains=busq))

        qs = qs.order_by("nombre")

        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(page)

        can_add = can_user_create_centro(user)

        context = {
            "centros": page_obj,
            "request": request,
            "can_add": can_add,
            "table_headers": [
                {"title": "Nombre", "sortable": True, "sort_key": "nombre"},
                {"title": "Dirección", "sortable": True, "sort_key": "calle"},
                {"title": "Teléfono", "sortable": True, "sort_key": "telefono"},
                {"title": "Estado", "sortable": True, "sort_key": "activo"},
                {"title": "Acciones"},
            ],
        }

        html = render_to_string(
            "vat/partials/centros_rows.html",
            context,
            request=request,
        )

        pagination_html = render_to_string(
            "components/pagination.html",
            {
                "page_obj": page_obj,
                "is_paginated": page_obj.has_other_pages(),
                "query": query,
                "prev_text": "Volver",
                "next_text": "Continuar",
            },
            request=request,
        )

        return JsonResponse(
            {
                "html": html,
                "pagination_html": pagination_html,
                "count": paginator.count,
                "num_pages": paginator.num_pages,
                "has_previous": page_obj.has_previous(),
                "has_next": page_obj.has_next(),
                "current_page": page_obj.number,
            }
        )

    return _centros_ajax(request)
