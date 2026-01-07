from django.contrib.auth.decorators import login_required
from django.urls import path

from dashboard.views import DashboardView, TableroEmbedView

urlpatterns = [
    path(
        "dashboard/centro-de-familia",
        login_required(DashboardView.as_view()),
        name="dashboard",
    ),
    path(
        "dashboard/<slug:slug>/",
        login_required(TableroEmbedView.as_view()),
        name="dashboard_tablero",
    ),
]
