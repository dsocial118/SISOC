from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from core.soft_delete.view_helpers import SoftDeleteDeleteViewMixin

from VAT.models import (
    Sector,
    Subsector,
    TituloReferencia,
    ModalidadCursada,
    PlanVersionCurricular,
)
from VAT.forms import (
    SectorForm,
    SubsectorForm,
    TituloReferenciaForm,
    ModalidadCursadaForm,
    PlanVersionCurricularForm,
)
from VAT.services.access_scope import (
    get_user_provincia_id,
    is_vat_provincial,
    is_vat_sse,
)


# ============ MODALIDAD CURSADA ============


class ModalidadCursadaListView(LoginRequiredMixin, ListView):
    model = ModalidadCursada
    template_name = "vat/catalogo/modalidadcursada_list.html"
    context_object_name = "modalidades"
    paginate_by = 50

    def get_queryset(self):
        return super().get_queryset().order_by("nombre")


class ModalidadCursadaCreateView(LoginRequiredMixin, CreateView):
    model = ModalidadCursada
    form_class = ModalidadCursadaForm
    template_name = "vat/catalogo/modalidadcursada_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Modalidad de cursado creada correctamente.")
        return response

    def get_success_url(self):
        return reverse("vat_modalidadcursada_detail", kwargs={"pk": self.object.pk})


class ModalidadCursadaDetailView(LoginRequiredMixin, DetailView):
    model = ModalidadCursada
    template_name = "vat/catalogo/modalidadcursada_detail.html"
    context_object_name = "modalidad"


class ModalidadCursadaUpdateView(LoginRequiredMixin, UpdateView):
    model = ModalidadCursada
    form_class = ModalidadCursadaForm
    template_name = "vat/catalogo/modalidadcursada_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, "Modalidad de cursado actualizada correctamente."
        )
        return response

    def get_success_url(self):
        return reverse("vat_modalidadcursada_detail", kwargs={"pk": self.object.pk})


class ModalidadCursadaDeleteView(LoginRequiredMixin, DeleteView):
    model = ModalidadCursada
    template_name = "vat/catalogo/modalidadcursada_confirm_delete.html"
    context_object_name = "modalidad"
    success_url = reverse_lazy("vat_modalidadcursada_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Modalidad de cursado eliminada correctamente.")
        return super().delete(request, *args, **kwargs)


# ============ SECTOR ============


class SectorListView(LoginRequiredMixin, ListView):
    model = Sector
    template_name = "vat/catalogo/sector_list.html"
    context_object_name = "sectores"
    paginate_by = 50

    def get_queryset(self):
        return super().get_queryset().order_by("nombre")


class SectorCreateView(LoginRequiredMixin, CreateView):
    model = Sector
    form_class = SectorForm
    template_name = "vat/catalogo/sector_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Sector creado correctamente.")
        return response

    def get_success_url(self):
        return reverse("vat_sector_detail", kwargs={"pk": self.object.pk})


class SectorDetailView(LoginRequiredMixin, DetailView):
    model = Sector
    template_name = "vat/catalogo/sector_detail.html"
    context_object_name = "sector"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subsectores"] = self.object.subsectores.all().order_by("nombre")
        return context


class SectorUpdateView(LoginRequiredMixin, UpdateView):
    model = Sector
    form_class = SectorForm
    template_name = "vat/catalogo/sector_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Sector actualizado correctamente.")
        return response

    def get_success_url(self):
        return reverse("vat_sector_detail", kwargs={"pk": self.object.pk})


class SectorDeleteView(LoginRequiredMixin, DeleteView):
    model = Sector
    template_name = "vat/catalogo/sector_confirm_delete.html"
    context_object_name = "sector"
    success_url = reverse_lazy("vat_sector_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Sector eliminado correctamente.")
        return super().delete(request, *args, **kwargs)


# ============ SUBSECTOR ============


class SubsectorListView(LoginRequiredMixin, ListView):
    model = Subsector
    template_name = "vat/catalogo/subsector_list.html"
    context_object_name = "subsectores"
    paginate_by = 50

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related("sector")
            .order_by("sector__nombre", "nombre")
        )
        sector_id = self.request.GET.get("sector")
        if sector_id:
            queryset = queryset.filter(sector_id=sector_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sectores"] = Sector.objects.all().order_by("nombre")
        context["sector_filter"] = self.request.GET.get("sector")
        return context


class SubsectorCreateView(LoginRequiredMixin, CreateView):
    model = Subsector
    form_class = SubsectorForm
    template_name = "vat/catalogo/subsector_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Subsector creado correctamente.")
        return response

    def get_success_url(self):
        return reverse("vat_subsector_detail", kwargs={"pk": self.object.pk})


class SubsectorDetailView(LoginRequiredMixin, DetailView):
    model = Subsector
    template_name = "vat/catalogo/subsector_detail.html"
    context_object_name = "subsector"


class SubsectorUpdateView(LoginRequiredMixin, UpdateView):
    model = Subsector
    form_class = SubsectorForm
    template_name = "vat/catalogo/subsector_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Subsector actualizado correctamente.")
        return response

    def get_success_url(self):
        return reverse("vat_subsector_detail", kwargs={"pk": self.object.pk})


class SubsectorDeleteView(LoginRequiredMixin, DeleteView):
    model = Subsector
    template_name = "vat/catalogo/subsector_confirm_delete.html"
    context_object_name = "subsector"
    success_url = reverse_lazy("vat_subsector_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Subsector eliminado correctamente.")
        return super().delete(request, *args, **kwargs)


# ============ TITULO REFERENCIA ============


class TituloReferenciaListView(LoginRequiredMixin, ListView):
    model = TituloReferencia
    template_name = "vat/catalogo/titulorreferencia_list.html"
    context_object_name = "titulos"
    paginate_by = 50

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related(
                "plan_estudio", "plan_estudio__sector", "plan_estudio__subsector"
            )
            .order_by("nombre")
        )
        sector_id = self.request.GET.get("sector")
        activo = self.request.GET.get("activo")
        if sector_id:
            queryset = queryset.filter(plan_estudio__sector_id=sector_id)
        if activo == "true":
            queryset = queryset.filter(activo=True)
        elif activo == "false":
            queryset = queryset.filter(activo=False)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sectores"] = Sector.objects.all().order_by("nombre")
        context["sector_filter"] = self.request.GET.get("sector")
        context["activo_filter"] = self.request.GET.get("activo")
        return context


class TituloReferenciaCreateView(LoginRequiredMixin, CreateView):
    model = TituloReferencia
    form_class = TituloReferenciaForm
    template_name = "vat/catalogo/titulorreferencia_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Título de referencia creado correctamente.")
        return response

    def get_success_url(self):
        return reverse("vat_titulorreferencia_detail", kwargs={"pk": self.object.pk})


@login_required
def subsectores_por_sector(request):
    """Devuelve subsectores filtrados por sector. Usado por el modal de Título de Referencia."""
    sector_id = request.GET.get("sector_id")
    if not sector_id:
        return JsonResponse({"subsectores": []})
    try:
        sector_id = int(sector_id)
    except (ValueError, TypeError):
        return JsonResponse({"subsectores": []})
    qs = Subsector.objects.filter(sector_id=sector_id).order_by("nombre")
    data = [{"id": s.id, "nombre": s.nombre} for s in qs]
    return JsonResponse({"subsectores": data})


class TituloReferenciaDetailView(LoginRequiredMixin, DetailView):
    model = TituloReferencia
    template_name = "vat/catalogo/titulorreferencia_detail.html"
    context_object_name = "titulo"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "plan_estudio",
                "plan_estudio__sector",
                "plan_estudio__subsector",
                "plan_estudio__modalidad_cursada",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["planes"] = PlanVersionCurricular.objects.filter(
            titulos=self.object
        ).select_related("sector", "subsector", "modalidad_cursada")
        return context


class TituloReferenciaUpdateView(LoginRequiredMixin, UpdateView):
    model = TituloReferencia
    form_class = TituloReferenciaForm
    template_name = "vat/catalogo/titulorreferencia_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, "Título de referencia actualizado correctamente."
        )
        return response

    def get_success_url(self):
        return reverse("vat_titulorreferencia_detail", kwargs={"pk": self.object.pk})


class TituloReferenciaDeleteView(
    SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView
):
    model = TituloReferencia
    template_name = "vat/catalogo/titulorreferencia_confirm_delete.html"
    context_object_name = "tituloreferencia"

    def get_success_url(self):
        next_url = self.request.POST.get("next")
        if next_url:
            return next_url
        return reverse_lazy("vat_titulorreferencia_list")


# ============ PLAN VERSION CURRICULAR ============


class VATProvincialOnlyMixin:
    """Restringe acceso a usuarios provinciales VAT."""

    def dispatch(self, request, *args, **kwargs):
        if not (is_vat_sse(request.user) or is_vat_provincial(request.user)):
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)


class VATPlanScopeMixin:
    """Aplica scope a planes curriculares según rol VAT."""

    def get_scoped_plan_queryset(self, queryset=None):
        queryset = queryset or super().get_queryset()
        user = self.request.user
        if is_vat_sse(user):
            return queryset

        provincia_id = get_user_provincia_id(user)
        if provincia_id:
            return queryset.filter(provincia_id=provincia_id)

        return queryset.none()


class PlanVersionCurricularListView(
    VATProvincialOnlyMixin, VATPlanScopeMixin, LoginRequiredMixin, ListView
):
    model = PlanVersionCurricular
    template_name = "vat/catalogo/planversioncurricular_list.html"
    context_object_name = "planes"
    paginate_by = 50

    def get_queryset(self):
        queryset = (
            self.get_scoped_plan_queryset()
            .select_related("sector", "subsector", "modalidad_cursada")
            .prefetch_related("titulos")
        )
        titulo_id = self.request.GET.get("titulo")
        activo = self.request.GET.get("activo")
        if titulo_id:
            queryset = queryset.filter(titulos__id=titulo_id)
        if activo == "true":
            queryset = queryset.filter(activo=True)
        elif activo == "false":
            queryset = queryset.filter(activo=False)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulos"] = TituloReferencia.objects.all().order_by("nombre")
        context["titulo_filter"] = self.request.GET.get("titulo")
        context["activo_filter"] = self.request.GET.get("activo")
        return context


class PlanVersionCurricularCreateView(VATProvincialOnlyMixin, LoginRequiredMixin, CreateView):
    model = PlanVersionCurricular
    form_class = PlanVersionCurricularForm
    template_name = "vat/catalogo/planversioncurricular_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "Nuevo Plan de Estudio",
                "submit_text": "Crear plan",
                "cancel_url": reverse("vat_planversioncurricular_list"),
            }
        )
        return context

    def form_valid(self, form):
        provincia_id = get_user_provincia_id(self.request.user)
        if provincia_id:
            form.instance.provincia_id = provincia_id
        response = super().form_valid(form)
        messages.success(self.request, "Plan de estudio creado correctamente.")
        return response

    def get_success_url(self):
        return reverse(
            "vat_planversioncurricular_detail", kwargs={"pk": self.object.pk}
        )


class PlanVersionCurricularDetailView(
    VATProvincialOnlyMixin, VATPlanScopeMixin, LoginRequiredMixin, DetailView
):
    model = PlanVersionCurricular
    template_name = "vat/catalogo/planversioncurricular_detail.html"
    context_object_name = "plan"

    def get_queryset(self):
        return self.get_scoped_plan_queryset(super().get_queryset())


class PlanVersionCurricularUpdateView(
    VATProvincialOnlyMixin, VATPlanScopeMixin, LoginRequiredMixin, UpdateView
):
    model = PlanVersionCurricular
    form_class = PlanVersionCurricularForm
    template_name = "vat/catalogo/planversioncurricular_form.html"

    def get_queryset(self):
        return self.get_scoped_plan_queryset(super().get_queryset())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "Editar Plan de Estudio",
                "submit_text": "Guardar cambios",
                "cancel_url": reverse(
                    "vat_planversioncurricular_detail", kwargs={"pk": self.object.pk}
                ),
            }
        )
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Plan de estudio actualizado correctamente.")
        return response

    def get_success_url(self):
        return reverse(
            "vat_planversioncurricular_detail", kwargs={"pk": self.object.pk}
        )


class PlanVersionCurricularDeleteView(
    VATProvincialOnlyMixin,
    VATPlanScopeMixin,
    SoftDeleteDeleteViewMixin,
    LoginRequiredMixin,
    DeleteView,
):
    model = PlanVersionCurricular
    template_name = "vat/catalogo/planversioncurricular_confirm_delete.html"
    context_object_name = "planversioncurricular"

    def get_queryset(self):
        return self.get_scoped_plan_queryset(super().get_queryset())

    def get_success_url(self):
        next_url = self.request.POST.get("next")
        if next_url:
            return next_url
        return reverse_lazy("vat_planversioncurricular_list")
