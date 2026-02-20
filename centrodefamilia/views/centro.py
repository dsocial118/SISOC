# centrodefamilia/views/centro.py
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
from django.shortcuts import get_object_or_404
from django.http import Http404

from centrodefamilia.models import (
    CabalArchivo,
    Categoria,
    Centro,
    ActividadCentro,
    InformeCabalRegistro,
    ParticipanteActividad,
)
from centrodefamilia.services.centro_filter_config import (
    FIELD_MAP as CENTRO_FILTER_MAP,
    FIELD_TYPES as CENTRO_FIELD_TYPES,
    TEXT_OPS as CENTRO_TEXT_OPS,
    NUM_OPS as CENTRO_NUM_OPS,
    BOOL_OPS as CENTRO_BOOL_OPS,
    get_filters_ui_config as get_centro_filters_ui_config,
)
from centrodefamilia.forms import CentroForm
from core.services.advanced_filters import AdvancedFilterEngine
from core.services.favorite_filters import SeccionesFiltrosFavoritos
from core.soft_delete_views import SoftDeleteDeleteViewMixin


BOOL_ADVANCED_FILTER = AdvancedFilterEngine(
    field_map=CENTRO_FILTER_MAP,
    field_types=CENTRO_FIELD_TYPES,
    allowed_ops={
        "text": CENTRO_TEXT_OPS,
        "number": CENTRO_NUM_OPS,
        "boolean": CENTRO_BOOL_OPS,
    },
)


class CentroListView(LoginRequiredMixin, ListView):
    model = Centro
    template_name = "centros/centro_list.html"
    context_object_name = "centros"
    paginate_by = 10

    def get_queryset(self):
        base_qs = Centro.objects.select_related("faro_asociado", "referente").order_by(
            "nombre"
        )

        user = self.request.user
        busq = self.request.GET.get("busqueda", "").strip()

        if user.is_superuser or user.groups.filter(name="CDF SSE").exists():
            pass
        elif user.groups.filter(name="ReferenteCentro").exists():
            base_qs = base_qs.filter(referente=user)
        else:
            return Centro.objects.none()

        if busq:
            base_qs = base_qs.filter(
                Q(nombre__icontains=busq) | Q(tipo__icontains=busq)
            )

        return BOOL_ADVANCED_FILTER.filter_queryset(base_qs, self.request.GET)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        # Configuracion de la barra de busqueda
        ctx.update(
            {
                "filters_mode": True,
                "filters_js": "custom/js/advanced_filters.js",
                "filters_action": reverse("centro_list"),
                "filters_config": get_centro_filters_ui_config(),
                "seccion_filtros_favoritos": SeccionesFiltrosFavoritos.CDF_CENTROS,
                "add_url": reverse("centro_create"),
            }
        )

        ctx["can_add"] = (
            user.is_superuser or user.groups.filter(name="CDF SSE").exists()
        )

        ctx["table_headers"] = [
            {"title": "Nombre", "sortable": True, "sort_key": "nombre"},
            {"title": "Tipo", "sortable": True, "sort_key": "tipo"},
            {"title": "Dirección", "sortable": True, "sort_key": "calle"},
            {"title": "Teléfono", "sortable": True, "sort_key": "telefono"},
            {"title": "Estado", "sortable": True, "sort_key": "activo"},
            {"title": "Acciones"},
        ]

        if ctx["can_add"]:
            ctx["centro_additional_buttons"] = [
                {
                    "url": reverse("actividad_create_sola"),
                    "label": "Agregar Actividad",
                    "class": "btn btn-primary btn-lg text-white text-nowrap",
                },
                {
                    "url": reverse("informecabal_list"),
                    "label": "Procesar Informe Cabal",
                    "class": "btn btn-info btn-lg text-white text-nowrap",
                    "id": "btn-cabal",
                },
            ]

        return ctx


class CentroDetailView(LoginRequiredMixin, DetailView):
    model = Centro
    template_name = "centros/centro_detail.html"
    context_object_name = "centro"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        es_ref = obj.referente_id == user.id
        es_adherido = (
            obj.tipo == "adherido"
            and obj.faro_asociado
            and obj.faro_asociado.referente_id == user.id
        )
        es_cdf_sse = user.groups.filter(name="CDF SSE").exists()
        if not (es_ref or es_adherido or user.is_superuser or es_cdf_sse):
            raise PermissionDenied
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        centro = self.object

        # 2) Actividades en curso
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

        # Mantengo tu lista para métricas
        ctx["actividades"] = list(qs_acts)

        # ✅ Paginación con orden estable (nombre + id como desempate)
        page_curso = self.request.GET.get("page_actividades_curso", 1)
        ctx["actividades_curso_paginadas"] = Paginator(
            qs_acts.order_by("actividad__nombre", "id"), 5
        ).get_page(page_curso)

        # (opcional, por comodidad en el template)
        ctx["search_actividades_curso_val"] = self.request.GET.get(
            "search_actividades_curso", ""
        )
        ctx["total_actividades"] = qs_acts.count()
        ctx["total_recaudado"] = sum((act.ganancia or 0) for act in ctx["actividades"])

        # 3) Actividades de otros centros
        search_otras = self.request.GET.get("search_actividades", "").strip().lower()
        otras = (
            ActividadCentro.objects.exclude(centro=centro).select_related(
                "actividad", "actividad__categoria", "centro"
            )
            # ✅ Orden estable para evitar UnorderedObjectListWarning
            .order_by("centro__nombre", "actividad__nombre", "id")
        )
        if search_otras:
            otras = (
                otras.filter(
                    Q(actividad__nombre__icontains=search_otras)
                    | Q(actividad__categoria__nombre__icontains=search_otras)
                    | Q(estado__icontains=search_otras)
                    | Q(centro__nombre__icontains=search_otras)
                )
                # ✅ Mantener el mismo orden tras el filtro (por claridad)
                .order_by("centro__nombre", "actividad__nombre", "id")
            )

        ctx["actividades_paginados"] = Paginator(otras, 5).get_page(
            self.request.GET.get("page_act")
        )

        # 4) Centros adheridos
        if centro.tipo == "faro":
            adheridos = Centro.objects.filter(
                faro_asociado=centro, activo=True
            ).order_by("nombre")
        else:
            adheridos = Centro.objects.none()
        ctx["centros_adheridos_paginados"] = Paginator(adheridos, 5).get_page(
            self.request.GET.get("page")
        )
        ctx["centros_adheridos_total"] = adheridos.count()

        total_part = sum(a.inscritos for a in qs_acts)
        qs_inscritos = ParticipanteActividad.objects.filter(
            estado="inscrito", actividad_centro__centro=centro
        )
        hombres = qs_inscritos.filter(ciudadano__sexo__sexo__iexact="Masculino").count()
        mujeres = qs_inscritos.filter(ciudadano__sexo__sexo__iexact="Femenino").count()
        mixtas = total_part - hombres - mujeres
        espera = ParticipanteActividad.objects.filter(
            estado="lista_espera", actividad_centro__centro=centro
        ).count()

        ctx["metricas"] = {
            "centros_faro": ctx["centros_adheridos_total"],
            "categorias": Categoria.objects.count(),
            "actividades": ctx["total_actividades"],
            "interacciones": total_part,
            "inscriptos": qs_inscritos.count(),
            "hombres": hombres,
            "mujeres": mujeres,
            "mixtas": mixtas,
        }
        ctx["asistentes"] = {
            "total": total_part,
            "hombres": hombres,
            "mujeres": mujeres,
            "espera": espera,
        }

        # 6) Archivos CABAL vinculados al centro
        ctx["archivos_cabal_centro"] = (
            CabalArchivo.objects.filter(registros__centro=centro)
            .distinct()
            .order_by("-fecha_subida")
        )

        return ctx


class CentroCreateView(LoginRequiredMixin, CreateView):
    model = Centro
    form_class = CentroForm
    template_name = "centros/centro_form.html"
    success_url = reverse_lazy("centro_list")

    def get_initial(self):
        initial = super().get_initial()
        faro_id = self.request.GET.get("faro")
        if faro_id:
            initial["tipo"] = "adherido"
            initial["faro_asociado"] = faro_id
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["from_faro"] = bool(self.request.GET.get("faro"))
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        if form.cleaned_data.get("tipo") == "adherido":
            form.instance.faro_asociado_id = self.request.GET.get("faro")
        messages.success(self.request, "Centro creado exitosamente.")
        return super().form_valid(form)


class CentroUpdateView(LoginRequiredMixin, UpdateView):
    model = Centro
    form_class = CentroForm
    template_name = "centros/centro_form.html"

    def dispatch(self, request, *args, **kwargs):
        centro = self.get_object()
        user = request.user
        es_cdf_sse = user.groups.filter(name="CDF SSE").exists()
        if not (centro.referente_id == user.id or user.is_superuser or es_cdf_sse):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Centro actualizado correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("centro_detail", kwargs={"pk": self.object.pk})


class CentroDeleteView(SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView):
    model = Centro
    success_url = reverse_lazy("centro_list")
    template_name = "centros/centro_confirm_delete.html"
    success_message = "Centro dado de baja correctamente."

    def dispatch(self, request, *args, **kwargs):
        centro = self.get_object()
        user = request.user
        es_cdf_sse = user.groups.filter(name="CDF SSE").exists()
        if not (centro.referente_id == user.id or user.is_superuser or es_cdf_sse):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)



class InformeCabalArchivoPorCentroDetailView(LoginRequiredMixin, DetailView):
    model = CabalArchivo
    template_name = "informecabal/archivo_por_centro.html"
    context_object_name = "archivo"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        centro_id_raw = self.kwargs.get("centro_id")

        try:
            centro_id = int(centro_id_raw)
        except (TypeError, ValueError):
            raise Http404("Parámetro 'centro_id' inválido.")

        centro = get_object_or_404(Centro, id=centro_id)

        registros_qs = (
            InformeCabalRegistro.objects.filter(
                archivo=self.object, centro_id=centro_id
            )
            .only(
                "id",
                "nro_comercio",
                "razon_social",
                "importe",
                "fecha_trx",
                "moneda_origen",
                "importe_pesos",
                "motivo_rechazo",
                "desc_motivo_rechazo",
                "no_coincidente",
                "fila_numero",
                "centro_id",
            )
            .order_by("fila_numero")
        )

        paginator = Paginator(registros_qs, 50)
        page_param = self.request.GET.get("page") or 1
        try:
            page_obj = paginator.get_page(page_param)
        except Exception:
            page_obj = paginator.get_page(1)

        context["registros"] = page_obj
        context["centro"] = centro
        return context


def centros_ajax(request):
    """Endpoint AJAX para búsqueda filtrada de Centros de Familia"""
    from django.template.loader import render_to_string
    from django.core.paginator import Paginator
    from django.http import JsonResponse
    from core.decorators import group_required

    def _centros_ajax(request):
        query = request.GET.get("busqueda", "")
        page = request.GET.get("page", 1)
        user = request.user

        qs = Centro.objects.select_related("faro_asociado", "referente")

        if user.is_superuser:
            pass
        elif user.groups.filter(name="CDF SSE").exists():
            pass
        elif user.groups.filter(name="ReferenteCentro").exists():
            qs = qs.filter(referente=user)
        else:
            qs = Centro.objects.none()

        busq = query.strip()
        if busq:
            qs = qs.filter(Q(nombre__icontains=busq) | Q(tipo__icontains=busq))

        qs = qs.order_by("nombre")

        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(page)

        can_add = user.is_superuser or user.groups.filter(name="CDF SSE").exists()

        context = {
            "centros": page_obj,
            "request": request,
            "can_add": can_add,
            "table_headers": [
                {"title": "Nombre", "sortable": True, "sort_key": "nombre"},
                {"title": "Tipo", "sortable": True, "sort_key": "tipo"},
                {"title": "Dirección", "sortable": True, "sort_key": "calle"},
                {"title": "Teléfono", "sortable": True, "sort_key": "telefono"},
                {"title": "Estado", "sortable": True, "sort_key": "activo"},
                {"title": "Acciones"},
            ],
        }

        html = render_to_string(
            "partials/centros_rows.html",
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
