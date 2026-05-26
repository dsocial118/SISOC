from django import forms


class GenerarUsuarioCentroVATForm(forms.Form):
    """Datos del usuario referente CFP a generar para un Centro VAT.

    El grupo es fijo (lo asigna el servicio) y no se expone como campo. Los
    campos se precargan con el referente ya cargado en el centro cuando
    todavía no hay usuarios asociados.
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
