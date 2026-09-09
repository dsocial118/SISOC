"""Vistas del backoffice para editar y revisar instancias del ciclo de
seguimiento, y para gestionar actas complementarias extraordinarias.

Todo lo que se crea o edita desde acá queda con ``origen=sisoc``; la API que
consume la app no cambia.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic.base import View

from comedores.models import Comedor
from relevamientos.forms_backoffice import (
    ActaComplementariaEditor,
    SeguimientoEditor,
)
from relevamientos.models import ActaComplementaria
from relevamientos.views.seguimiento_helpers import (
    aplicar_revision_coordinador,
    resolver_seguimiento,
    seguimiento_queryset,
)


def _url_detalle_seguimiento(seguimiento):
    relevamiento = seguimiento.id_relevamiento
    return reverse(
        "seguimiento_detalle",
        kwargs={
            "comedor_pk": relevamiento.comedor_id,
            "relevamiento_pk": relevamiento.id,
            "pk": seguimiento.pk,
        },
    )


class SeguimientoUpdateView(LoginRequiredMixin, View):
    """Edición completa de una instancia: raíz, bloques y prestaciones."""

    template_name = "seguimiento_form.html"

    def _contexto(self, seguimiento, editor):
        relevamiento = seguimiento.id_relevamiento
        return {
            "seguimiento": seguimiento,
            "relevamiento": relevamiento,
            "comedor": relevamiento.comedor,
            "editor": editor,
        }

    def get(self, request, **kwargs):
        seguimiento = resolver_seguimiento(self.kwargs, seguimiento_queryset())
        editor = SeguimientoEditor(seguimiento)
        return render(request, self.template_name, self._contexto(seguimiento, editor))

    def post(self, request, **kwargs):
        seguimiento = resolver_seguimiento(self.kwargs, seguimiento_queryset())
        editor = SeguimientoEditor(seguimiento, data=request.POST)
        if editor.es_valido():
            editor.guardar()
            messages.success(request, "Seguimiento actualizado correctamente.")
            return redirect(_url_detalle_seguimiento(seguimiento))
        messages.error(request, "Revise los campos marcados en rojo.")
        return render(request, self.template_name, self._contexto(seguimiento, editor))


class SeguimientoRevisionCoordinadorView(LoginRequiredMixin, View):
    """Revisión del coordinador (N16) sobre una instancia del ciclo."""

    http_method_names = ["post"]

    def post(self, request, **kwargs):
        seguimiento = resolver_seguimiento(self.kwargs)
        error = aplicar_revision_coordinador(request, seguimiento, "el seguimiento")
        if error:
            messages.error(request, error)
        elif seguimiento.estado_validacion == seguimiento.ESTADO_VALIDACION_VALIDADO:
            messages.success(request, "Seguimiento validado correctamente.")
        else:
            messages.success(
                request, "Seguimiento devuelto al territorial para subsanar."
            )
        return redirect(_url_detalle_seguimiento(seguimiento))


class ActaComplementariaDetailView(LoginRequiredMixin, DetailView):
    model = ActaComplementaria
    template_name = "acta_complementaria_detail.html"
    context_object_name = "acta"

    def get_queryset(self):
        return (
            ActaComplementaria.objects.filter(comedor_id=self.kwargs["comedor_pk"])
            .select_related("comedor", "tecnico")
            .prefetch_related("prestaciones")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comedor"] = self.object.comedor
        context["prestaciones"] = list(self.object.prestaciones.all())
        return context


class ActaComplementariaFormView(LoginRequiredMixin, View):
    """Alta (sin ``pk``) y edición (con ``pk``) de un acta complementaria."""

    template_name = "acta_complementaria_form.html"

    def _cargar(self):
        comedor = get_object_or_404(Comedor, pk=self.kwargs["comedor_pk"])
        acta = None
        if "pk" in self.kwargs:
            acta = get_object_or_404(
                ActaComplementaria.objects.prefetch_related("prestaciones"),
                pk=self.kwargs["pk"],
                comedor=comedor,
            )
        return comedor, acta

    def _render(self, request, comedor, acta, editor):
        return render(
            request,
            self.template_name,
            {"comedor": comedor, "acta": acta, "editor": editor},
        )

    def get(self, request, **kwargs):
        comedor, acta = self._cargar()
        return self._render(
            request, comedor, acta, ActaComplementariaEditor(comedor, acta)
        )

    def post(self, request, **kwargs):
        comedor, acta = self._cargar()
        editor = ActaComplementariaEditor(comedor, acta, data=request.POST)
        if editor.es_valido():
            guardada = editor.guardar(request.user)
            messages.success(request, "Acta complementaria guardada correctamente.")
            return redirect(
                reverse(
                    "acta_complementaria_detalle",
                    kwargs={"comedor_pk": comedor.pk, "pk": guardada.pk},
                )
            )
        messages.error(request, "Revise los campos marcados en rojo.")
        return self._render(request, comedor, acta, editor)


class ActaComplementariaEliminarView(LoginRequiredMixin, View):
    """Borrado físico del acta (confirmado desde un modal, solo POST)."""

    http_method_names = ["post"]

    def post(self, request, comedor_pk, pk):
        acta = get_object_or_404(ActaComplementaria, pk=pk, comedor_id=comedor_pk)
        acta.delete()
        messages.success(request, "Acta complementaria eliminada correctamente.")
        return redirect(reverse("relevamientos", kwargs={"comedor_pk": comedor_pk}))
