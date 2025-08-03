from django.views.generic import TemplateView

from dashboard.models import Dashboard
from centrodefamilia.models import Centro, ActividadCentro, ParticipanteActividad


class DashboardView(TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 1) Datos fijos
        dashboard_data = Dashboard.objects.all()
        context.update({item.llave: item.cantidad for item in dashboard_data})

        # 2) Indicadores dinámicos
        context["participantes_total"] = ParticipanteActividad.objects.filter(
            estado="inscrito"
        ).count()

        context["centros_adheridos_totales"] = Centro.objects.filter(
            tipo="adherido"
        ).count()

        context["centros_faro_totales"] = Centro.objects.filter(
            tipo="faro"
        ).count()

        context["actividades_totales"] = ActividadCentro.objects.count()

        return context
