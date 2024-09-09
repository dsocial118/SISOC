from django.views.generic import TemplateView

from dashboard.services import DashboardService


class DashboardView(TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(DashboardService.obtener_dashboard_data())
        return context
