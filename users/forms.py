from django import forms
from django.contrib.auth.models import User, Group


class UserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "select2"}),
    )

    class Meta:
        model = User
        fields = ["username", "email", "password", "groups"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            user.groups.set(self.cleaned_data["groups"])
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
    )

    class Meta:
        model = User
        fields = ["username", "email", "password", "groups"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Guardamos el hash original
        self._original_password_hash = self.instance.password
        # Dejamos el campo limpio
        self.fields["password"].initial = ""

    def save(self, commit=True):
        # Antes de guardar, recordamos qué cambio de contraseña recibimos
        new_pwd = self.cleaned_data.get("password")
        user = super().save(commit=False)

        if new_pwd:
            # Si pusieron algo, lo seteamos como contraseña nueva
            user.set_password(new_pwd)
        else:
            # Si el campo quedó en blanco, restauramos el hash anterior
            user.password = self._original_password_hash

        if commit:
            user.save()
            user.groups.set(self.cleaned_data["groups"])
        return user
