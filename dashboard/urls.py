from django.contrib.auth.decorators import login_required
from django.urls import path

from dashboard.views import (
    DashboardView,
    DataCalleChacoDashboardView,
    DataCalleCorrientesDashboardView,
    DataCalleSaltaDashboardView,
    DataCalleMisionesDashboardView,
    DataCalleGeneralDashboardView,
)

urlpatterns = [
    path(
        "dashboard/centro-de-familia",
        login_required(DashboardView.as_view()),
        name="dashboard",
    ),
    path(
        "dashboard/datacalle-general-chaco/",
        login_required(DataCalleChacoDashboardView.as_view()),
        name="dashboard_datacalle_chaco",
    ),
    path(
        "dashboard/datacalle-general-salta/",
        login_required(DataCalleSaltaDashboardView.as_view()),
        name="dashboard_datacalle_salta",
    ),
    path(
        "dashboard/datacalle-general-corrientes/",
        login_required(DataCalleCorrientesDashboardView.as_view()),
        name="dashboard_datacalle_corrientes",
    ),
    path(
        "dashboard/datacalle-general-misiones/",
        login_required(DataCalleMisionesDashboardView.as_view()),
        name="dashboard_datacalle_misiones",
    ),
    path(
        "dashboard/datacalle-general/",
        login_required(DataCalleGeneralDashboardView.as_view()),
        name="dashboard_datacalle_general",
    ),
]
