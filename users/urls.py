from django.urls import path
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import login_required
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
    path("logout", login_required(LogoutView.as_view()), name="logout"),
    # Usuarios
    path("usuarios/", login_required(UserListView.as_view()), name="usuarios"),
    path(
        "usuarios/crear/",
        login_required(UserCreateView.as_view()),
        name="usuario_crear",
    ),
    path(
        "usuarios/editar/<int:pk>/",
        login_required(UserUpdateView.as_view()),
        name="usuario_editar",
    ),
    path(
        "usuarios/borrar/<int:pk>/",
        login_required(UserDeleteView.as_view()),
        name="usuario_borrar",
    ),
    # Grupos
    path("grupos/", login_required(GroupListView.as_view()), name="grupos"),
]
