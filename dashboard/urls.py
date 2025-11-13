from django.contrib.auth.decorators import login_required
from django.urls import path

from dashboard.views import DashboardView, DataCalleChacoDashboardView

urlpatterns = [
    path("dashboard/", login_required(DashboardView.as_view()), name="dashboard"),
    path(
        "dashboard/datacalle-chaco/",
        login_required(DataCalleChacoDashboardView.as_view()),
        name="dashboard_datacalle_chaco",
    ),
]
