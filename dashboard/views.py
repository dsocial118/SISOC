from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import DetailView, TemplateView

from centrodefamilia.api import obtener_metricas_dashboard
from dashboard.models import Dashboard, Tablero


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 1) Datos fijos
        dashboard_data = Dashboard.objects.all()
        context.update({item.llave: item.cantidad for item in dashboard_data})

        # 2) Indicadores dinámicos
        metricas_cdf = obtener_metricas_dashboard()
        context.update(metricas_cdf.__dict__)

        return context


class TableroEmbedView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Muestra tableros embebidos configurados desde el admin."""

    model = Tablero
    template_name = "dashboard_tablero.html"
    slug_url_kwarg = "slug"
    context_object_name = "tablero"
    raise_exception = True

    def get_queryset(self):
        return Tablero.objects.filter(activo=True)

    def test_func(self):
        tablero = self.get_object()
        return tablero.usuario_puede_ver(self.request.user)
