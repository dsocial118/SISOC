from django.urls import path
from .views import (
    UserListView,
    UserCreateView,
    UserUpdateView,
    UserDeleteView,
    GroupListView,
    GroupCreateView,
    GroupUpdateView,
    GroupDeleteView,
)

urlpatterns = [
    # Usuarios
    path("usuarios/", UserListView.as_view(), name="usuarios"),
    path("usuarios/crear/", UserCreateView.as_view(), name="usuario_crear"),
    path("usuarios/editar/<int:pk>/", UserUpdateView.as_view(), name="usuario_editar"),
    path("usuarios/borrar/<int:pk>/", UserDeleteView.as_view(), name="usuario_borrar"),
    # Grupos
    path("grupos/", GroupListView.as_view(), name="grupos"),
    path("grupos/crear/", GroupCreateView.as_view(), name="grupo_crear"),
    path("grupos/editar/<int:pk>/", GroupUpdateView.as_view(), name="grupo_editar"),
    path("grupos/borrar/<int:pk>/", GroupDeleteView.as_view(), name="grupo_borrar"),
]
