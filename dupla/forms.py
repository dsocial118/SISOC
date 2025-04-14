from django import forms
from django.utils import timezone
from django.utils import dateformat
from dupla.models import Dupla


class DuplaForm(forms.ModelForm):
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
            "abogado": "Abogado",
            "estado": "Estado",
        }
