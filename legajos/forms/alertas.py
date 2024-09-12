from django import forms

from legajos.models import CategoriaAlertas, LegajoAlertas


class LegajosAlertasForm(forms.ModelForm):
    fk_categoria = forms.ModelChoiceField(
        required=True,
        label="Categoría",
        queryset=CategoriaAlertas.objects.all(),
        widget=forms.Select(attrs={"class": "select2"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fk_legajo"].widget = forms.HiddenInput()
        self.fields["creada_por"].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        fk_alerta = cleaned_data.get("fk_alerta")
        fk_legajo = cleaned_data.get("fk_legajo")
        if (
            fk_alerta
            and fk_legajo
            and LegajoAlertas.objects.filter(
                fk_alerta=fk_alerta, fk_legajo=fk_legajo
            ).exists()
        ):
            self.add_error("fk_alerta", "Ya existe esa alerta en el legajo")
        return cleaned_data

    class Meta:
        model = LegajoAlertas
        fields = "__all__"
        widgets = {
            "fk_alerta": forms.Select(attrs={"class": "select2"}),
        }
        labels = {"fk_alerta": "Alerta"}
