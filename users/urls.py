from django.urls import path
from django.contrib.auth.views import LogoutView
from core.decorators import group_required
from users.views import (
    UsuariosLoginView,
    UserListView,
    UserCreateView,
    UserUpdateView,
    UserDeleteView,
    GroupListView,
)

urlpatterns = [
    path("", UsuariosLoginView.as_view(), name="login"),
    path("logout", (LogoutView.as_view()), name="logout"),
    # Usuarios
    path(
        "usuarios/",
        group_required("Usuario Ver")(UserListView.as_view()),
        name="usuarios",
    ),
    path(
        "usuarios/crear/",
        group_required("Usuario Crear")(UserCreateView.as_view()),
        name="usuario_crear",
    ),
    path(
        "usuarios/editar/<int:pk>/",
        group_required("Usuario Editar")(UserUpdateView.as_view()),
        name="usuario_editar",
    ),
    path(
        "usuarios/borrar/<int:pk>/",
        group_required("Usuario Eliminar")(UserDeleteView.as_view()),
        name="usuario_borrar",
    ),
    # Grupos
    path(
        "grupos/",
        group_required("Grupos Ver")(GroupListView.as_view()),
        name="grupos",
    ),
]
