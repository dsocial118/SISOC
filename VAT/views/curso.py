from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.views.generic import CreateView, UpdateView, DeleteView

from core.soft_delete.view_helpers import SoftDeleteDeleteViewMixin
from VAT.forms import CursoForm, ComisionCursoForm
from VAT.models import Centro, Curso, ComisionCurso
from VAT.services.access_scope import (
    can_user_access_centro,
    filter_centros_queryset_for_user,
)


class CursoCreateView(LoginRequiredMixin, CreateView):
    model = Curso
    form_class = CursoForm
    template_name = "vat/curso/curso_form.html"

    def dispatch(self, request, *args, **kwargs):
        centro_id = request.GET.get("centro") or request.POST.get("centro")
        if not centro_id:
            raise PermissionDenied

        try:
            centro = Centro.objects.get(pk=centro_id)
        except Centro.DoesNotExist as exc:
            raise PermissionDenied from exc

        if not can_user_access_centro(request.user, centro):
            raise PermissionDenied

        self.centro = centro
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial["centro"] = self.centro.id
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        scoped_centros = filter_centros_queryset_for_user(
            Centro.objects.all(), self.request.user
        )
        form.fields["centro"].queryset = scoped_centros
        form.fields["ubicacion"].queryset = self.centro.ubicaciones.select_related(
            "localidad"
        )
        return form

    def form_valid(self, form):
        messages.success(self.request, "Curso creado exitosamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = (
            f"{reverse('vat_centro_detail', kwargs={'pk': self.centro.id})}#cursos"
        )
        return context

    def get_success_url(self):
        return f"{reverse('vat_centro_detail', kwargs={'pk': self.object.centro_id})}#cursos"


class CursoUpdateView(LoginRequiredMixin, UpdateView):
    model = Curso
    form_class = CursoForm
    template_name = "vat/curso/curso_form.html"

    def get_queryset(self):
        scoped_centros = filter_centros_queryset_for_user(
            Centro.objects.all(), self.request.user
        ).values_list("id", flat=True)
        return Curso.objects.select_related("centro", "ubicacion").filter(
            centro_id__in=scoped_centros
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        scoped_centros = filter_centros_queryset_for_user(
            Centro.objects.all(), self.request.user
        )
        form.fields["centro"].queryset = scoped_centros
        form.fields["ubicacion"].queryset = self.object.centro.ubicaciones.select_related(
            "localidad"
        )
        return form

    def form_valid(self, form):
        messages.success(self.request, "Curso actualizado exitosamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = (
            f"{reverse('vat_centro_detail', kwargs={'pk': self.object.centro_id})}#cursos"
        )
        return context

    def get_success_url(self):
        return f"{reverse('vat_centro_detail', kwargs={'pk': self.object.centro_id})}#cursos"


class CursoDeleteView(SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView):
    model = Curso
    template_name = "vat/curso/curso_confirm_delete.html"
    context_object_name = "curso"

    def get_queryset(self):
        scoped_centros = filter_centros_queryset_for_user(
            Centro.objects.all(), self.request.user
        ).values_list("id", flat=True)
        return Curso.objects.select_related("centro").filter(centro_id__in=scoped_centros)

    def get_success_url(self):
        return f"{reverse('vat_centro_detail', kwargs={'pk': self.object.centro_id})}#cursos"


class ComisionCursoCreateView(LoginRequiredMixin, CreateView):
    model = ComisionCurso
    form_class = ComisionCursoForm
    template_name = "vat/curso/comision_curso_form.html"

    def dispatch(self, request, *args, **kwargs):
        curso_id = request.GET.get("curso") or request.POST.get("curso")
        if curso_id:
            try:
                curso = Curso.objects.select_related("centro").get(pk=curso_id)
            except Curso.DoesNotExist as exc:
                raise PermissionDenied from exc
            if not can_user_access_centro(request.user, curso.centro):
                raise PermissionDenied
            self.curso = curso
        else:
            self.curso = None
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if self.curso:
            initial["curso"] = self.curso.id
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        scoped_centros = filter_centros_queryset_for_user(
            Centro.objects.all(), self.request.user
        )
        form.fields["curso"].queryset = Curso.objects.filter(
            centro_id__in=scoped_centros.values_list("id", flat=True)
        ).select_related("centro")
        return form

    def form_valid(self, form):
        messages.success(self.request, "Comisión del curso creada exitosamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return (
            f"{reverse('vat_centro_detail', kwargs={'pk': self.object.curso.centro_id})}"
            "#cursos"
        )


class ComisionCursoUpdateView(LoginRequiredMixin, UpdateView):
    model = ComisionCurso
    form_class = ComisionCursoForm
    template_name = "vat/curso/comision_curso_form.html"

    def get_queryset(self):
        scoped_centros = filter_centros_queryset_for_user(
            Centro.objects.all(), self.request.user
        ).values_list("id", flat=True)
        return ComisionCurso.objects.select_related("curso__centro").filter(
            curso__centro_id__in=scoped_centros
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        scoped_centros = filter_centros_queryset_for_user(
            Centro.objects.all(), self.request.user
        )
        form.fields["curso"].queryset = Curso.objects.filter(
            centro_id__in=scoped_centros.values_list("id", flat=True)
        ).select_related("centro")
        return form

    def form_valid(self, form):
        messages.success(self.request, "Comisión del curso actualizada exitosamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return (
            f"{reverse('vat_centro_detail', kwargs={'pk': self.object.curso.centro_id})}"
            "#cursos"
        )


class ComisionCursoDeleteView(
    SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView
):
    model = ComisionCurso
    template_name = "vat/curso/comision_curso_confirm_delete.html"
    context_object_name = "comision_curso"

    def get_queryset(self):
        scoped_centros = filter_centros_queryset_for_user(
            Centro.objects.all(), self.request.user
        ).values_list("id", flat=True)
        return ComisionCurso.objects.select_related("curso__centro").filter(
            curso__centro_id__in=scoped_centros
        )

    def get_success_url(self):
        return (
            f"{reverse('vat_centro_detail', kwargs={'pk': self.object.curso.centro_id})}"
            "#cursos"
        )
