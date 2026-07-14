from django import forms
from django.db.models import Q

from core.models import Programa

from .models import Insumo, InsumoCategoria
from .validators import INSUMO_ACCEPT_ATTR


class CategoriaSelect(forms.Select):
    """Select de categoría que expone en cada opción su programa.

    El atributo ``data-programa`` permite filtrar las categorías en el cliente
    según el programa elegido, para que una categoría solo esté disponible en el
    programa al que fue asociada.
    """

    # pylint: disable=too-many-arguments  # firma impuesta por forms.Select
    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name, value, label, selected, index, subindex, attrs
        )
        instance = getattr(value, "instance", None)
        programa_id = getattr(instance, "programa_id", None)
        if programa_id:
            option["attrs"]["data-programa"] = str(programa_id)
        return option


class InsumoCategoriaForm(forms.ModelForm):
    class Meta:
        model = InsumoCategoria
        fields = ["programa", "nombre", "descripcion", "orden", "activo"]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        programa_queryset = Programa.objects.filter(estado=True)
        if self.instance.pk and self.instance.programa_id:
            programa_queryset = Programa.objects.filter(
                Q(estado=True) | Q(pk=self.instance.programa_id)
            )
        self.fields["programa"].queryset = programa_queryset

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
            "categoria": CategoriaSelect,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        programa_queryset = Programa.objects.filter(estado=True)
        categoria_queryset = InsumoCategoria.objects.filter(activo=True)
        if self.instance.pk:
            if self.instance.programa_id:
                programa_queryset = Programa.objects.filter(
                    Q(estado=True) | Q(pk=self.instance.programa_id)
                )
            if self.instance.categoria_id:
                categoria_queryset = InsumoCategoria.objects.filter(
                    Q(activo=True) | Q(pk=self.instance.categoria_id)
                )
        self.fields["programa"].queryset = programa_queryset
        self.fields["categoria"].queryset = categoria_queryset.select_related(
            "programa"
        )
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
