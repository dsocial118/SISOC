from datetime import timedelta

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group, Permission, User
from django.db import transaction
from django.utils import timezone

from comedores.models import Comedor
from core.models import Provincia
from duplas.models import Dupla
from organizaciones.models import Organizacion
from users.models import AccesoComedorPWA, Profile
from users.services_pwa import (
    deactivate_representante_accesses,
    is_pwa_user,
    sync_representante_accesses,
)


ROLE_PERMISSION_QUERYSET = (
    Permission.objects.select_related("content_type")
    .filter(
        content_type__app_label="auth",
        codename__startswith="role_",
    )
    .order_by("name")
)


class BackofficeAuthenticationForm(AuthenticationForm):
    """Bloquea login web para usuarios de uso exclusivo PWA."""

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if is_pwa_user(user):
            raise forms.ValidationError(
                "Este usuario solo puede ingresar desde la PWA.",
                code="pwa_only",
            )
        profile = getattr(user, "profile", None)
        expires_at = getattr(profile, "initial_password_expires_at", None)
        if (
            getattr(profile, "must_change_password", False)
            and expires_at
            and expires_at <= timezone.now()
        ):
            raise forms.ValidationError(
                "La contraseña inicial expiró. Solicite un reinicio a un administrador.",
                code="initial_password_expired",
            )


class UserLoginForm(BackofficeAuthenticationForm):
    """Compatibilidad para configuraciones existentes."""


class PWAAccessMixin:
    def _setup_pwa_fields(self):
        self.fields["es_representante_pwa"] = forms.BooleanField(
            required=False,
            label="Es representante PWA",
        )
        self.fields["organizaciones_pwa"] = forms.ModelMultipleChoiceField(
            queryset=Organizacion.objects.all().order_by("nombre"),
            required=False,
            widget=forms.SelectMultiple(attrs={"class": "select2"}),
            label="Organizaciones PWA",
            help_text="Organizaciones habilitadas para construir el alcance en la PWA.",
        )
        self.fields["comedores_pwa"] = forms.ModelMultipleChoiceField(
            queryset=Comedor.objects.all().order_by("nombre"),
            required=False,
            widget=forms.SelectMultiple(attrs={"class": "select2"}),
            label="Comedores PWA",
            help_text="Comedores que este usuario representa en la PWA.",
        )

    def _init_pwa_fields(self):
        if not self.instance or not self.instance.pk:
            return
        accesos = AccesoComedorPWA.objects.filter(
            user=self.instance,
            rol=AccesoComedorPWA.ROL_REPRESENTANTE,
            activo=True,
        )
        organizacion_ids = list(
            accesos.exclude(organizacion_id__isnull=True)
            .values_list("organizacion_id", flat=True)
            .distinct()
        )
        comedor_ids = list(accesos.values_list("comedor_id", flat=True))
        self.fields["es_representante_pwa"].initial = bool(comedor_ids)
        self.fields["organizaciones_pwa"].initial = organizacion_ids
        self.fields["comedores_pwa"].initial = comedor_ids

    def _clean_pwa_fields(self, cleaned):
        es_representante_pwa = cleaned.get("es_representante_pwa", False)
        comedores_pwa = cleaned.get("comedores_pwa")
        es_coordinador = cleaned.get("es_coordinador", False)

        if es_representante_pwa and not comedores_pwa:
            self.add_error(
                "comedores_pwa",
                "Debe seleccionar al menos un comedor para un representante PWA.",
            )
        if not es_representante_pwa and comedores_pwa:
            self.add_error(
                "es_representante_pwa",
                "Marque este campo para asignar comedores PWA.",
            )
        if es_representante_pwa and es_coordinador:
            self.add_error(
                "es_coordinador",
                "Un representante PWA no puede ser coordinador de equipo técnico.",
            )
        if es_representante_pwa and self.instance and self.instance.pk:
            if AccesoComedorPWA.objects.filter(
                user=self.instance,
                rol=AccesoComedorPWA.ROL_OPERADOR,
                activo=True,
            ).exists():
                self.add_error(
                    "es_representante_pwa",
                    "No se puede asignar representante PWA a un usuario operador activo.",
                )

        return cleaned

    def _sync_pwa_access(self, user):
        if self.cleaned_data.get("es_representante_pwa"):
            sync_representante_accesses(
                user=user,
                comedor_ids=self.cleaned_data["comedores_pwa"].values_list(
                    "id", flat=True
                ),
                actor=None,
            )
            return
        deactivate_representante_accesses(user)

    def _validate_required_email(self, cleaned):
        email = (cleaned.get("email") or "").strip()
        if not email:
            self.add_error("email", "Este campo es obligatorio.")
            return cleaned

        qs = User.objects.filter(email__iexact=email)
        if getattr(self.instance, "pk", None):
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            self.add_error("email", "Ya existe un usuario con ese email.")
            return cleaned

        cleaned["email"] = email
        return cleaned


class DelegationScopeMixin:
    actor = None

    def _setup_delegation_fields(self):
        self.fields["grupos_asignables"] = forms.ModelMultipleChoiceField(
            queryset=Group.objects.all().order_by("name"),
            required=False,
            widget=forms.SelectMultiple(attrs={"class": "select2"}),
            label="Grupos que puede asignar",
            help_text=(
                "Define qué grupos podrá asignar este usuario al crear/editar "
                "otros usuarios."
            ),
        )
        self.fields["roles_asignables"] = forms.ModelMultipleChoiceField(
            queryset=ROLE_PERMISSION_QUERYSET,
            required=False,
            widget=forms.SelectMultiple(attrs={"class": "select2"}),
            label="Roles que puede asignar",
            help_text="Permisos auth.role_* delegables a terceros.",
        )

    def _is_unrestricted_actor(self):
        return not self.actor or self.actor.is_superuser

    def _allowed_groups_for_actor(self):
        if self._is_unrestricted_actor():
            return Group.objects.all().order_by("name")

        profile = getattr(self.actor, "profile", None)
        if not profile:
            return Group.objects.none()
        return profile.grupos_asignables.all().order_by("name")

    def _allowed_roles_for_actor(self):
        if self._is_unrestricted_actor():
            return ROLE_PERMISSION_QUERYSET

        profile = getattr(self.actor, "profile", None)
        if not profile:
            return Permission.objects.none()
        return profile.roles_asignables.filter(
            content_type__app_label="auth",
            codename__startswith="role_",
        ).order_by("name")

    def _scope_assignable_fields_for_actor(self):
        allowed_groups = self._allowed_groups_for_actor()
        allowed_roles = self._allowed_roles_for_actor()

        self.fields["groups"].queryset = allowed_groups
        self.fields["user_permissions"].queryset = allowed_roles
        self.fields["grupos_asignables"].queryset = allowed_groups
        self.fields["roles_asignables"].queryset = allowed_roles

    def _init_delegation_fields(self, profile):
        if not profile:
            return
        self.fields["grupos_asignables"].initial = profile.grupos_asignables.all()
        self.fields["roles_asignables"].initial = profile.roles_asignables.filter(
            content_type__app_label="auth",
            codename__startswith="role_",
        )

    def _validate_selected_within_allowed(self, cleaned):
        if self._is_unrestricted_actor():
            return

        allowed_group_ids = set(
            self._allowed_groups_for_actor().values_list("id", flat=True)
        )
        selected_group_ids = set(
            cleaned.get("groups", Group.objects.none()).values_list("id", flat=True)
        )
        selected_assignable_group_ids = set(
            cleaned.get("grupos_asignables", Group.objects.none()).values_list(
                "id", flat=True
            )
        )

        if not selected_group_ids.issubset(allowed_group_ids):
            self.add_error(
                "groups",
                "Solo puede asignar grupos habilitados para su usuario.",
            )
        if not selected_assignable_group_ids.issubset(allowed_group_ids):
            self.add_error(
                "grupos_asignables",
                "Solo puede delegar grupos que usted mismo puede asignar.",
            )

        allowed_role_ids = set(
            self._allowed_roles_for_actor().values_list("id", flat=True)
        )
        selected_role_ids = set(
            cleaned.get("user_permissions", Permission.objects.none()).values_list(
                "id", flat=True
            )
        )
        selected_assignable_role_ids = set(
            cleaned.get("roles_asignables", Permission.objects.none()).values_list(
                "id", flat=True
            )
        )

        if not selected_role_ids.issubset(allowed_role_ids):
            self.add_error(
                "user_permissions",
                "Solo puede asignar roles habilitados para su usuario.",
            )
        if not selected_assignable_role_ids.issubset(allowed_role_ids):
            self.add_error(
                "roles_asignables",
                "Solo puede delegar roles que usted mismo puede asignar.",
            )


class UserCreationForm(PWAAccessMixin, DelegationScopeMixin, forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "select2"}),
        label="Grupos",
    )
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.select_related("content_type").order_by(
            "content_type__app_label", "name"
        ),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "select2"}),
        label="Permisos directos",
        help_text=(
            "Permisos adicionales específicos para este usuario, "
            "independientes de sus grupos."
        ),
    )
    es_usuario_provincial = forms.BooleanField(
        required=False,
        label="Es usuario provincial",
    )
    provincia = forms.ModelChoiceField(
        queryset=Provincia.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "select"}),
        label="Provincia",
    )
    es_coordinador = forms.BooleanField(
        required=False,
        label="Es Coordinador de Equipo Técnico",
    )
    duplas_asignadas = forms.ModelMultipleChoiceField(
        queryset=Dupla.objects.activas(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "select2"}),
        label="Equipos técnicos (Duplas) asignadas",
        help_text="Duplas activas disponibles (con o sin comedores asignados)",
    )
    rol = forms.CharField(max_length=100, required=False, label="Rol")

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "groups",
            "user_permissions",
            "es_usuario_provincial",
            "provincia",
            "es_coordinador",
            "duplas_asignadas",
            "last_name",
            "first_name",
            "rol",
        ]

    def __init__(self, *args, **kwargs):
        self.actor = kwargs.pop("actor", None)
        super().__init__(*args, **kwargs)
        self._setup_pwa_fields()
        self._setup_delegation_fields()
        self._scope_assignable_fields_for_actor()
        self.fields["email"].required = True

    def clean(self):
        cleaned = super().clean()
        cleaned = self._validate_required_email(cleaned)
        if cleaned.get("es_usuario_provincial") and not cleaned.get("provincia"):
            self.add_error("provincia", "Seleccione una provincia.")
        if cleaned.get("es_coordinador") and not cleaned.get("duplas_asignadas"):
            self.add_error("duplas_asignadas", "Seleccione al menos una dupla.")
        self._validate_selected_within_allowed(cleaned)
        return self._clean_pwa_fields(cleaned)

    def save(self, commit=True):
        with transaction.atomic():
            return self._save_atomic(commit=commit)

    def _save_atomic(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.email = self.cleaned_data.get("email", "")

        if self.cleaned_data.get("es_representante_pwa", False):
            user.is_staff = False
        elif self.cleaned_data.get("es_coordinador", False):
            user.is_staff = True

        if commit:
            user.save()
            if self.cleaned_data.get("es_representante_pwa", False):
                user.groups.clear()
                user.user_permissions.clear()
            else:
                user.groups.set(self.cleaned_data.get("groups", []))
                user.user_permissions.set(self.cleaned_data.get("user_permissions", []))

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.es_usuario_provincial = self.cleaned_data.get(
                "es_usuario_provincial", False
            )
            profile.provincia = (
                self.cleaned_data.get("provincia")
                if self.cleaned_data.get("es_usuario_provincial")
                else None
            )
            profile.es_coordinador = self.cleaned_data.get("es_coordinador", False)
            profile.rol = self.cleaned_data.get("rol")
            profile.must_change_password = True
            profile.password_changed_at = None
            profile.initial_password_expires_at = timezone.now() + timedelta(
                hours=settings.INITIAL_PASSWORD_MAX_AGE_HOURS
            )
            profile.save()
            # Evita devolver un profile cacheado con valores viejos tras el signal de User.
            user.refresh_from_db()
            profile.grupos_asignables.set(
                self.cleaned_data.get("grupos_asignables", [])
            )
            profile.roles_asignables.set(self.cleaned_data.get("roles_asignables", []))

            duplas = self.cleaned_data.get("duplas_asignadas", [])
            if profile.es_coordinador and duplas:
                profile.duplas_asignadas.set(duplas)
            else:
                profile.duplas_asignadas.clear()

            self._sync_pwa_access(user)

        return user


class CustomUserChangeForm(PWAAccessMixin, DelegationScopeMixin, forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Contraseña (dejar en blanco para no cambiarla)",
        required=False,
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "select2"}),
        label="Grupos",
    )
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.select_related("content_type").order_by(
            "content_type__app_label", "name"
        ),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "select2"}),
        label="Permisos directos",
        help_text=(
            "Permisos adicionales específicos para este usuario, "
            "independientes de sus grupos."
        ),
    )
    es_usuario_provincial = forms.BooleanField(
        required=False,
        label="Es usuario provincial",
    )
    provincia = forms.ModelChoiceField(
        queryset=Provincia.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "select2"}),
        label="Provincia",
    )
    es_coordinador = forms.BooleanField(
        required=False,
        label="Es Coordinador de Equipo Técnico",
    )
    duplas_asignadas = forms.ModelMultipleChoiceField(
        queryset=Dupla.objects.activas(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "select2"}),
        label="Equipos técnicos (Duplas) asignadas",
        help_text="Duplas activas disponibles (con o sin comedores asignados)",
    )
    rol = forms.CharField(max_length=100, required=False, label="Rol")

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "groups",
            "user_permissions",
            "es_usuario_provincial",
            "provincia",
            "es_coordinador",
            "duplas_asignadas",
            "last_name",
            "first_name",
            "rol",
        ]

    def __init__(self, *args, **kwargs):
        self.actor = kwargs.pop("actor", None)
        super().__init__(*args, **kwargs)
        self._setup_pwa_fields()
        self._setup_delegation_fields()
        self._scope_assignable_fields_for_actor()
        self.fields["email"].required = True
        self._original_password_hash = self.instance.password
        self.fields["password"].initial = ""
        self._init_pwa_fields()

        try:
            prof = self.instance.profile
        except Profile.DoesNotExist:
            prof = None

        if prof:
            self.fields["es_usuario_provincial"].initial = prof.es_usuario_provincial
            self.fields["provincia"].initial = prof.provincia
            self.fields["es_coordinador"].initial = prof.es_coordinador
            self.fields["duplas_asignadas"].initial = prof.duplas_asignadas.all()
            self.fields["rol"].initial = prof.rol
            self._init_delegation_fields(prof)

    def clean(self):
        cleaned = super().clean()
        cleaned = self._validate_required_email(cleaned)
        if cleaned.get("es_usuario_provincial") and not cleaned.get("provincia"):
            self.add_error("provincia", "Seleccione una provincia.")
        if cleaned.get("es_coordinador") and not cleaned.get("duplas_asignadas"):
            self.add_error("duplas_asignadas", "Seleccione al menos una dupla.")
        self._validate_selected_within_allowed(cleaned)
        return self._clean_pwa_fields(cleaned)

    def save(self, commit=True):
        with transaction.atomic():
            return self._save_atomic(commit=commit)

    def _save_atomic(self, commit=True):
        new_pwd = self.cleaned_data.get("password")
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email", "")

        if new_pwd:
            user.set_password(new_pwd)
        else:
            user.password = self._original_password_hash

        if self.cleaned_data.get("es_representante_pwa", False):
            user.is_staff = False
        elif self.cleaned_data.get("es_coordinador", False):
            user.is_staff = True

        if commit:
            user.save()
            if self.cleaned_data.get("es_representante_pwa", False):
                user.groups.clear()
                user.user_permissions.clear()
            else:
                user.groups.set(self.cleaned_data.get("groups", []))
                user.user_permissions.set(self.cleaned_data.get("user_permissions", []))

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.es_usuario_provincial = self.cleaned_data.get(
                "es_usuario_provincial", False
            )
            profile.provincia = (
                self.cleaned_data.get("provincia")
                if self.cleaned_data.get("es_usuario_provincial")
                else None
            )
            profile.es_coordinador = self.cleaned_data.get("es_coordinador", False)
            profile.rol = self.cleaned_data.get("rol")
            if new_pwd:
                profile.must_change_password = True
                profile.password_changed_at = None
                profile.initial_password_expires_at = timezone.now() + timedelta(
                    hours=settings.INITIAL_PASSWORD_MAX_AGE_HOURS
                )
            profile.save()
            user.refresh_from_db()
            profile.grupos_asignables.set(
                self.cleaned_data.get("grupos_asignables", [])
            )
            profile.roles_asignables.set(self.cleaned_data.get("roles_asignables", []))

            duplas = self.cleaned_data.get("duplas_asignadas", [])
            if profile.es_coordinador and duplas:
                profile.duplas_asignadas.set(duplas)
            else:
                profile.duplas_asignadas.clear()

            self._sync_pwa_access(user)

        return user


class GroupForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.select_related("content_type").order_by(
            "content_type__app_label", "name"
        ),
        required=False,
        widget=FilteredSelectMultiple("Permisos", is_stacked=False),
        label="Permisos (roles)",
        help_text=(
            "Selecciona los permisos del grupo. "
            "Estos permisos se aplican a todos los usuarios del grupo."
        ),
    )

    class Meta:
        model = Group
        fields = ["name", "permissions"]

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise forms.ValidationError("Este campo es obligatorio.")

        qs = Group.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ya existe un grupo con ese nombre.")
        return name
