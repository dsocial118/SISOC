from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import TemplateView

from VAT.models import Asistencia, Encuentro, ParticipanteActividad
from VAT.services.encuentro_service import AsistenciaService


class RegistrarAsistenciaView(LoginRequiredMixin, TemplateView):
    template_name = "vat/centros/encuentro_asistencia.html"

    def get_encuentro(self):
        return get_object_or_404(Encuentro, pk=self.kwargs["pk"])

    def _participantes_con_estado(self, encuentro):
        """
        Retorna lista de dicts con participante + estado de asistencia actual.
        """
        participantes = (
            ParticipanteActividad.objects.filter(
                actividad_centro=encuentro.actividad_centro,
                estado="inscrito",
            )
            .select_related("ciudadano", "ciudadano__sexo")
            .order_by("ciudadano__apellido", "ciudadano__nombre")
        )
        asistencias_map = AsistenciaService.obtener_asistencias_para_encuentro(
            encuentro
        )

        resultado = []
        for p in participantes:
            asistencia = asistencias_map.get(p.id)
            resultado.append(
                {
                    "participante": p,
                    "estado": asistencia.estado if asistencia else "presente",
                    "observaciones": asistencia.observaciones if asistencia else "",
                }
            )
        return resultado

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        encuentro = self.get_encuentro()
        context["encuentro"] = encuentro
        context["participantes_con_estado"] = self._participantes_con_estado(encuentro)
        context["estado_choices"] = Asistencia.ESTADO_CHOICES
        return context

    def post(self, request, *args, **kwargs):
        encuentro = self.get_encuentro()
        participantes = ParticipanteActividad.objects.filter(
            actividad_centro=encuentro.actividad_centro,
            estado="inscrito",
        )

        datos = [
            {
                "participante_id": p.id,
                "estado": request.POST.get(f"estado_{p.id}", "ausente"),
                "observaciones": request.POST.get(f"obs_{p.id}", ""),
            }
            for p in participantes
        ]

        AsistenciaService.registrar_bulk(encuentro, datos, request.user)

        messages.success(request, "Asistencia registrada correctamente.")
        return redirect(
            reverse(
                "vat_actividadcentro_detail",
                kwargs={"pk": encuentro.actividad_centro.pk},
            )
        )
