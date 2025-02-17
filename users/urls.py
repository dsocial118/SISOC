from django.urls import path
from django.contrib.auth.views import LogoutView
from configuraciones.decorators import group_required
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
    path("logout", group_required("Admin")(LogoutView.as_view()), name="logout"),
    # Usuarios
    path("usuarios/", group_required("Admin")(UserListView.as_view()), name="usuarios"),
    path(
        "usuarios/crear/",
        group_required("Admin")(UserCreateView.as_view()),
        name="usuario_crear",
    ),
    path(
        "usuarios/editar/<int:pk>/",
        group_required("Admin")(UserUpdateView.as_view()),
        name="usuario_editar",
    ),
    path(
        "usuarios/borrar/<int:pk>/",
        group_required("Admin")(UserDeleteView.as_view()),
        name="usuario_borrar",
    ),
    # Grupos
    path("grupos/", group_required("Admin")(GroupListView.as_view()), name="grupos"),
]
