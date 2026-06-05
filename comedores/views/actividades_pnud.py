from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from comedores.forms.actividades_pnud_form import ActividadPnudForm
from pwa.models import CatalogoActividadPWA


VIEW_PERMISSION = "pwa.view_catalogoactividadpwa"
MANAGE_PERMISSION = "pwa.manage_catalogoactividadpwa"


class ActividadPnudPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    permission_codes = (VIEW_PERMISSION,)
    raise_exception = True

    def test_func(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return False
        if user.has_perm("auth.role_admin"):
            return True
        return any(user.has_perm(code) for code in self.permission_codes)


class ActividadPnudManagePermissionMixin(ActividadPnudPermissionMixin):
    permission_codes = (MANAGE_PERMISSION,)


class ActividadPnudListView(ActividadPnudPermissionMixin, ListView):
    model = CatalogoActividadPWA
    template_name = "comedor/actividades_pnud_list.html"
    context_object_name = "actividades"
    paginate_by = 50
    permission_codes = (VIEW_PERMISSION, MANAGE_PERMISSION)

    def get_queryset(self):
        queryset = CatalogoActividadPWA.objects.order_by(
            "categoria",
            "actividad",
            "id",
        )
        estado = (self.request.GET.get("estado") or "activa").strip().lower()
        if estado == "activa":
            queryset = queryset.filter(activo=True)
        elif estado == "inactiva":
            queryset = queryset.filter(activo=False)
        busqueda = (self.request.GET.get("q") or "").strip()
        if busqueda:
            queryset = queryset.filter(
                Q(categoria__icontains=busqueda) | Q(actividad__icontains=busqueda)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["estado_filtro"] = (self.request.GET.get("estado") or "activa").strip()
        context["busqueda"] = (self.request.GET.get("q") or "").strip()
        context["can_manage_actividades_pnud"] = self.request.user.has_perm(
            "auth.role_admin"
        ) or self.request.user.has_perm(MANAGE_PERMISSION)
        return context


class ActividadPnudCreateView(ActividadPnudManagePermissionMixin, CreateView):
    model = CatalogoActividadPWA
    form_class = ActividadPnudForm
    template_name = "comedor/actividades_pnud_form.html"
    success_url = reverse_lazy("actividades_pnud_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["categorias"] = (
            CatalogoActividadPWA.objects.order_by("categoria")
            .values_list("categoria", flat=True)
            .distinct()
        )
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Actividad PNUD creada correctamente.")
        return super().form_valid(form)


class ActividadPnudUpdateView(ActividadPnudManagePermissionMixin, UpdateView):
    model = CatalogoActividadPWA
    form_class = ActividadPnudForm
    template_name = "comedor/actividades_pnud_form.html"
    success_url = reverse_lazy("actividades_pnud_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["categorias"] = (
            CatalogoActividadPWA.objects.order_by("categoria")
            .values_list("categoria", flat=True)
            .distinct()
        )
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Actividad PNUD actualizada correctamente.")
        return super().form_valid(form)


class ActividadPnudDeactivateView(ActividadPnudManagePermissionMixin, TemplateView):
    template_name = "comedor/actividades_pnud_confirm_deactivate.html"

    def get_object(self):
        return get_object_or_404(CatalogoActividadPWA, pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        context["cancel_url"] = reverse("actividades_pnud_list")
        return context

    def post(self, request, *args, **kwargs):
        actividad = self.get_object()
        if actividad.activo:
            actividad.activo = False
            actividad.save(update_fields=["activo", "fecha_actualizacion"])
            messages.success(request, "Actividad PNUD dada de baja correctamente.")
        else:
            messages.info(request, "La actividad PNUD ya se encontraba inactiva.")
        return HttpResponseRedirect(reverse("actividades_pnud_list"))
