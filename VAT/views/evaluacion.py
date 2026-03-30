import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView,
)
from django.contrib import messages
from django.db.models import Q, Count

from core.soft_delete.view_helpers import SoftDeleteDeleteViewMixin
from VAT.models import (
    Evaluacion,
    ResultadoEvaluacion,
)
from VAT.forms import (
    EvaluacionForm,
    ResultadoEvaluacionForm,
)

logger = logging.getLogger("django")


# ============================================================================
# EVALUACIÓN VIEWS
# ============================================================================


class EvaluacionListView(LoginRequiredMixin, ListView):
    model = Evaluacion
    template_name = "vat/evaluacion/evaluacion_list.html"
    context_object_name = "evaluaciones"
    paginate_by = 20

    def get_queryset(self):
        queryset = Evaluacion.objects.select_related("comision").order_by("-fecha")

        comision_id = self.request.GET.get("comision_id")
        tipo = self.request.GET.get("tipo")
        buscar = self.request.GET.get("busqueda") or self.request.GET.get("q")

        if comision_id:
            queryset = queryset.filter(comision_id=comision_id)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if buscar:
            queryset = queryset.filter(
                Q(nombre__icontains=buscar)
                | Q(comision__codigo_comision__icontains=buscar)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tipo_choices"] = Evaluacion.TIPO_EVALUACION_CHOICES
        return context


class EvaluacionCreateView(LoginRequiredMixin, CreateView):
    model = Evaluacion
    form_class = EvaluacionForm
    template_name = "vat/evaluacion/evaluacion_form.html"
    success_url = reverse_lazy("vat_evaluacion_list")

    def form_valid(self, form):
        messages.success(self.request, "Evaluación creada exitosamente.")
        return super().form_valid(form)


class EvaluacionDetailView(LoginRequiredMixin, DetailView):
    model = Evaluacion
    template_name = "vat/evaluacion/evaluacion_detail.html"
    context_object_name = "evaluacion"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        evaluacion = self.get_object()
        context["resultados"] = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion
        ).select_related("inscripcion__ciudadano")
        context["total_resultados"] = context["resultados"].count()
        context["aprobados"] = context["resultados"].filter(aprobo=True).count()
        return context


class EvaluacionUpdateView(LoginRequiredMixin, UpdateView):
    model = Evaluacion
    form_class = EvaluacionForm
    template_name = "vat/evaluacion/evaluacion_form.html"
    success_url = reverse_lazy("vat_evaluacion_list")

    def form_valid(self, form):
        messages.success(self.request, "Evaluación actualizada exitosamente.")
        return super().form_valid(form)


class EvaluacionDeleteView(LoginRequiredMixin, DeleteView):
    model = Evaluacion
    template_name = "vat/evaluacion/evaluacion_confirm_delete.html"
    context_object_name = "evaluacion"
    success_url = reverse_lazy("vat_evaluacion_list")


# ============================================================================
# RESULTADO EVALUACIÓN VIEWS
# ============================================================================


class ResultadoEvaluacionListView(LoginRequiredMixin, ListView):
    model = ResultadoEvaluacion
    template_name = "vat/evaluacion/resultado_list.html"
    context_object_name = "resultados"
    paginate_by = 20

    def get_queryset(self):
        queryset = ResultadoEvaluacion.objects.select_related(
            "evaluacion", "inscripcion__ciudadano"
        ).order_by("-fecha_registro")

        evaluacion_id = self.request.GET.get("evaluacion_id")
        inscripcion_id = self.request.GET.get("inscripcion_id")
        calificacion = self.request.GET.get("calificacion")
        buscar = self.request.GET.get("busqueda") or self.request.GET.get("q")

        if evaluacion_id:
            queryset = queryset.filter(evaluacion_id=evaluacion_id)
        if inscripcion_id:
            queryset = queryset.filter(inscripcion_id=inscripcion_id)
        if calificacion:
            queryset = queryset.filter(calificacion=calificacion)
        if buscar:
            queryset = queryset.filter(
                Q(inscripcion__ciudadano__apellido__icontains=buscar)
                | Q(inscripcion__ciudadano__nombre__icontains=buscar)
                | Q(evaluacion__nombre__icontains=buscar)
            )

        return queryset


class ResultadoEvaluacionCreateView(LoginRequiredMixin, CreateView):
    model = ResultadoEvaluacion
    form_class = ResultadoEvaluacionForm
    template_name = "vat/evaluacion/resultado_form.html"
    success_url = reverse_lazy("vat_resultado_evaluacion_list")

    def form_valid(self, form):
        form.instance.registrado_por = self.request.user
        messages.success(self.request, "Resultado de evaluación creado exitosamente.")
        return super().form_valid(form)


class ResultadoEvaluacionDetailView(LoginRequiredMixin, DetailView):
    model = ResultadoEvaluacion
    template_name = "vat/evaluacion/resultado_detail.html"
    context_object_name = "resultado"


class ResultadoEvaluacionUpdateView(LoginRequiredMixin, UpdateView):
    model = ResultadoEvaluacion
    form_class = ResultadoEvaluacionForm
    template_name = "vat/evaluacion/resultado_form.html"
    success_url = reverse_lazy("vat_resultado_evaluacion_list")

    def form_valid(self, form):
        form.instance.registrado_por = self.request.user
        messages.success(
            self.request, "Resultado de evaluación actualizado exitosamente."
        )
        return super().form_valid(form)


class ResultadoEvaluacionDeleteView(
    SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView
):
    model = ResultadoEvaluacion
    template_name = "vat/evaluacion/resultado_confirm_delete.html"
    context_object_name = "resultado"
    success_url = reverse_lazy("vat_resultado_evaluacion_list")
