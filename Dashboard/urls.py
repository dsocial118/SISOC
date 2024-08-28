from django.contrib.auth.decorators import login_required
from django.urls import path

from Dashboard.views import DashboardView

urlpatterns = [
    path("dashboard/", login_required(DashboardView.as_view()), name="dashboard"),
]
