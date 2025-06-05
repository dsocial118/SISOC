from django import forms
from rendicioncuentasmensual.models import RendicionCuentaMensual, DocumentacionAdjunta

class RendicionCuentaMensualForm(forms.ModelForm):
    arvhios_adjuntos = forms.ModelMultipleChoiceField(
        queryset=DocumentacionAdjunta.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    class Meta:
        model = RendicionCuentaMensual
        fields = "__all__"
        exclude = ["comedor"]
        widgets = {
            "mes": forms.Select(attrs={"class": "form-control"}),
            "anio": forms.NumberInput(attrs={"class": "form-control"}),
            "documento_adjunto": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        labels = {
            "mes": "Mes",
            "anio": "Año",
            "documento_adjunto": "Documento Adjunto",
            "observaciones": "Observaciones",
            "arvhios_adjuntos": "Archivos Adjuntos",
        }
class DocumentacionAdjuntaForm(forms.ModelForm):
    class Meta:
        model = DocumentacionAdjunta
        fields = "__all__"
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "archivo": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
        labels = {
            "nombre": "Nombre del Documento",
            "archivo": "Archivo",
        }