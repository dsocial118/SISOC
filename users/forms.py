from django import forms
from django.contrib.auth.models import User, Group

from core.models import Provincia
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

    class Meta:
        model = User
        fields = ["username", "email", "password", "groups", "es_usuario_provincial", "provincia"]

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("es_usuario_provincial") and not cleaned.get("provincia"):
            self.add_error("provincia", "Seleccione una provincia.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()
            user.groups.set(self.cleaned_data.get("groups", []))

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.es_usuario_provincial = self.cleaned_data.get("es_usuario_provincial", False)
            profile.provincia = (
                self.cleaned_data.get("provincia") if self.cleaned_data.get("es_usuario_provincial") else None
            )
            profile.save()

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

    class Meta:
        model = User
        fields = ["username", "email", "password", "groups", "es_usuario_provincial", "provincia"]

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

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("es_usuario_provincial") and not cleaned.get("provincia"):
            self.add_error("provincia", "Seleccione una provincia.")
        return cleaned

    def save(self, commit=True):
        new_pwd = self.cleaned_data.get("password")
        user = super().save(commit=False)

        if new_pwd:
            user.set_password(new_pwd)
        else:
            user.password = self._original_password_hash

        if commit:
            user.save()
            user.groups.set(self.cleaned_data.get("groups", []))

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.es_usuario_provincial = self.cleaned_data.get("es_usuario_provincial", False)
            profile.provincia = (
                self.cleaned_data.get("provincia") if self.cleaned_data.get("es_usuario_provincial") else None
            )
            profile.save()

        return user
