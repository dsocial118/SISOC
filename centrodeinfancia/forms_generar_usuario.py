from django import forms


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

    def clean_first_name(self):
        return (self.cleaned_data.get("first_name") or "").strip()

    def clean_last_name(self):
        return (self.cleaned_data.get("last_name") or "").strip()

    def clean_email(self):
        return (self.cleaned_data.get("email") or "").strip()
