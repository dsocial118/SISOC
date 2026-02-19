from django.contrib.auth.models import User, Group
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views.decorators.csrf import ensure_csrf_cookie
from core.services.column_preferences import build_columns_context
from .forms import (
    BackofficeAuthenticationForm,
    CustomUserChangeForm,
    UserCreationForm,
)
from .grupos_column_config import GRUPOS_COLUMNS, GRUPOS_LIST_KEY
from .services import UsuariosService


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class UsuariosLoginView(LoginView):
    template_name = "user/login.html"
    authentication_form = BackofficeAuthenticationForm


@method_decorator(ensure_csrf_cookie, name="dispatch")
class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = "user/user_list.html"
    context_object_name = "users"

    def get_queryset(self):
        return UsuariosService.get_filtered_usuarios(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Configuración para el componente data_table
        context.update(UsuariosService.get_usuarios_list_context(self.request))
        return context


class UserCreateView(AdminRequiredMixin, CreateView):
    model = User
    form_class = UserCreationForm
    template_name = "user/user_form.html"
    success_url = reverse_lazy("usuarios")


class UserUpdateView(AdminRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = "user/user_form.html"
    success_url = reverse_lazy("usuarios")


class UserDeleteView(AdminRequiredMixin, DeleteView):
    model = User
    template_name = "user/user_confirm_delete.html"
    success_url = reverse_lazy("usuarios")


@method_decorator(ensure_csrf_cookie, name="dispatch")
class GroupListView(AdminRequiredMixin, ListView):
    model = Group
    template_name = "group/group_list.html"
    context_object_name = "groups"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Configuración para el componente data_table
        context.update(
            build_columns_context(
                self.request,
                GRUPOS_LIST_KEY,
                GRUPOS_COLUMNS,
            )
        )

        return context
