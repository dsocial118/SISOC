from django.contrib.auth.decorators import login_required
from django.urls import path

from dashboard.views import DashboardView

urlpatterns = [
    path("dashboard/", login_required(DashboardView.as_view()), name="dashboard"),
]
