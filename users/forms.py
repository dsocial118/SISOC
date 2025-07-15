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
        # Incluyo password en fields para que siempre aparezca
        fields = ["username", "email", "password", "groups"]

    def save(self, commit=True):
        user = super().save(commit=False)
        # Sólo seteo la contraseña si me pasaron un valor
        new_pwd = self.cleaned_data.get("password")
        if new_pwd:
            user.set_password(new_pwd)
        if commit:
            user.save()
            user.groups.set(self.cleaned_data["groups"])
        return user