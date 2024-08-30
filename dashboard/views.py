from django.views.generic import TemplateView

from dashboard.models import Dashboard


class DashboardView(TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        dashboard_data = Dashboard.objects.all()
        data = {item.llave: item.cantidad for item in dashboard_data}

        context.update(data)

        return context
