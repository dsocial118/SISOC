from django.contrib.auth.decorators import login_required
from django.urls import path

from dashboard.views import (
    DashboardView,
    DataCalleChacoDashboardView,
    DataCalleGeneralDashboardView,
)

urlpatterns = [
    path("dashboard/centro-de-familia", login_required(DashboardView.as_view()), name="dashboard"),
    path(
        "dashboard/datacalle-general-chaco/",
        login_required(DataCalleChacoDashboardView.as_view()),
        name="dashboard_datacalle_chaco",
    ),
    path(
        "dashboard/datacalle-general/",
        login_required(DataCalleGeneralDashboardView.as_view()),
        name="dashboard_datacalle_general",
    ),
]
