from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse, reverse_lazy
from django.contrib import messages

from VAT.models import Sector, Subsector, TituloReferencia, ModalidadCursada, PlanVersionCurricular
from VAT.forms import (
    SectorForm,
    SubsectorForm,
    TituloReferenciaForm,
    ModalidadCursadaForm,
    PlanVersionCurricularForm,
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
        messages.success(self.request, "Modalidad de cursado actualizada correctamente.")
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
        queryset = super().get_queryset().select_related("sector").order_by("sector__nombre", "nombre")
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
        messages.success(self.request, "Modalidad de cursado actualizada correctamente.")
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


# ============ TITULO REFERENCIA ============

class TituloReferenciaListView(LoginRequiredMixin, ListView):
    model = TituloReferencia
    template_name = "vat/catalogo/titulorreferencia_list.html"
    context_object_name = "titulos"
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset().select_related("sector", "subsector").order_by("nombre")
        sector_id = self.request.GET.get("sector")
        activo = self.request.GET.get("activo")
        if sector_id:
            queryset = queryset.filter(sector_id=sector_id)
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


class TituloReferenciaDetailView(LoginRequiredMixin, DetailView):
    model = TituloReferencia
    template_name = "vat/catalogo/titulorreferencia_detail.html"
    context_object_name = "titulo"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["planes"] = self.object.planes.all().select_related("modalidad_cursada").order_by("modalidad_cursada")
        return context


class TituloReferenciaUpdateView(LoginRequiredMixin, UpdateView):
    model = TituloReferencia
    form_class = TituloReferenciaForm
    template_name = "vat/catalogo/titulorreferencia_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Título de referencia actualizado correctamente.")
        return response

    def get_success_url(self):
        return reverse("vat_titulorreferencia_detail", kwargs={"pk": self.object.pk})


class TituloReferenciaDeleteView(LoginRequiredMixin, DeleteView):
    model = TituloReferencia
    template_name = "vat/catalogo/titulorreferencia_confirm_delete.html"
    context_object_name = "tituloreferencia"
    success_url = reverse_lazy("vat_titulorreferencia_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Título de referencia eliminado correctamente.")
        return super().delete(request, *args, **kwargs)


# ============ PLAN VERSION CURRICULAR ============

class PlanVersionCurricularListView(LoginRequiredMixin, ListView):
    model = PlanVersionCurricular
    template_name = "vat/catalogo/planversioncurricular_list.html"
    context_object_name = "planes"
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            "titulo_referencia", "modalidad_cursada"
        ).order_by("titulo_referencia", "modalidad_cursada")
        titulo_id = self.request.GET.get("titulo")
        activo = self.request.GET.get("activo")
        if titulo_id:
            queryset = queryset.filter(titulo_referencia_id=titulo_id)
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


class PlanVersionCurricularCreateView(LoginRequiredMixin, CreateView):
    model = PlanVersionCurricular
    form_class = PlanVersionCurricularForm
    template_name = "vat/catalogo/planversioncurricular_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Plan curricular creado correctamente.")
        return response

    def get_success_url(self):
        return reverse("vat_planversioncurricular_detail", kwargs={"pk": self.object.pk})


class PlanVersionCurricularDetailView(LoginRequiredMixin, DetailView):
    model = PlanVersionCurricular
    template_name = "vat/catalogo/planversioncurricular_detail.html"
    context_object_name = "plan"


class PlanVersionCurricularUpdateView(LoginRequiredMixin, UpdateView):
    model = PlanVersionCurricular
    form_class = PlanVersionCurricularForm
    template_name = "vat/catalogo/planversioncurricular_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Plan curricular actualizado correctamente.")
        return response

    def get_success_url(self):
        return reverse("vat_planversioncurricular_detail", kwargs={"pk": self.object.pk})


class PlanVersionCurricularDeleteView(LoginRequiredMixin, DeleteView):
    model = PlanVersionCurricular
    template_name = "vat/catalogo/planversioncurricular_confirm_delete.html"
    context_object_name = "planversioncurricular"
    success_url = reverse_lazy("vat_planversioncurricular_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Plan curricular eliminado correctamente.")
        return super().delete(request, *args, **kwargs)
