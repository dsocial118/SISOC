from django import forms
from cdi.models import CentroDesarrolloInfantil

class CentroDesarrolloInfantilForm(forms.ModelForm):
    class Meta:
        model = CentroDesarrolloInfantil
        fields = "__all__" 
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre del CDI"}),
            "organizacion": forms.Select(attrs={"class": "form-control"}),  # ForeignKey -> Select
            "comienzo": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Año de inicio"}),
            "modalidad_gestion": forms.Select(attrs={"class": "form-control"}),  # Choices -> Select
            "provincia": forms.Select(attrs={"class": "form-control"}),  # ForeignKey -> Select
            "municipio": forms.Select(attrs={"class": "form-control"}),  # ForeignKey -> Select
            "localidad": forms.Select(attrs={"class": "form-control"}),  # ForeignKey -> Select
            "partido": forms.TextInput(attrs={"class": "form-control", "placeholder": "Partido"}),
            "barrio": forms.TextInput(attrs={"class": "form-control", "placeholder": "Barrio"}),
            "codigo_postal": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Código Postal"}),
            "direccion": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Dirección completa"}),
            "telefono": forms.TextInput(attrs={"class": "form-control", "placeholder": "Teléfono"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"}),
            "meses_funcionamiento": forms.CheckboxSelectMultiple(),  # ManyToManyField -> CheckboxSelectMultiple
            "dias_funcionamiento": forms.CheckboxSelectMultiple(),  # ManyToManyField -> CheckboxSelectMultiple
            "turnos_funcionamiento": forms.CheckboxSelectMultiple(),  # ManyToManyField -> CheckboxSelectMultiple
            "horario_inicio": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "horario_fin": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "cantidad_ninos": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Cantidad de niños"}),
            "cantidad_trabajadores": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Cantidad de trabajadores"}),
            "cobro_arancel": forms.Select(attrs={"class": "form-control"}),  # Choices -> Select
            "estabilidad_matricula": forms.CheckboxInput(attrs={"class": "form-check-input"}),  # BooleanField -> Checkbox
        }
