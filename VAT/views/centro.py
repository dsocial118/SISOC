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
from django.db.models import Count, Q
from django import forms
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, JsonResponse

from VAT.models import (
    AutoridadInstitucional,
    Centro,
    Curso,
    ComisionCurso,
    Comision,
    InstitucionIdentificadorHist,
    InstitucionUbicacion,
    PlanVersionCurricular,
    TituloReferencia,
)
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
    CentroForm,
    InstitucionContactoAltaFormSet,
    InstitucionContactoForm,
    AutoridadInstitucionalForm,
    InstitucionIdentificadorHistForm,
    InstitucionUbicacionForm,
    CursoForm,
    ComisionCursoForm,
    OfertaInstitucionalForm,
    ComisionForm,
    TituloReferenciaForm,
    PlanVersionCurricularForm,
)
from VAT.services.access_scope import (
    can_user_access_centro,
    can_user_add_vat_entities,
    can_user_create_centro,
    can_user_edit_centro,
    filter_centros_queryset_for_user,
    is_vat_referente,
)
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


class CentroDetailView(LoginRequiredMixin, DetailView):
    model = Centro
    template_name = "vat/centros/centro_detail.html"
    context_object_name = "centro"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not can_user_access_centro(self.request.user, obj):
            raise PermissionDenied
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        centro = self.object

        # Evaluar listas una sola vez para reutilizar en los counts
        ctx["autoridades"] = list(
            centro.autoridades.all().order_by("-es_actual", "-vigencia_desde")
        )
        ctx["identificadores"] = list(
            centro.identificadores_hist.select_related("ubicacion")
            .all()
            .order_by("-es_actual", "-vigencia_desde")
        )
        ctx["contactos"] = list(centro.contactos_adicionales.all())
        ctx["ubicaciones"] = centro.ubicaciones.select_related("localidad").all()

        # annotate para evitar N+1 al contar comisiones por oferta
        ctx["ofertas"] = list(
            centro.ofertas_institucionales.select_related("plan_curricular", "programa")
            .annotate(comisiones_count=Count("comisiones"))
            .order_by("-ciclo_lectivo")
        )
        ctx["planes_centro"] = list(
            PlanVersionCurricular.objects.filter(
                activo=True,
                provincia_id=centro.provincia_id,
            )
            .select_related("sector", "subsector", "modalidad_cursada")
            .prefetch_related("titulos")
            .order_by("sector__nombre", "subsector__nombre", "id")
        )
        ctx["comisiones"] = list(
            Comision.objects.filter(oferta__centro=centro)
            .select_related(
                "oferta__plan_curricular",
                "oferta__programa",
            )
            .order_by("codigo_comision")
        )
        ctx["cursos"] = list(
            Curso.objects.filter(centro=centro)
            .select_related("modalidad")
            .prefetch_related("comisiones", "voucher_parametrias")
            .order_by("-fecha_creacion")
        )
        ctx["comisiones_curso"] = list(
            ComisionCurso.objects.filter(curso__centro=centro)
            .select_related("curso", "ubicacion__localidad")
            .order_by("codigo_comision")
        )

        # Todos los counts desde datos ya cargados, sin queries adicionales
        ctx["count_ofertas"] = len(ctx["ofertas"])
        ctx["count_comisiones"] = len(ctx["comisiones"])
        ctx["count_cursos"] = len(ctx["cursos"])
        ctx["count_comisiones_curso"] = len(ctx["comisiones_curso"])
        ctx["count_autoridades"] = len(ctx["autoridades"])
        ctx["count_identificadores"] = len(ctx["identificadores"])
        ctx["count_contactos"] = len(ctx["contactos"])

        # Títulos y planes activos (catálogo disponible)
        ctx["titulos"] = list(
            TituloReferencia.objects.filter(activo=True).select_related(
                "plan_estudio",
                "plan_estudio__sector",
                "plan_estudio__subsector",
                "plan_estudio__modalidad_cursada",
            )
        )
        ctx["planes"] = list(
            PlanVersionCurricular.objects.filter(activo=True)
            .select_related("sector", "subsector", "modalidad_cursada")
            .prefetch_related("titulos")
        )

        # Forms para modales
        ctx["contacto_form"] = InstitucionContactoForm(initial={"centro": centro})
        ctx["autoridad_form"] = AutoridadInstitucionalForm(
            initial={"centro": centro, "es_actual": True}
        )
        ctx["identificador_form"] = InstitucionIdentificadorHistForm(
            initial={"centro": centro, "es_actual": True}
        )
        ctx["ubicacion_form"] = InstitucionUbicacionForm(initial={"centro": centro})
        ctx["oferta_form"] = OfertaInstitucionalForm(initial={"centro": centro})
        ctx["oferta_form"].fields["centro"].queryset = Centro.objects.filter(
            pk=centro.pk
        )
        ctx["oferta_form"].fields["centro"].initial = centro.pk
        ctx["oferta_form"].fields["centro"].widget = forms.HiddenInput()
        ctx["comision_form"] = ComisionForm()
        ctx["comision_form"].fields["oferta"].queryset = (
            centro.ofertas_institucionales.order_by("-ciclo_lectivo")
        )
        ctx["comision_form"].fields["ubicacion"].queryset = (
            centro.ubicaciones.select_related("localidad").order_by(
                "es_principal", "rol_ubicacion"
            )
        )
        ctx["curso_form"] = CursoForm(initial={"centro": centro})
        ctx["comision_curso_form"] = ComisionCursoForm()
        ctx["comision_curso_form"].fields["curso"].queryset = centro.cursos.order_by(
            "nombre"
        )
        ctx["comision_curso_form"].fields["ubicacion"].queryset = (
            centro.ubicaciones.select_related("localidad").order_by(
                "es_principal", "rol_ubicacion"
            )
        )
        ctx["titulo_form"] = TituloReferenciaForm()
        ctx["plan_form"] = PlanVersionCurricularForm()
        ctx["can_edit_centro"] = can_user_edit_centro(self.request.user, centro)

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
                    "ubicación, contactos y autoridad responsable."
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

            AutoridadInstitucional.objects.create(
                centro=self.object,
                nombre_completo=(
                    f"{form.cleaned_data['nombre_referente']} "
                    f"{form.cleaned_data['apellido_referente']}"
                ).strip(),
                dni=form.cleaned_data["autoridad_dni"],
                cargo="Director/a",
                email=form.cleaned_data["correo_referente"],
                telefono=form.cleaned_data.get("telefono_referente"),
                es_actual=True,
            )

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
        autoridad = (
            self.object.autoridades.filter(es_actual=True)
            .order_by("-vigencia_desde", "-id")
            .first()
            or self.object.autoridades.order_by("-vigencia_desde", "-id").first()
        )
        if autoridad:
            initial["autoridad_dni"] = autoridad.dni
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
                    "Actualizá los datos institucionales, la ubicación, los "
                    "contactos y la autoridad responsable del centro VAT."
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

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        contacto_formset = InstitucionContactoAltaFormSet(
            self.request.POST,
            instance=self.object,
            prefix="contactos",
        )
        form.instance.provincia = self.object.provincia
        if form.is_valid() and contacto_formset.is_valid():
            return self.form_valid(form, contacto_formset)
        return self.form_invalid(form, contacto_formset)

    def form_valid(self, form, contacto_formset):  # pylint: disable=arguments-differ
        with transaction.atomic():
            form.instance.activo = self.object.activo
            self.object = form.save()

            contacto_formset.instance = self.object
            contacto_formset.save()

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

            autoridad_actual = (
                self.object.autoridades.filter(es_actual=True)
                .order_by("-vigencia_desde", "-id")
                .first()
                or self.object.autoridades.order_by("-vigencia_desde", "-id").first()
            )
            if autoridad_actual is None:
                autoridad_actual = AutoridadInstitucional(centro=self.object)
            autoridad_actual.nombre_completo = (
                f"{form.cleaned_data['nombre_referente']} "
                f"{form.cleaned_data['apellido_referente']}"
            ).strip()
            autoridad_actual.dni = form.cleaned_data["autoridad_dni"]
            autoridad_actual.cargo = autoridad_actual.cargo or "Director/a"
            autoridad_actual.email = form.cleaned_data["correo_referente"]
            autoridad_actual.telefono = form.cleaned_data.get("telefono_referente")
            autoridad_actual.es_actual = True
            autoridad_actual.save()

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
