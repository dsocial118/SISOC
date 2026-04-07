from django.urls import path
from django.contrib.auth.views import LogoutView
from core.decorators import permissions_all_required, permissions_any_required
from users.views import (
    BulkCredentialsTemplateView,
    BulkCredentialsUploadView,
    FirstLoginPasswordChangeView,
    GroupCreateView,
    UserCreateView,
    UserDeleteView,
    GroupListView,
    GroupUpdateView,
    PasswordResetConfirmCustomView,
    UserGenerateTemporaryPasswordView,
    UserListView,
    UserUpdateView,
    UsuariosLoginView,
    UserActiveView,
)
from users.views_export import UserExportView, GroupExportView


urlpatterns = [
    path("", UsuariosLoginView.as_view(), name="login"),
    path("logout", (LogoutView.as_view()), name="logout"),
    path(
        "password/first-change/",
        FirstLoginPasswordChangeView.as_view(),
        name="password_change_required",
    ),
    path(
        "password/reset/confirm/<uidb64>/<token>/",
        PasswordResetConfirmCustomView.as_view(),
        name="password_reset_confirm_custom",
    ),
    path(
        "usuarios/",
        permissions_any_required(["auth.view_user"])(UserListView.as_view()),
        name="usuarios",
    ),
    path(
        "usuarios/exportar/",
        permissions_all_required(["auth.view_user", "auth.role_exportar_a_csv"])(
            UserExportView.as_view()
        ),
        name="usuarios_exportar",
    ),
    path(
        "usuarios/crear/",
        permissions_any_required(["auth.add_user"])(UserCreateView.as_view()),
        name="usuario_crear",
    ),
    path(
        "usuarios/editar/<int:pk>/",
        permissions_any_required(["auth.change_user"])(UserUpdateView.as_view()),
        name="usuario_editar",
    ),
    path(
        "usuarios/generar-password-temporal/<int:pk>/",
        permissions_any_required(["auth.change_user"])(
            UserGenerateTemporaryPasswordView.as_view()
        ),
        name="usuario_generar_password_temporal",
    ),
    path(
        "usuarios/credenciales-masivas/",
        permissions_all_required(
            ["auth.change_user", "auth.role_enviar_credenciales_masivas"]
        )(BulkCredentialsUploadView.as_view()),
        name="usuarios_credenciales_masivas",
    ),
    path(
        "usuarios/credenciales-masivas/plantilla/",
        permissions_all_required(
            ["auth.change_user", "auth.role_enviar_credenciales_masivas"]
        )(BulkCredentialsTemplateView.as_view()),
        name="usuarios_credenciales_plantilla",
    ),
    path(
        "usuarios/borrar/<int:pk>/",
        permissions_any_required(["auth.delete_user"])(UserDeleteView.as_view()),
        name="usuario_borrar",
    ),
    path(
        "usuarios/activar/<int:pk>/",
        permissions_any_required(["auth.delete_user"])(UserActiveView.as_view()),
        name="usuario_activar",
    ),
    path(
        "grupos/",
        permissions_any_required(["auth.view_group"])(GroupListView.as_view()),
        name="grupos",
    ),
    path(
        "grupos/exportar/",
        permissions_all_required(["auth.view_group", "auth.role_exportar_a_csv"])(
            GroupExportView.as_view()
        ),
        name="grupos_exportar",
    ),
    path(
        "grupos/crear/",
        permissions_any_required(["auth.add_group"])(GroupCreateView.as_view()),
        name="grupo_crear",
    ),
    path(
        "grupos/editar/<int:pk>/",
        permissions_any_required(["auth.change_group"])(GroupUpdateView.as_view()),
        name="grupo_editar",
    ),
]
