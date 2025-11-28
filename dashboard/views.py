from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView

from core.constants import UserGroups
from dashboard.models import Dashboard
from centrodefamilia.models import Centro, ActividadCentro, ParticipanteActividad

DATACALLE_CHACO_GROUP = "Tablero DataCalle Chaco"
DATACALLE_MISIONES_GROUP = "Tablero DataCalle Misiones"
DATACALLE_SALTA_GROUP = "Tablero DataCalle Salta"
DATACALLE_CORRIENTES_GROUP = "Tablero DataCalle Corrientes"
DATACALLE_GENERAL_GROUP = "Tablero DataCalle General"


class DashboardView(LoginRequiredMixin, TemplateView):
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

        context["centros_faro_totales"] = Centro.objects.filter(tipo="faro").count()

        context["actividades_totales"] = ActividadCentro.objects.count()

        return context


class DataCalleChacoDashboardView(
    LoginRequiredMixin, UserPassesTestMixin, TemplateView
):
    template_name = "dashboard_datacalle_chaco.html"
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return (
            user.is_superuser
            or user.groups.filter(
                name__in=[DATACALLE_CHACO_GROUP, UserGroups.ADMINISTRADOR]
            ).exists()
        )

class DataCalleSaltaDashboardView(
    LoginRequiredMixin, UserPassesTestMixin, TemplateView
):
    template_name = "dashboard_datacalle_salta.html"
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return (
            user.is_superuser
            or user.groups.filter(
                name__in=[DATACALLE_SALTA_GROUP, UserGroups.ADMINISTRADOR]
            ).exists()
        )

class DataCalleCorrientesDashboardView(
    LoginRequiredMixin, UserPassesTestMixin, TemplateView
):
    template_name = "dashboard_datacalle_corrientes.html"
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return (
            user.is_superuser
            or user.groups.filter(
                name__in=[DATACALLE_CORRIENTES_GROUP, UserGroups.ADMINISTRADOR]
            ).exists()
        )

class DataCalleMisionesDashboardView(
    LoginRequiredMixin, UserPassesTestMixin, TemplateView
):
    template_name = "dashboard_datacalle_misiones.html"
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return (
            user.is_superuser
            or user.groups.filter(
                name__in=[DATACALLE_MISIONES_GROUP, UserGroups.ADMINISTRADOR]
            ).exists()
        )


class DataCalleGeneralDashboardView(
    LoginRequiredMixin, UserPassesTestMixin, TemplateView
):
    template_name = "dashboard_datacalle_general.html"
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return (
            user.is_superuser
            or user.groups.filter(
                name__in=[DATACALLE_GENERAL_GROUP, UserGroups.ADMINISTRADOR]
            ).exists()
        )
