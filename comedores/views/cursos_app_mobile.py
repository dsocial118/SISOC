from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from comedores.forms.cursos_app_mobile_form import CursoAppMobileForm
from comedores.models import CursoAppMobile
from core.soft_delete.view_helpers import SoftDeleteDeleteViewMixin


class CursoAppMobileListView(LoginRequiredMixin, ListView):
    model = CursoAppMobile
    template_name = "comedor/cursos_app_mobile_list.html"
    context_object_name = "cursos"
    paginate_by = 20

    def get_queryset(self):
        return CursoAppMobile.objects.select_related("creado_por", "modificado_por")


class CursoAppMobileCreateView(LoginRequiredMixin, CreateView):
    model = CursoAppMobile
    form_class = CursoAppMobileForm
    template_name = "comedor/cursos_app_mobile_form.html"
    success_url = reverse_lazy("cursos_app_mobile_list")

    def form_valid(self, form):
        with transaction.atomic():
            obj = form.save(commit=False)
            obj.creado_por = self.request.user
            obj.modificado_por = self.request.user
            obj.save()
            self.object = obj
        messages.success(self.request, "Curso para app mobile creado correctamente.")
        return HttpResponseRedirect(self.get_success_url())


class CursoAppMobileUpdateView(LoginRequiredMixin, UpdateView):
    model = CursoAppMobile
    form_class = CursoAppMobileForm
    template_name = "comedor/cursos_app_mobile_form.html"
    success_url = reverse_lazy("cursos_app_mobile_list")

    def form_valid(self, form):
        with transaction.atomic():
            obj = form.save(commit=False)
            obj.modificado_por = self.request.user
            obj.save()
            self.object = obj
        messages.success(
            self.request, "Curso para app mobile actualizado correctamente."
        )
        return HttpResponseRedirect(self.get_success_url())


class CursoAppMobileDeleteView(
    SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView
):
    model = CursoAppMobile
    template_name = "comedor/cursos_app_mobile_confirm_delete.html"
    success_url = reverse_lazy("cursos_app_mobile_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse("cursos_app_mobile_list")
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Curso para app mobile eliminado correctamente.")
        return response
