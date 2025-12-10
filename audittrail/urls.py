from django.urls import path

from audittrail import views

app_name = "audittrail"

urlpatterns = [
    path("auditoria/", views.AuditLogListView.as_view(), name="log_list"),
    path(
        "auditoria/<str:app_label>/<str:model_name>/<str:object_pk>/",
        views.AuditLogInstanceView.as_view(),
        name="log_instance",
    ),
    path(
        "auditoria/evento/<int:pk>/",
        views.AuditLogDetailView.as_view(),
        name="log_detail",
    ),
]
