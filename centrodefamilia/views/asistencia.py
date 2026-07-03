"""Toma de asistencia de una actividad de Centro de Familia.

Copia el flujo de ``VAT.views.oferta_institucional.AsistenciaSesionView``
adaptado a CDF: la planilla es por (actividad, fecha) sobre los inscritos.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import TemplateView

from centrodefamilia.access import puede_tomar_asistencia_cdf
from centrodefamilia.models import ActividadCentro
from centrodefamilia.services.asistencia import AsistenciaActividadService


class AsistenciaActividadView(LoginRequiredMixin, TemplateView):
    """
    GET: planilla de inscritos para tomar asistencia en una fecha (hoy por defecto).
    POST: guarda/actualiza los registros de AsistenciaActividad de esa fecha.
    """

    template_name = "centros/actividadcentro_asistencia.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        self.actividad = get_object_or_404(
            ActividadCentro.objects.select_related(
                "centro", "actividad", "actividad__categoria"
            ),
            pk=kwargs["pk"],
        )
        if not puede_tomar_asistencia_cdf(request.user, self.actividad.centro):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def _fecha_or_error(self, raw):
        try:
            return AsistenciaActividadService.parse_fecha(raw), None
        except ValidationError as exc:
            return AsistenciaActividadService.parse_fecha(None), exc.messages[0]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fecha, fecha_error = self._fecha_or_error(self.request.GET.get("fecha"))
        filas = AsistenciaActividadService.obtener_planilla(self.actividad, fecha)
        presentes = sum(1 for fila in filas if fila["presente"] is True)
        ausentes = sum(1 for fila in filas if fila["presente"] is False)
        context.update(
            {
                "actividad": self.actividad,
                "centro": self.actividad.centro,
                "fecha": fecha,
                "fecha_error": fecha_error,
                "filas": filas,
                "ya_tomada": any(fila["presente"] is not None for fila in filas),
                "total_presentes": presentes,
                "total_ausentes": ausentes,
                "total_sin_marcar": len(filas) - presentes - ausentes,
                "detalle_url": reverse(
                    "actividadcentro_detail", kwargs={"pk": self.actividad.pk}
                ),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        try:
            fecha = AsistenciaActividadService.parse_fecha(request.POST.get("fecha"))
        except ValidationError as exc:
            messages.error(request, exc.messages[0])
            return redirect("actividadcentro_asistencia", pk=self.actividad.pk)

        inscritos = AsistenciaActividadService.inscritos(self.actividad)
        marcas = {
            participante.pk: request.POST.get(f"presente_{participante.pk}")
            for participante in inscritos
        }
        guardados = AsistenciaActividadService.registrar(
            self.actividad, fecha, marcas, request.user, participantes=inscritos
        )
        messages.success(
            request,
            f"Asistencia del {fecha:%d/%m/%Y} registrada para {guardados} participante(s).",
        )
        url = reverse("actividadcentro_asistencia", kwargs={"pk": self.actividad.pk})
        return redirect(f"{url}?fecha={fecha:%Y-%m-%d}")
