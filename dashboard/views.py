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
DATACALLE_CHUBUT_GROUP = "Tablero DataCalle Chubut"
DATACALLE_SANLUIS_GROUP = "Tablero DataCalle San Lus"
DATACALLE_ENTRERIOS_GROUP = "Tablero DataCalle Entre Ríos"
DATACALLE_MENDOZA_GROUP = "Tablero DataCalle Mendoza"
DATACALLE_SANJUAN_GROUP = "Tablero DataCalle San Juan"
DATACALLE_SANTACRUZ_GROUP = "Tablero DataCalle Santa Cruz"
DATACALLE_SANTAFE_GROUP = "Tablero DataCalle Santa Fe"
DATACALLE_LAPAMPA_GROUP = "Tablero DataCalle La Pampa"
DATACALLE_CATAMARCA_GROUP = "Tablero DataCalle Catamarca"


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


class DataCalleChubutDashboardView(
    LoginRequiredMixin, UserPassesTestMixin, TemplateView
):
    template_name = "dashboard_datacalle_chubut.html"
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return (
            user.is_superuser
            or user.groups.filter(
                name__in=[DATACALLE_CHUBUT_GROUP, UserGroups.ADMINISTRADOR]
            ).exists()
        )


class DataCalleSanLuisDashboardView(
    LoginRequiredMixin, UserPassesTestMixin, TemplateView
):
    template_name = "dashboard_datacalle_sanluis.html"
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return (
            user.is_superuser
            or user.groups.filter(
                name__in=[DATACALLE_SANLUIS_GROUP, UserGroups.ADMINISTRADOR]
            ).exists()
        )


class DataCalleEntreRiosDashboardView(
    LoginRequiredMixin, UserPassesTestMixin, TemplateView
):
    template_name = "dashboard_datacalle_entrerios.html"
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return (
            user.is_superuser
            or user.groups.filter(
                name__in=[DATACALLE_ENTRERIOS_GROUP, UserGroups.ADMINISTRADOR]
            ).exists()
        )


class DataCalleMendozaDashboardView(
    LoginRequiredMixin, UserPassesTestMixin, TemplateView
):
    template_name = "dashboard_datacalle_mendoza.html"
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return (
            user.is_superuser
            or user.groups.filter(
                name__in=[DATACALLE_MENDOZA_GROUP, UserGroups.ADMINISTRADOR]
            ).exists()
        )


class DataCalleSanJuanDashboardView(
    LoginRequiredMixin, UserPassesTestMixin, TemplateView
):
    template_name = "dashboard_datacalle_sanjuan.html"
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return (
            user.is_superuser
            or user.groups.filter(
                name__in=[DATACALLE_SANJUAN_GROUP, UserGroups.ADMINISTRADOR]
            ).exists()
        )


class DataCalleSantaCruzDashboardView(
    LoginRequiredMixin, UserPassesTestMixin, TemplateView
):
    template_name = "dashboard_datacalle_santacruz.html"
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return (
            user.is_superuser
            or user.groups.filter(
                name__in=[DATACALLE_SANTACRUZ_GROUP, UserGroups.ADMINISTRADOR]
            ).exists()
        )


class DataCalleSantaFeDashboardView(
    LoginRequiredMixin, UserPassesTestMixin, TemplateView
):
    template_name = "dashboard_datacalle_santafe.html"
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return (
            user.is_superuser
            or user.groups.filter(
                name__in=[DATACALLE_SANTAFE_GROUP, UserGroups.ADMINISTRADOR]
            ).exists()
        )


class DataCalleLaPampaDashboardView(
    LoginRequiredMixin, UserPassesTestMixin, TemplateView
):
    template_name = "dashboard_datacalle_lapampa.html"
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return (
            user.is_superuser
            or user.groups.filter(
                name__in=[DATACALLE_LAPAMPA_GROUP, UserGroups.ADMINISTRADOR]
            ).exists()
        )


class DataCalleCatamarcaDashboardView(
    LoginRequiredMixin, UserPassesTestMixin, TemplateView
):
    template_name = "dashboard_datacalle_catamarca.html"
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return (
            user.is_superuser
            or user.groups.filter(
                name__in=[DATACALLE_CATAMARCA_GROUP, UserGroups.ADMINISTRADOR]
            ).exists()
        )
