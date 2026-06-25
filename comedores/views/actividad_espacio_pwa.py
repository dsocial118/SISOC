from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView, UpdateView

from comedores.forms.actividad_espacio_pwa_form import ActividadEspacioPWAWebForm
from comedores.services.comedor_service import ComedorService
from comedores.utils import is_pnud_comedor
from pwa.models import ActividadEspacioPWA
from pwa.services.actividades_service import (
    create_actividad_espacio,
    update_actividad_espacio,
)


MANAGE_ACTIVIDADES_ESPACIO_PERMISSION = "pwa.manage_colaboradores_pwa"


class ActividadEspacioPWAWebPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (
            user.has_perm("auth.role_admin")
            or user.has_perm(MANAGE_ACTIVIDADES_ESPACIO_PERMISSION)
        )

    def dispatch(self, request, *args, **kwargs):
        self.comedor = ComedorService.get_scoped_comedor_or_404(
            self.kwargs["pk"],
            request.user,
        )
        if not is_pnud_comedor(self.comedor):
            raise Http404("Modulo de actividades no disponible para este programa.")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["comedor"] = self.comedor
        return kwargs

    def get_success_url(self):
        return (
            f"{reverse('comedor_detalle', kwargs={'pk': self.comedor.id})}"
            "#legajo-actividades-pnud"
        )


class ActividadEspacioPWACreateView(ActividadEspacioPWAWebPermissionMixin, FormView):
    form_class = ActividadEspacioPWAWebForm
    template_name = "comedor/actividad_espacio_pwa_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comedor"] = self.comedor
        context["edit_mode"] = False
        return context

    def form_valid(self, form):
        schedules = form.get_schedule_data()
        with transaction.atomic():
            for schedule in schedules:
                create_actividad_espacio(
                    comedor_id=self.comedor.id,
                    actor=self.request.user,
                    data=form.get_service_data(schedule),
                )
        if len(schedules) == 1:
            messages.success(self.request, "Actividad creada correctamente.")
        else:
            messages.success(
                self.request,
                f"Se crearon {len(schedules)} horarios de actividad correctamente.",
            )
        return redirect(self.get_success_url())


class ActividadEspacioPWAUpdateView(ActividadEspacioPWAWebPermissionMixin, UpdateView):
    model = ActividadEspacioPWA
    form_class = ActividadEspacioPWAWebForm
    template_name = "comedor/actividad_espacio_pwa_form.html"
    pk_url_kwarg = "pk2"

    def get_queryset(self):
        return ActividadEspacioPWA.objects.filter(comedor=self.comedor)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comedor"] = self.comedor
        context["edit_mode"] = True
        return context

    def form_valid(self, form):
        schedules = form.get_schedule_data()
        first_schedule, *extra_schedules = schedules
        with transaction.atomic():
            update_actividad_espacio(
                actividad=self.object,
                actor=self.request.user,
                data=form.get_service_data(first_schedule),
            )
            for schedule in extra_schedules:
                create_actividad_espacio(
                    comedor_id=self.comedor.id,
                    actor=self.request.user,
                    data=form.get_service_data(schedule),
                )
        if extra_schedules:
            messages.success(
                self.request,
                "Actividad actualizada y horarios adicionales creados correctamente.",
            )
        else:
            messages.success(self.request, "Actividad actualizada correctamente.")
        return redirect(self.get_success_url())
