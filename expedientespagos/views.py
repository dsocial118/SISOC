from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import ensure_csrf_cookie
from core.soft_delete.view_helpers import SoftDeleteDeleteViewMixin
from core.services.column_preferences import build_columns_context_for_custom_cells
from core.templatetags.custom_filters import monto_sin_decimales
from expedientespagos.models import ExpedientePago
from expedientespagos.filter_config import get_filters_ui_config
from expedientespagos.forms import ExpedientePagoForm
from expedientespagos.services import ExpedientesPagosService
from comedores.models import Comedor
from iam.services import user_has_any_permission_codes


_BADGE_SIN_ADMISION = mark_safe(  # nosec B308 - literal sin datos de usuario
    '<span class="badge bg-warning text-dark" '
    'title="No se encontró una admisión con este expediente de convenio">'
    '<i class="fas fa-exclamation-triangle me-1"></i>Sin admisión</span>'
)


def _celda_admision(expediente):
    """Muestra la admisión vinculada o una alerta cuando quedó sin asignar."""
    admision = expediente.admision
    if admision is None:
        return {"content": _BADGE_SIN_ADMISION}
    return {"content": escape(admision.num_expediente or f"Admisión #{admision.id}")}


def _build_expediente_pago_list_item(expediente):
    return {
        "pk": expediente.pk,
        "cells": [
            {"content": escape(expediente.mes_pago or "-")},
            {"content": escape(expediente.ano or "-")},
            {"content": escape(expediente.expediente_pago or "-")},
            {"content": escape(expediente.expediente_convenio or "-")},
            _celda_admision(expediente),
            {"content": format_html("${}", monto_sin_decimales(expediente.total))},
            {
                "content": (
                    expediente.fecha_creacion.strftime("%d/%m/%Y")
                    if expediente.fecha_creacion
                    else "-"
                )
            },
        ],
    }


@method_decorator(ensure_csrf_cookie, name="dispatch")
class ExpedientesPagosListView(LoginRequiredMixin, ListView):
    model = ExpedientePago
    template_name = "expedientespagos_list.html"
    context_object_name = "expedientespagos"
    paginate_by = 10

    def get_queryset(self):
        """Expedientes del comedor de la URL, filtrados y ordenados.

        Antes devolvía ``ExpedientePago.objects.all()`` y el contexto lo pisaba
        con los del comedor, así que el paginador contaba sobre el total del
        sistema en lugar de sobre lo que se mostraba.
        """
        return ExpedientesPagosService.obtener_expedientes_pagos(
            self.kwargs.get("pk"), self.request
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor_id = self.kwargs.get("pk")
        context["expedientes_pagos"] = [
            _build_expediente_pago_list_item(expediente)
            for expediente in context["object_list"]
        ]
        context["comedorid"] = comedor_id
        context["sin_admision_count"] = ExpedientesPagosService.contar_sin_admision(
            comedor_id
        )
        context.update(
            {
                "reset_url": reverse(
                    "expedientespagos_list", kwargs={"pk": comedor_id}
                ),
                "filters_mode": True,
                "filters_config": get_filters_ui_config(),
                "filters_action": reverse(
                    "expedientespagos_list", kwargs={"pk": comedor_id}
                ),
            }
        )

        headers = [
            {"key": "mes_pago", "title": "Mes de Pago"},
            {"key": "ano", "title": "Año"},
            {"key": "expediente_pago", "title": "Expediente de Pago"},
            {"key": "expediente_convenio", "title": "Expediente del Convenio"},
            {"key": "admision", "title": "Admisión"},
            {"key": "total", "title": "Total"},
            {"key": "fecha_creacion", "title": "Fecha de creación"},
        ]

        context.update(
            build_columns_context_for_custom_cells(
                self.request,
                "expedientes_pagos_list",
                headers,
                context["expedientes_pagos"],
                items_key="expedientes_pagos",
            )
        )
        context["custom_cells"] = True

        context["table_actions"] = [
            {"label": "Ver", "url_name": "expedientespagos_detail", "type": "info"}
        ]

        return context


class ExpedientesPagosDetailView(LoginRequiredMixin, DetailView):
    model = ExpedientePago
    template_name = "expedientespagos_detail.html"
    context_object_name = "expediente_pago"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["expediente"] = ExpedientesPagosService.obtener_expediente_pago(
            self.kwargs.get("pk")
        )
        return context


class ExpedientesPagosCreateView(LoginRequiredMixin, CreateView):
    model = ExpedientePago
    template_name = "expedientespagos_form.html"
    form_class = ExpedientePagoForm

    def _get_role_flags(self):
        es_area_legales = (
            self.request.user.is_superuser
            or user_has_any_permission_codes(
                self.request.user,
                [
                    "comedores.view_comedor",
                    "admisiones.view_admision",
                    "acompanamientos.view_informacionrelevante",
                    "expedientespagos.view_expedientepago",
                ],
            )
        )
        es_tecnico_comedor = (
            self.request.user.is_superuser
            or user_has_any_permission_codes(
                self.request.user,
                [
                    "comedores.view_comedor",
                    "admisiones.view_admision",
                    "acompanamientos.view_informacionrelevante",
                ],
            )
        )
        return es_area_legales, es_tecnico_comedor

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        es_area_legales, es_tecnico_comedor = self._get_role_flags()
        kwargs.update(
            {
                "es_area_legales": es_area_legales,
                "es_tecnico_comedor": es_tecnico_comedor,
                "comedor": Comedor.objects.filter(pk=self.kwargs.get("pk")).first(),
            }
        )
        return kwargs

    def get_success_url(self):
        return reverse_lazy(
            "expedientespagos_list", kwargs={"pk": self.kwargs.get("pk")}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor_id = self.kwargs.get("pk")
        context["comedorid"] = comedor_id
        # No se reemplaza context["form"]: pisarlo con un form nuevo descartaba
        # los datos cargados y los errores de validación al reenviar.
        es_area_legales, es_tecnico_comedor = self._get_role_flags()
        context["es_area_legales"] = es_area_legales
        context["es_tecnico_comedor"] = es_tecnico_comedor
        # URL de cancelación para el componente form_buttons
        context["expedientes_list_url"] = reverse(
            "expedientespagos_list", kwargs={"pk": comedor_id}
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        comedor_id = self.kwargs.get("pk")
        form = self.get_form()
        comedor = Comedor.objects.get(pk=comedor_id)
        if form.is_valid():
            # Crear el objeto y asignarlo a self.object
            self.object = ExpedientesPagosService.crear_expediente_pago(
                comedor, form.cleaned_data
            )
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class ExpedientesPagosUpdateView(LoginRequiredMixin, UpdateView):
    model = ExpedientePago
    template_name = "expedientespagos_form.html"
    form_class = ExpedientePagoForm

    def _get_role_flags(self):
        es_area_legales = (
            self.request.user.is_superuser
            or user_has_any_permission_codes(
                self.request.user,
                [
                    "comedores.view_comedor",
                    "admisiones.view_admision",
                    "acompanamientos.view_informacionrelevante",
                    "expedientespagos.view_expedientepago",
                ],
            )
        )
        es_tecnico_comedor = (
            self.request.user.is_superuser
            or user_has_any_permission_codes(
                self.request.user,
                [
                    "comedores.view_comedor",
                    "admisiones.view_admision",
                    "acompanamientos.view_informacionrelevante",
                ],
            )
        )
        return es_area_legales, es_tecnico_comedor

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        es_area_legales, es_tecnico_comedor = self._get_role_flags()
        kwargs.update(
            {
                "es_area_legales": es_area_legales,
                "es_tecnico_comedor": es_tecnico_comedor,
                "comedor": getattr(self.get_object(), "comedor", None),
            }
        )
        return kwargs

    def get_success_url(self):
        return reverse_lazy(
            "expedientespagos_list", kwargs={"pk": self.object.comedor.id}
        )

    def form_valid(self, form):
        # Mantén el mismo comedor que tenía originalmente
        form.instance.comedor = self.get_object().comedor
        ExpedientesPagosService.actualizar_expediente_pago(
            form.instance, form.cleaned_data
        )
        self.object = form.instance
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        expediente = self.get_object()
        context["comedorid"] = expediente.comedor.id
        es_area_legales, es_tecnico_comedor = self._get_role_flags()
        context["es_area_legales"] = es_area_legales
        context["es_tecnico_comedor"] = es_tecnico_comedor
        # URL de cancelación para el componente form_buttons
        context["expedientes_list_url"] = reverse(
            "expedientespagos_list", kwargs={"pk": expediente.comedor.id}
        )
        return context

    def post(self, request, *args, **kwargs):
        # Configurar self.object antes de llamar a form_valid
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class ExpedientesPagosDeleteView(
    SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView
):
    model = ExpedientePago
    template_name = "expedientespagos_confirm_delete.html"
    success_message = "Expediente dado de baja correctamente."

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except ExpedientePago.DoesNotExist as exc:
            raise Http404("El expediente de pago no existe.") from exc

    def get_success_url(self):
        return reverse("lista_comedores_acompanamiento")
