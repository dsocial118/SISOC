from django.contrib.auth.models import User, Group
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.urls import reverse,reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .forms import CustomUserChangeForm, UserCreationForm
from .services import UsuariosService

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class UsuariosLoginView(LoginView):
    template_name = "user/login.html"


class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = "user/user_list.html"
    context_object_name = "users"

    def get_queryset(self):
        return UsuariosService.get_filtered_usuarios(self.request)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Configuración para el componente data_table
        context.update(UsuariosService.get_usuarios_list_context())
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


class GroupListView(AdminRequiredMixin, ListView):
    model = Group
    template_name = "group/group_list.html"
    context_object_name = "groups"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Configuración para el componente data_table
        context["table_headers"] = [
            {"title": "Nombre"},
        ]

        context["table_fields"] = [
            {"name": "name"},
        ]

        return context
