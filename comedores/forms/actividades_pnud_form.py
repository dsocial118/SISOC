from django import forms

from pwa.models import CatalogoActividadPWA


class ActividadPnudForm(forms.ModelForm):
    categoria_modo = forms.ChoiceField(
        required=True,
        initial="existente",
        choices=(("existente", "Usar existente"), ("nueva", "Crear nueva")),
        widget=forms.HiddenInput(),
    )
    categoria_existente = forms.ChoiceField(
        required=False,
        label="Categoria existente",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    categoria_nueva = forms.CharField(
        required=False,
        label="Nueva categoria",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Escribi una categoria nueva",
            }
        ),
    )

    class Meta:
        model = CatalogoActividadPWA
        fields = ["categoria", "actividad", "activo"]
        widgets = {
            "categoria": forms.HiddenInput(),
            "actividad": forms.TextInput(attrs={"class": "form-control"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "categoria": "Categoria",
            "actividad": "Actividad",
            "activo": "Activo",
        }

    def __init__(self, *args, categorias=None, **kwargs):
        super().__init__(*args, **kwargs)
        categorias = list(categorias or [])
        self.fields["categoria"].required = False
        if self.instance and self.instance.pk:
            self.fields["categoria_modo"].initial = "existente"
        self.fields["categoria_existente"].choices = [
            ("", "Selecciona una categoria"),
            *[(categoria, categoria) for categoria in categorias],
        ]
        if self.instance and self.instance.pk:
            self.fields["categoria_existente"].initial = self.instance.categoria

    def clean_categoria(self):
        return (self.cleaned_data.get("categoria") or "").strip()

    def clean(self):
        cleaned_data = super().clean()
        modo = self.cleaned_data.get("categoria_modo") or "existente"
        value = (
            self.cleaned_data.get("categoria_nueva")
            if modo == "nueva"
            else self.cleaned_data.get("categoria_existente")
        ) or (
            self.cleaned_data.get("categoria_nueva")
            or self.cleaned_data.get("categoria_existente")
            or self.cleaned_data.get("categoria")
            or ""
        )
        value = value.strip()
        if not value:
            field_name = "categoria_nueva" if modo == "nueva" else "categoria_existente"
            self.add_error(field_name, "La categoria es obligatoria.")
            return cleaned_data
        cleaned_data["categoria"] = value
        return cleaned_data

    def clean_actividad(self):
        value = (self.cleaned_data.get("actividad") or "").strip()
        if not value:
            raise forms.ValidationError("La actividad es obligatoria.")
        return value
