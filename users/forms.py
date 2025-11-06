from django import forms
from django.contrib.auth.models import User, Group

from core.models import Provincia
from core.constants import UserGroups
from duplas.models import Dupla
from .models import Profile


class UserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "select2"}),
        label="Grupos",
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
        label="Es Coordinador de Gestión",
    )

    duplas_asignadas = forms.ModelMultipleChoiceField(
        queryset=Dupla.objects.activas_con_comedores(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "select2"}),
        label="Equipos técnicos (Duplas) asignadas",
        help_text="Solo duplas activas con comedores asignados",
    )

    rol = forms.CharField(max_length=100, required=False, label="Rol")

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "groups",
            "es_usuario_provincial",
            "provincia",
            "es_coordinador",
            "duplas_asignadas",
            "last_name",
            "first_name",
            "rol",
        ]

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("es_usuario_provincial") and not cleaned.get("provincia"):
            self.add_error("provincia", "Seleccione una provincia.")
        if cleaned.get("es_coordinador") and not cleaned.get("duplas_asignadas"):
            self.add_error("duplas_asignadas", "Seleccione al menos una dupla.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        # Activar is_staff si es coordinador (requerido para acceso al backoffice)
        if self.cleaned_data.get("es_coordinador", False):
            user.is_staff = True

        if commit:
            user.save()
            user.groups.set(self.cleaned_data.get("groups", []))

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
            profile.save()

            # ManyToMany se guarda después de save()
            duplas = self.cleaned_data.get("duplas_asignadas", [])
            if profile.es_coordinador and duplas:
                profile.duplas_asignadas.set(duplas)
            else:
                profile.duplas_asignadas.clear()

        return user


class CustomUserChangeForm(forms.ModelForm):
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
        label="Es Coordinador de Gestión",
    )

    duplas_asignadas = forms.ModelMultipleChoiceField(
        queryset=Dupla.objects.activas_con_comedores(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "select2"}),
        label="Equipos técnicos (Duplas) asignadas",
        help_text="Solo duplas activas con comedores asignados",
    )

    rol = forms.CharField(max_length=100, required=False, label="Rol")

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "groups",
            "es_usuario_provincial",
            "provincia",
            "es_coordinador",
            "duplas_asignadas",
            "last_name",
            "first_name",
            "rol",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_password_hash = self.instance.password
        self.fields["password"].initial = ""

        # Inicializar con datos del profile si existe
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

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("es_usuario_provincial") and not cleaned.get("provincia"):
            self.add_error("provincia", "Seleccione una provincia.")
        if cleaned.get("es_coordinador") and not cleaned.get("duplas_asignadas"):
            self.add_error("duplas_asignadas", "Seleccione al menos una dupla.")
        return cleaned

    def save(self, commit=True):
        new_pwd = self.cleaned_data.get("password")
        user = super().save(commit=False)

        if new_pwd:
            user.set_password(new_pwd)
        else:
            user.password = self._original_password_hash

        # Activar is_staff si es coordinador (requerido para acceso al backoffice)
        if self.cleaned_data.get("es_coordinador", False):
            user.is_staff = True

        if commit:
            user.save()
            user.groups.set(self.cleaned_data.get("groups", []))

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
            profile.save()

            # ManyToMany se guarda después de save()
            duplas = self.cleaned_data.get("duplas_asignadas", [])
            if profile.es_coordinador and duplas:
                profile.duplas_asignadas.set(duplas)
            else:
                profile.duplas_asignadas.clear()

        return user
