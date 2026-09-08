from django import forms

from core.validators import solo_digitos, validate_cuit


class GenerarUsuarioCDIForm(forms.Form):
    """Datos del usuario "CDI - Referente centro" a generar.

    El grupo es fijo y no se expone como campo (lo asigna el servicio). Los
    campos se precargan con los datos del referente ya cargado en el CDI.
    """

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
    dni = forms.CharField(
        max_length=16,
        label="DNI",
        widget=forms.TextInput(attrs={"class": "form-control", "inputmode": "numeric"}),
    )
    cuil = forms.CharField(
        max_length=16,
        label="CUIL",
        widget=forms.TextInput(attrs={"class": "form-control", "inputmode": "numeric"}),
    )

    def clean_first_name(self):
        return (self.cleaned_data.get("first_name") or "").strip()

    def clean_last_name(self):
        return (self.cleaned_data.get("last_name") or "").strip()

    def clean_email(self):
        return (self.cleaned_data.get("email") or "").strip()

    def clean_dni(self):
        dni = solo_digitos(self.cleaned_data.get("dni"))
        if len(dni) < 6:
            raise forms.ValidationError("Ingrese un DNI válido (solo números).")
        return dni

    def clean_cuil(self):
        return validate_cuit((self.cleaned_data.get("cuil") or "").strip())
