from django.contrib.auth.models import User, Group
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .forms import CustomUserChangeForm, UserCreationForm


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class UsuariosLoginView(LoginView):
    template_name = "user/login.html"


class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = "user/user_list.html"
    context_object_name = "users"
    paginate_by = 20  # Agregado para paginación
    
    def get_queryset(self):
        queryset = super().get_queryset()
        busqueda = self.request.GET.get("busqueda", "").strip()
        if busqueda:
            queryset = queryset.filter(
                Q(username__icontains=busqueda) | 
                Q(email__icontains=busqueda) |
                Q(first_name__icontains=busqueda) |
                Q(last_name__icontains=busqueda)
            )
        return queryset.order_by('username')  # Orden consistente
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Breadcrumb
        context['breadcrumb_items'] = [
            {'url': reverse_lazy('dashboard'), 'text': 'Dashboard'},
            {'url': reverse_lazy('usuarios'), 'text': 'Usuarios'},
        ]
        
        # Parámetros de búsqueda para mantener en paginación
        context['query'] = self.request.GET.get("busqueda", "")
        
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
