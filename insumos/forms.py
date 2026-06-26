from django import forms

from core.models import Programa

from .models import Insumo, InsumoCategoria
from .validators import INSUMO_ACCEPT_ATTR


class InsumoCategoriaForm(forms.ModelForm):
    class Meta:
        model = InsumoCategoria
        fields = ["programa", "nombre", "descripcion", "orden", "activo"]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["programa"].queryset = Programa.objects.filter(estado=True)

    def clean(self):
        cleaned_data = super().clean()
        programa = cleaned_data.get("programa")
        nombre = cleaned_data.get("nombre")
        if programa and nombre:
            duplicados = InsumoCategoria.objects.filter(
                programa=programa, nombre__iexact=nombre.strip()
            )
            if self.instance.pk:
                duplicados = duplicados.exclude(pk=self.instance.pk)
            if duplicados.exists():
                self.add_error(
                    "nombre",
                    "Ya existe una categoría con ese nombre en el programa.",
                )
        return cleaned_data


class InsumoForm(forms.ModelForm):
    class Meta:
        model = Insumo
        fields = ["programa", "categoria", "titulo", "descripcion", "archivo", "activo"]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "archivo": forms.ClearableFileInput(attrs={"accept": INSUMO_ACCEPT_ATTR}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["programa"].queryset = Programa.objects.filter(estado=True)
        self.fields["categoria"].queryset = InsumoCategoria.objects.filter(
            activo=True
        ).select_related("programa")
        self.fields["categoria"].required = False
        self.fields["categoria"].empty_label = "Sin categoría"

    def clean(self):
        cleaned_data = super().clean()
        programa = cleaned_data.get("programa")
        categoria = cleaned_data.get("categoria")
        if programa and categoria and categoria.programa_id != programa.id:
            self.add_error(
                "categoria",
                "La categoría seleccionada pertenece a otro programa.",
            )
        return cleaned_data
