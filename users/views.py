from django.contrib.auth.models import User, Group
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .forms import UserCreationForm


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = "user/user_list.html"
    context_object_name = "users"


class UserCreateView(AdminRequiredMixin, CreateView):
    model = User
    form_class = UserCreationForm
    template_name = "user/user_form.html"
    success_url = reverse_lazy("usuarios")


class UserUpdateView(AdminRequiredMixin, UpdateView):
    model = User
    form_class = UserCreationForm
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


class GroupCreateView(AdminRequiredMixin, CreateView):
    model = Group
    fields = ["name"]
    template_name = "group/group_form.html"
    success_url = reverse_lazy("grupos")


class GroupUpdateView(AdminRequiredMixin, UpdateView):
    model = Group
    fields = ["name"]
    template_name = "group/group_form.html"
    success_url = reverse_lazy("grupos")


class GroupDeleteView(AdminRequiredMixin, DeleteView):
    model = Group
    template_name = "group/group_confirm_delete.html"
    success_url = reverse_lazy("grupos")
