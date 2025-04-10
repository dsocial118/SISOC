from django import forms
from django.utils import timezone
from django.utils import dateformat
from dupla.models import Dupla


class DuplaForm(forms.ModelForm):
    fecha = forms.CharField(
        disabled=False,
        initial=dateformat.format(timezone.now(), "H:i d/m/Y"),
    )
    class Meta:
        model = Dupla
        fields = "__all__"
        widgets = {
            "tecnico": forms.CheckboxSelectMultiple(),
            "fecha": forms.DateInput(
                attrs={"type": "date", "class": "form-control"},
            ),
        }
        labels = {
            "nombre": "Nombre",
            "tecnico": "Técnico",
            "fecha": "Fecha",
            "abogado": "Abogado",
        }