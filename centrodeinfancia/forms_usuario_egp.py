from django import forms

from core.models import Provincia


class GenerarUsuarioEGPForm(forms.Form):
    """Datos del referente provincial SIMEPI - EGP a generar."""

    first_name = forms.CharField(
        max_length=150,
        label="Nombre",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        max_length=150,
        label="Apellido",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
        help_text="Se usará como usuario y para enviarle las credenciales.",
    )
    provincia = forms.ModelChoiceField(
        queryset=Provincia.objects.all(),
        required=True,
        label="Provincia",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def clean_first_name(self):
        return (self.cleaned_data.get("first_name") or "").strip()

    def clean_last_name(self):
        return (self.cleaned_data.get("last_name") or "").strip()

    def clean_email(self):
        return (self.cleaned_data.get("email") or "").strip()
