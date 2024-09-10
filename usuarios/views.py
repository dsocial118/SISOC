from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import (
    LoginView,
    PasswordChangeView,
    PasswordResetView,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.core.files.base import ContentFile
from django.db.models import Q

# region---------------------------------------------------------------------------------------USUARIOS
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib.auth.models import Group, User
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from usuarios.forms import (
    GruposUsuariosForm,
    MyPasswordChangeForm,
    MyResetPasswordForm,
    PerfilUpdateForm,
    UsuariosCreateForm,
    UsuariosUpdateForm,
)
from usuarios.models import Usuarios
from usuarios.utils import recortar_imagen

from .mixins import PermisosMixin


ROL_ADMIN = "Usuarios.rol_admin"
ROL_OBSERVADOR = "Usuarios.rol_observador"
ROL_CONSULTANTE = "Usuarios.rol_consultante"


def set_dark_mode(request):
    if request.method == "POST":
        user = request.user
        if user.usuarios.darkmode:
            user.usuarios.darkmode = False
        else:
            user.usuarios.darkmode = True
        user.usuarios.save()
        return JsonResponse({"status": "ok"})
    return None


class UsuariosLoginView(LoginView):
    template_name = "login.html"


class UsuariosListView(PermisosMixin, ListView):
    permission_required = [
        ROL_ADMIN,
        ROL_OBSERVADOR,
        ROL_CONSULTANTE,
    ]
    model = Usuarios

    # Funcion de busqueda
    def get_queryset(self):
        query = self.request.GET.get("busqueda")
        if query:
            # Separa el término de búsqueda en nombre y apellido
            terminos = query.split()
            nombre = terminos[0]
            apellido = terminos[-1]

            object_list = self.model.objects.filter(
                Q(usuario__username__icontains=query)
                | Q(usuario__first_name__icontains=nombre)
                & Q(usuario__last_name__icontains=apellido)
                | Q(usuario__first_name__icontains=query)
                | Q(usuario__last_name__icontains=query)
                | Q(usuario__email__icontains=query)
                | Q(telefono__icontains=query)
            ).distinct()
        else:
            object_list = self.model.objects.all().exclude(
                usuario_id__is_superuser=True
            )
        return object_list


class UsuariosDetailView(UserPassesTestMixin, DetailView):
    permission_required = [
        ROL_ADMIN,
        ROL_OBSERVADOR,
        ROL_CONSULTANTE,
    ]
    model = Usuarios
    template_name = "Usuarios/usuarios_detail.html"

    def test_func(self):
        # accede a la vista de detalle si es admin o si es el mismo usuario
        if self.request.user.is_authenticated:
            usuario_actual = self.request.user.id
            usuario_solicitado = int(self.kwargs["pk"])
            if (
                (usuario_actual == usuario_solicitado)
                or self.request.user.has_perm(ROL_ADMIN)
                or self.request.user.has_perm("auth_user.view_user")
            ):
                return True
        return False


class UsuariosDeleteView(PermisosMixin, SuccessMessageMixin, DeleteView):
    permission_required = ROL_ADMIN
    model = Usuarios
    template_name = "Usuarios/usuarios_confirm_delete.html"
    success_url = reverse_lazy("usuarios_listar")
    success_message = "El registro fue eliminado correctamente"


class UsuariosCreateView(PermisosMixin, SuccessMessageMixin, CreateView):
    permission_required = ROL_ADMIN
    template_name = "Usuarios/usuarios_create_form.html"
    form_class = UsuariosCreateForm
    model = User

    def form_valid(self, form):
        dni = form.cleaned_data["dni"]
        img = self.request.FILES.get("imagen")
        telefono = form.cleaned_data["telefono"]
        groups = form.cleaned_data.get("groups")
        if form.is_valid():
            try:
                user = form.save()
                if groups:
                    user.groups.set(
                        groups
                    )  # Asigna los grupos seleccionados al usuario
                usuario = Usuarios.objects.get(usuario_id=user.id)
                if dni:
                    usuario.dni = dni
                if telefono:
                    usuario.telefono = telefono
                if img:
                    buffer = recortar_imagen(img)
                    usuario.imagen.save(img.name, ContentFile(buffer.getvalue()))

                usuario.save()
                messages.success(self.request, ("Usuario creado con éxito."))
                return redirect("usuarios_ver", user.usuarios.id)

            except Exception as e:
                messages.error(self.request, (f"No fue posible crear el usuario: {e}"))
                user.delete()
                return redirect("usuarios_listar")
        return None


class UsuariosUpdateView(PermisosMixin, SuccessMessageMixin, UpdateView):
    permission_required = ROL_ADMIN
    model = User
    form_class = UsuariosUpdateForm
    template_name = "Usuarios/usuarios_update_form.html"

    def form_valid(self, form):
        dni = form.cleaned_data["dni"]
        img = self.request.FILES.get("imagen")
        telefono = form.cleaned_data["telefono"]

        if form.is_valid():
            user = form.save()
            usuario = Usuarios.objects.get(usuario_id=user.id)

            if dni:
                usuario.dni = dni

            if telefono:
                usuario.telefono = telefono

            if img:
                buffer = recortar_imagen(img)
                usuario.imagen.save(img.name, ContentFile(buffer.getvalue()))

            usuario.save()
            messages.success(self.request, ("Usuario modificado con éxito."))
            return redirect("usuarios_ver", user.usuarios.id)

        return None


# endregion------------------------------------------------------------------------------------------


# region---------------------------------------------------------------------------------------PASSWORDS


class UsuariosResetPassView(PermisosMixin, SuccessMessageMixin, PasswordResetView):
    """
    Permite al usuario staff resetear la clave a otros usuarios del sistema mediante el envío de un token por mail.
    IMPORTANTE: el mail  al que se envía el token de recupero debe coincidir con el mail que el usuario tiene
    almacenado en su perfil, por lo cual es imprescindible chequear que sea correcto.

    De la documentación de Django:
        Given an email, return matching user(s) who should receive a reset.
        This allows subclasses to more easily customize the default policies
        that prevent inactive users and users with unusable passwords from
        resetting their password.
    """

    permission_required = ROL_ADMIN
    template_name = "Passwords/password_reset.html"
    form_class = MyResetPasswordForm
    success_url = reverse_lazy("usuarios_listar")
    success_message = "Mail de reseteo de contraseña enviado con éxito."

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs["pk"]
        user = User.objects.get(id=user_id)
        email = user.email
        context["email"] = email
        context["user"] = user
        return context


# endregion


# region---------------------------------------------------------------------------------------PERFILES DE USUARIOS


class PerfilUpdateView(UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    """
    Vista para que los usuarios logueados (no staff) realicen cambios en sus datos de perfil.
    De la tabla USER: Nombre de usuario, Nombre, Apellido o email.
    De la tabla USUARIOS(extensión del modelo USER): telefono.
    """

    model = User
    form_class = PerfilUpdateForm
    template_name = "Perfiles/perfil_update_form.html"
    success_message = "Perfil editado con éxito."

    def test_func(self):
        # accede a la vista si es el mismo usuario
        if self.request.user.is_authenticated:
            usuario_actual = self.request.user.id
            usuario_solicitado = int(self.kwargs["pk"])
            if usuario_actual == usuario_solicitado:
                return True
        return False

    def form_valid(self, form):
        img = self.request.FILES.get("imagen")
        telefono = form.cleaned_data["telefono"]
        dni = form.cleaned_data["dni"]
        if form.is_valid():
            user = form.save()
            usuario = Usuarios.objects.get(usuario_id=user.id)
            if dni:
                usuario.dni = dni
            if telefono:
                usuario.telefono = telefono
            # Verificar si la imagen ha cambiado antes de recortarla y guardarla
            if img:
                buffer = recortar_imagen(img)
                usuario.imagen.save(img.name, ContentFile(buffer.getvalue()))
            usuario.save()
            messages.success(self.request, ("Perfil modificado con éxito."))
        else:
            messages.error(self.request, ("No fue posible modificar el perfil."))
        return redirect("usuarios_ver", pk=user.id)


class PerfilChangePassView(LoginRequiredMixin, SuccessMessageMixin, PasswordChangeView):
    """
    Vista para que los usuarios logueados (no staff) realicen cambios de clave.
    Es requisito conocer su clave anterior e introducir una nueva contraseña que cumpla con los requisitos del sistema.
    """

    template_name = "Perfiles/perfil_change_password.html"
    form_class = MyPasswordChangeForm
    success_url = reverse_lazy("legajos_listar")
    success_message = "La contraseña fue modificada con éxito."


# endregion


# region---------------------------------------------------------------------------------------GRUPOS DE USUARIOS


class GruposListView(PermisosMixin, ListView):
    permission_required = [
        ROL_ADMIN,
        ROL_OBSERVADOR,
        ROL_CONSULTANTE,
    ]
    model = Group
    template_name = "Grupos/grupos_list.html"

    # Funcion de busqueda
    def get_queryset(self):
        query = self.request.GET.get("busqueda")
        if query:
            object_list = self.model.objects.filter(
                Q(permissions__codename__icontains=query) | Q(name__icontains=query)
            ).distinct()
        else:
            object_list = self.model.objects.all().order_by("name")
        return object_list


class GruposDetailView(PermisosMixin, DetailView):
    permission_required = [
        "auth_user.view_group",
        ROL_ADMIN,
        ROL_OBSERVADOR,
        ROL_CONSULTANTE,
    ]
    model = Group
    template_name = "Grupos/grupos_detail.html"


class GruposDeleteView(PermisosMixin, SuccessMessageMixin, DeleteView):
    permission_required = ("auth_user.delete_group", ROL_ADMIN)
    model = Group
    template_name = "Grupos/grupos_confirm_delete.html"
    success_url = reverse_lazy("grupos_listar")
    success_message = "El registro fue eliminado correctamente"


class GruposCreateView(PermisosMixin, SuccessMessageMixin, CreateView):
    permission_required = ROL_ADMIN
    model = Group
    form_class = GruposUsuariosForm
    template_name = "Grupos/grupos_form.html"
    success_message = "%(name)s fue registrado correctamente"

    def form_valid(self, form):
        if form.is_valid():
            programa = form.cleaned_data["programa"]
            permiso = form.cleaned_data["permiso"]
            creator_permissions = [
                programa.id,
                permiso.id,
            ]
            grupo = form.save()
            grupo.permissions.set(creator_permissions)
            return redirect("grupos_ver", pk=grupo.id)
        return None

    def form_invalid(self, form):
        print("selfie", form.cleaned_data)
        if "programa" not in form.cleaned_data or "permiso" not in form.cleaned_data:
            messages.error(self.request, "Complete los campos")
            return self.render_to_response(self.get_context_data(form=form))

        messages.error(self.request, "Ya existe un grupo con esos permisos")
        return self.render_to_response(self.get_context_data(form=form))


class GruposUpdateView(PermisosMixin, SuccessMessageMixin, UpdateView):
    permission_required = ROL_ADMIN
    model = Group
    form_class = GruposUsuariosForm
    template_name = "Grupos/grupos_form.html"
    success_message = "%(name)s fue editado correctamente"

    def form_valid(self, form):
        if form.is_valid():
            programa = form.cleaned_data["programa"]
            permiso = form.cleaned_data["permiso"]
            creator_permissions = [
                programa.id,
                permiso.id,
            ]
            grupo = form.save()
            grupo.permissions.set(creator_permissions)
            return redirect("grupos_ver", pk=grupo.id)

        return None

    def form_invalid(self, form):
        if "programa" not in form.cleaned_data or "permiso" not in form.cleaned_data:
            messages.error(self.request, "Complete los campos")
            return self.render_to_response(self.get_context_data(form=form))

        return None


# endregion------------------------------------------------------------------------------------------
