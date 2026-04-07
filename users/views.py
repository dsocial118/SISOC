from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group, User
from django.contrib.auth.views import (
    INTERNAL_RESET_SESSION_TOKEN,
    LoginView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import CreateView, DeleteView, FormView, ListView, UpdateView

from core.services.column_preferences import build_columns_context

from .forms import (
    BackofficeAuthenticationForm,
    BulkCredentialsUploadForm,
    CustomUserChangeForm,
    GroupForm,
    UserCreationForm,
)
from .grupos_column_config import GRUPOS_COLUMNS, GRUPOS_LIST_KEY
from .services import UsuariosService
from .services_auth import generate_temporary_password_for_user
from .services_bulk_credentials import (
    TEMPLATE_FILENAME,
    generate_bulk_credentials_template,
    process_bulk_credentials_file,
)
from .temporary_passwords import clear_temporary_password, get_temporary_password


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    required_permissions: tuple[str, ...] = tuple()
    require_all_permissions = False

    def get_required_permissions(self):
        return tuple(self.required_permissions)

    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        required_permissions = self.get_required_permissions()
        if not required_permissions:
            return False

        if self.require_all_permissions:
            return all(user.has_perm(code) for code in required_permissions)
        return any(user.has_perm(code) for code in required_permissions)


class UsuariosLoginView(LoginView):
    template_name = "user/login.html"
    authentication_form = BackofficeAuthenticationForm


@method_decorator(ensure_csrf_cookie, name="dispatch")
class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = "user/user_list.html"
    context_object_name = "users"
    required_permissions = ("auth.view_user",)

    def get_queryset(self):
        return UsuariosService.get_filtered_usuarios(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Configuracion para el componente data_table
        context.update(UsuariosService.get_usuarios_list_context(self.request))
        context["user_table_items"] = UsuariosService.build_user_table_items(
            context["users"],
            context["table_fields"],
        )
        return context


class UserCreateView(AdminRequiredMixin, CreateView):
    model = User
    form_class = UserCreationForm
    template_name = "user/user_form.html"
    success_url = reverse_lazy("usuarios")
    required_permissions = ("auth.add_user",)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actor"] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        generated_password = getattr(form, "generated_password", None)
        if generated_password:
            messages.success(
                self.request,
                (
                    "Usuario mobile creado correctamente. "
                    f"Contraseña inicial generada: {generated_password}"
                ),
            )
            self._redirect_to_user_edit = True
            return HttpResponseRedirect(self.get_success_url())
        messages.success(self.request, "Usuario creado correctamente.")
        self._redirect_to_user_edit = False
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if getattr(self, "_redirect_to_user_edit", False):
            return reverse_lazy("usuario_editar", kwargs={"pk": self.object.pk})
        return super().get_success_url()


class UserUpdateView(AdminRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = "user/user_form.html"
    success_url = reverse_lazy("usuarios")
    required_permissions = ("auth.change_user",)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actor"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = getattr(self.object, "profile", None)
        context["password_reset_requested_at"] = (
            getattr(profile, "password_reset_requested_at", None) if profile else None
        )
        temporary_password_plaintext = get_temporary_password(
            self.request.session,
            user_id=self.object.pk,
        )
        if not temporary_password_plaintext:
            temporary_password_plaintext = getattr(
                profile,
                "temporary_password_plaintext",
                None,
            )
        context["temporary_password_plaintext"] = temporary_password_plaintext
        context["temporary_password_visible"] = bool(temporary_password_plaintext)
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        if form.cleaned_data.get("password"):
            clear_temporary_password(self.request.session, user_id=self.object.pk)
        return response


class UserDeleteView(AdminRequiredMixin, DeleteView):
    model = User
    template_name = "user/user_confirm_delete.html"
    success_url = reverse_lazy("usuarios")
    required_permissions = ("auth.delete_user",)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save(update_fields=["is_active"])
        messages.success(request, "Usuario desactivado correctamente.")
        return HttpResponseRedirect(self.success_url)


class UserGenerateTemporaryPasswordView(AdminRequiredMixin, View):
    required_permissions = ("auth.change_user",)

    def post(self, request, *args, **kwargs):
        user = User.objects.select_related("profile").filter(pk=kwargs["pk"]).first()
        if not user:
            messages.error(request, "Usuario inexistente.")
            return HttpResponseRedirect(reverse("usuarios"))

        profile = getattr(user, "profile", None)
        if not getattr(profile, "password_reset_requested_at", None):
            messages.warning(
                request,
                "El usuario no tiene una solicitud pendiente de reseteo de contraseña.",
            )
            return HttpResponseRedirect(reverse("usuarios"))

        generate_temporary_password_for_user(user=user)
        messages.success(
            request,
            (
                "Se generó una nueva contraseña temporal. "
                "Puede verla en la pantalla de edición del usuario."
            ),
        )
        return HttpResponseRedirect(reverse("usuario_editar", kwargs={"pk": user.pk}))


class UserActiveView(AdminRequiredMixin, UpdateView):
    model = User
    template_name = "user/user_confirm_delete.html"
    success_url = reverse_lazy("usuarios")
    required_permissions = ("auth.delete_user",)
    fields = []

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_active = True
        self.object.save(update_fields=["is_active"])
        messages.success(request, "Usuario activado correctamente.")
        return HttpResponseRedirect(self.success_url)


class BulkCredentialsTemplateView(AdminRequiredMixin, View):
    required_permissions = (
        "auth.change_user",
        "auth.role_enviar_credenciales_masivas",
    )
    require_all_permissions = True

    def get(self, request, *args, **kwargs):
        content = generate_bulk_credentials_template()
        response = HttpResponse(
            content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{TEMPLATE_FILENAME}"'
        return response


class BulkCredentialsUploadView(AdminRequiredMixin, FormView):
    template_name = "user/bulk_credentials_form.html"
    form_class = BulkCredentialsUploadForm
    required_permissions = (
        "auth.change_user",
        "auth.role_enviar_credenciales_masivas",
    )
    require_all_permissions = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("results", None)
        context["form_title"] = "Enviar credenciales masivas"
        context["template_download_url"] = reverse("usuarios_credenciales_plantilla")
        return context

    def form_valid(self, form):
        try:
            results = process_bulk_credentials_file(
                uploaded_file=form.cleaned_data["archivo"],
                request=self.request,
            )
        except ValidationError as exc:
            form.add_error("archivo", " ".join(exc.messages))
            return self.form_invalid(form)

        summary = results["summary"]
        messages.success(
            self.request,
            (
                "Proceso finalizado. "
                f"Enviados: {summary['enviadas']} | "
                f"Actualizados: {summary['actualizadas']} | "
                f"Sin cambios: {summary['sin_cambios']} | "
                f"Rechazados: {summary['rechazadas']}"
            ),
        )
        return self.render_to_response(
            self.get_context_data(
                form=self.form_class(),
                results=results,
            )
        )


@method_decorator(ensure_csrf_cookie, name="dispatch")
class GroupListView(AdminRequiredMixin, ListView):
    model = Group
    template_name = "group/group_list.html"
    context_object_name = "groups"
    required_permissions = ("auth.view_group",)

    def get_queryset(self):
        queryset = Group.objects.annotate(
            permissions_count=Count("permissions", distinct=True)
        ).order_by("name")
        query = (self.request.GET.get("busqueda") or "").strip()
        if query:
            queryset = queryset.filter(name__icontains=query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Configuracion para el componente data_table
        context.update(
            build_columns_context(
                self.request,
                GRUPOS_LIST_KEY,
                GRUPOS_COLUMNS,
            )
        )
        context["table_actions"] = [
            {
                "label": "Editar",
                "url_name": "grupo_editar",
                "type": "editar",
                "icon": "edit",
            }
        ]
        context["query"] = (self.request.GET.get("busqueda") or "").strip()

        return context


class FirstLoginPasswordChangeView(LoginRequiredMixin, FormView):
    template_name = "user/force_password_change.html"
    form_class = SetPasswordForm
    success_url = reverse_lazy("inicio")

    def dispatch(self, request, *args, **kwargs):
        profile = getattr(request.user, "profile", None)
        if not getattr(profile, "must_change_password", False):
            return HttpResponseRedirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        profile = getattr(user, "profile", None)
        if profile:
            profile.must_change_password = False
            profile.password_changed_at = timezone.now()
            profile.initial_password_expires_at = None
            profile.password_reset_requested_at = None
            profile.temporary_password_plaintext = None
            profile.save(
                update_fields=[
                    "must_change_password",
                    "password_changed_at",
                    "initial_password_expires_at",
                    "password_reset_requested_at",
                    "temporary_password_plaintext",
                ]
            )
        update_session_auth_hash(self.request, user)
        messages.success(self.request, "Contraseña actualizada correctamente.")
        return super().form_valid(form)


class PasswordResetConfirmCustomView(PasswordResetConfirmView):
    template_name = "user/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")

    def dispatch(self, *args, **kwargs):
        """Permite POST directo con token sin requerir paso intermedio set-password."""
        request = args[0]
        token = kwargs.get("token")
        uidb64 = kwargs.get("uidb64")

        if (
            request.method == "POST"
            and token
            and token != self.reset_url_token
            and uidb64
        ):
            self.user = self.get_user(uidb64)
            if self.user and self.token_generator.check_token(self.user, token):
                self.request.session[INTERNAL_RESET_SESSION_TOKEN] = token
                self.validlink = True
                return FormView.dispatch(self, *args, **kwargs)

        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        user = form.user
        response = super().form_valid(form)

        profile = getattr(user, "profile", None)
        if profile:
            profile.must_change_password = False
            profile.password_changed_at = timezone.now()
            profile.initial_password_expires_at = None
            profile.password_reset_requested_at = None
            profile.temporary_password_plaintext = None
            profile.save(
                update_fields=[
                    "must_change_password",
                    "password_changed_at",
                    "initial_password_expires_at",
                    "password_reset_requested_at",
                    "temporary_password_plaintext",
                ]
            )

        return response


class GroupCreateView(AdminRequiredMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = "group/group_form.html"
    success_url = reverse_lazy("grupos")
    required_permissions = ("auth.add_group",)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Grupo creado correctamente.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Crear grupo"
        context["submit_text"] = "Crear grupo"
        return context


class GroupUpdateView(AdminRequiredMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = "group/group_form.html"
    success_url = reverse_lazy("grupos")
    required_permissions = ("auth.change_group",)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Grupo actualizado correctamente.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Editar grupo"
        context["submit_text"] = "Guardar cambios"
        return context


class SisocPasswordResetView(PasswordResetView):
    template_name = "user/password_reset_form.html"
    email_template_name = "user/password_reset_email.txt"
    subject_template_name = "user/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")


class SisocPasswordResetDoneView(PasswordResetDoneView):
    template_name = "user/password_reset_done.html"


class SisocPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "user/password_reset_complete.html"
