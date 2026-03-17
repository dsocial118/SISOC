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
from django.db.models import Q, Count, F, ExpressionWrapper, IntegerField
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import JsonResponse

from django.utils import timezone

from VAT.models import (
    Centro,
    ActividadCentro,
    Encuentro,
    ParticipanteActividad,
)
from VAT.services.centro_filter_config import (
    FIELD_MAP as CENTRO_FILTER_MAP,
    FIELD_TYPES as CENTRO_FIELD_TYPES,
    TEXT_OPS as CENTRO_TEXT_OPS,
    NUM_OPS as CENTRO_NUM_OPS,
    BOOL_OPS as CENTRO_BOOL_OPS,
    get_filters_ui_config as get_centro_filters_ui_config,
)
from VAT.forms import CentroForm
from core.services.advanced_filters import AdvancedFilterEngine
from core.services.favorite_filters import SeccionesFiltrosFavoritos
from core.soft_delete.view_helpers import SoftDeleteDeleteViewMixin
from iam.services import user_has_permission_code


BOOL_ADVANCED_FILTER = AdvancedFilterEngine(
    field_map=CENTRO_FILTER_MAP,
    field_types=CENTRO_FIELD_TYPES,
    allowed_ops={
        "text": CENTRO_TEXT_OPS,
        "number": CENTRO_NUM_OPS,
        "boolean": CENTRO_BOOL_OPS,
    },
)


ROLE_VAT_SSE_PERMISSION = "auth.role_vat_sse"
ROLE_REFERENTE_CENTRO_PERMISSION = "auth.role_referentecentrovat"


def _has_permission(user, permission_code):
    return user_has_permission_code(user, permission_code)


class CentroListView(LoginRequiredMixin, ListView):
    model = Centro
    template_name = "vat/centros/centro_list.html"
    context_object_name = "centros"
    paginate_by = 10

    def get_queryset(self):
        base_qs = Centro.objects.select_related("referente").order_by("nombre")

        user = self.request.user
        busq = self.request.GET.get("busqueda", "").strip()

        if user.is_superuser or _has_permission(user, ROLE_VAT_SSE_PERMISSION):
            pass
        elif _has_permission(user, ROLE_REFERENTE_CENTRO_PERMISSION):
            base_qs = base_qs.filter(referente=user)
        else:
            return Centro.objects.none()

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

        ctx["can_add"] = user.is_superuser or _has_permission(
            user, ROLE_VAT_SSE_PERMISSION
        )

        ctx["table_headers"] = [
            {"title": "Nombre", "sortable": True, "sort_key": "nombre"},
            {"title": "Dirección", "sortable": True, "sort_key": "calle"},
            {"title": "Teléfono", "sortable": True, "sort_key": "telefono"},
            {"title": "Estado", "sortable": True, "sort_key": "activo"},
            {"title": "Acciones"},
        ]

        if ctx["can_add"]:
            ctx["centro_additional_buttons"] = [
                {
                    "url": reverse("vat_actividad_create_sola"),
                    "label": "Agregar Actividad",
                    "class": "btn btn-primary btn-lg text-white text-nowrap",
                },
            ]

        return ctx


class CentroDetailView(LoginRequiredMixin, DetailView):
    model = Centro
    template_name = "vat/centros/centro_detail.html"
    context_object_name = "centro"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        es_ref = obj.referente_id == user.id
        es_vat_sse = _has_permission(user, ROLE_VAT_SSE_PERMISSION)
        if not (es_ref or user.is_superuser or es_vat_sse):
            raise PermissionDenied
        return obj

    def get_context_data(self, **kwargs):  # pylint: disable=too-many-locals
        ctx = super().get_context_data(**kwargs)
        centro = self.object

        search_curso = (
            self.request.GET.get("search_actividades_curso", "").strip().lower()
        )
        qs_acts = (
            ActividadCentro.objects.filter(centro=centro)
            .select_related("actividad", "actividad__categoria")
            .annotate(
                inscritos=Count("participanteactividad", distinct=True),
                ganancia=ExpressionWrapper(
                    F("precio") * F("inscritos"), output_field=IntegerField()
                ),
            )
        )
        if search_curso:
            qs_acts = qs_acts.filter(
                Q(actividad__nombre__icontains=search_curso)
                | Q(actividad__categoria__nombre__icontains=search_curso)
                | Q(estado__icontains=search_curso)
            )

        ctx["actividades"] = list(qs_acts)

        page_curso = self.request.GET.get("page_actividades_curso", 1)
        ctx["actividades_curso_paginadas"] = Paginator(
            qs_acts.order_by("actividad__nombre", "id"), 5
        ).get_page(page_curso)

        ctx["search_actividades_curso_val"] = self.request.GET.get(
            "search_actividades_curso", ""
        )
        ctx["total_actividades"] = qs_acts.count()
        ctx["total_recaudado"] = sum((act.ganancia or 0) for act in ctx["actividades"])

        qs_inscritos = ParticipanteActividad.objects.filter(
            estado="inscrito", actividad_centro__centro=centro
        )
        hombres = qs_inscritos.filter(ciudadano__sexo__sexo__iexact="Masculino").count()
        mujeres = qs_inscritos.filter(ciudadano__sexo__sexo__iexact="Femenino").count()
        espera = ParticipanteActividad.objects.filter(
            estado="lista_espera", actividad_centro__centro=centro
        ).count()

        # Próximo encuentro por actividad (sin N+1)
        today = timezone.now().date()
        proximos_list = list(
            Encuentro.objects.filter(
                actividad_centro__centro=centro,
                estado="programado",
                fecha__gte=today,
            )
            .order_by("actividad_centro_id", "fecha")
            .values("actividad_centro_id", "id", "fecha", "numero_encuentro")
        )
        proximos_map = {}
        for enc in proximos_list:
            proximos_map.setdefault(enc["actividad_centro_id"], enc)

        # Enriquecer cada actividad con su próximo encuentro
        for act in ctx["actividades"]:
            act.proximo_encuentro = proximos_map.get(act.id)

        total_encuentros_programados = Encuentro.objects.filter(
            actividad_centro__centro=centro, estado="programado"
        ).count()

        inscriptos_count = qs_inscritos.count()
        ctx["metricas"] = {
            "actividades": ctx["total_actividades"],
            "inscriptos": inscriptos_count,
            "espera": espera,
            "encuentros_proximos": total_encuentros_programados,
            "recaudacion": ctx["total_recaudado"],
            "hombres": hombres,
            "mujeres": mujeres,
        }

        estado_counts = {"en_curso": 0, "planificada": 0, "finalizada": 0}
        for act in ctx["actividades"]:
            key = act.estado if act.estado in estado_counts else "finalizada"
            estado_counts[key] += 1
        ctx["estado_counts"] = estado_counts

        return ctx


class CentroCreateView(LoginRequiredMixin, CreateView):
    model = Centro
    form_class = CentroForm
    template_name = "vat/centros/centro_form.html"
    success_url = reverse_lazy("vat_centro_list")

    def form_valid(self, form):
        messages.success(self.request, "Centro creado exitosamente.")
        return super().form_valid(form)


class CentroUpdateView(LoginRequiredMixin, UpdateView):
    model = Centro
    form_class = CentroForm
    template_name = "vat/centros/centro_form.html"

    def dispatch(self, request, *args, **kwargs):
        centro = self.get_object()
        user = request.user
        es_vat_sse = _has_permission(user, ROLE_VAT_SSE_PERMISSION)
        if not (centro.referente_id == user.id or user.is_superuser or es_vat_sse):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Centro actualizado correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("vat_centro_detail", kwargs={"pk": self.object.pk})


class CentroDeleteView(SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView):
    model = Centro
    success_url = reverse_lazy("vat_centro_list")
    template_name = "vat/centros/centro_confirm_delete.html"
    success_message = "Centro dado de baja correctamente."

    def dispatch(self, request, *args, **kwargs):
        centro = self.get_object()
        user = request.user
        es_vat_sse = _has_permission(user, ROLE_VAT_SSE_PERMISSION)
        if not (centro.referente_id == user.id or user.is_superuser or es_vat_sse):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


def centros_ajax(request):
    from django.template.loader import render_to_string

    def _centros_ajax(request):
        query = request.GET.get("busqueda", "")
        page = request.GET.get("page", 1)
        user = request.user

        qs = Centro.objects.select_related("referente")

        if user.is_superuser:
            pass
        elif _has_permission(user, ROLE_VAT_SSE_PERMISSION):
            pass
        elif _has_permission(user, ROLE_REFERENTE_CENTRO_PERMISSION):
            qs = qs.filter(referente=user)
        else:
            qs = Centro.objects.none()

        busq = query.strip()
        if busq:
            qs = qs.filter(Q(nombre__icontains=busq))

        qs = qs.order_by("nombre")

        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(page)

        can_add = user.is_superuser or _has_permission(user, ROLE_VAT_SSE_PERMISSION)

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
