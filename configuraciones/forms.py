from django import forms  # pylint: disable=too-many-lines
from django.forms.models import inlineformset_factory
from configuraciones.models import CriterioAlerta


from .models import (
    Secretarias,
    Subsecretarias,
    Programas,
    Organismos,
    PlanesSociales,
    AgentesExternos,
    GruposDestinatarios,
    CategoriaAlertas,
    Alertas,
    Equipos,
    Acciones,
    Criterios,
    Vacantes,
    IndiceCriterios,
    Indices,
)


class SecretariasForm(forms.ModelForm):
    class Meta:
        model = Secretarias
        exclude = ()
        widgets = {
            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "estado": forms.Select(choices=[(True, "Activo"), (False, "Inactivo")]),
        }


class SubsecretariasForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fk_secretaria"].label = "Secretaría"

    class Meta:
        model = Subsecretarias
        exclude = ()
        widgets = {
            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "estado": forms.Select(choices=[(True, "Activo"), (False, "Inactivo")]),
        }


class ProgramasForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fk_subsecretaria"].label = "Subsecretaría"

    class Meta:
        model = Programas
        exclude = ()
        widgets = {
            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "estado": forms.Select(choices=[(True, "Activo"), (False, "Inactivo")]),
        }


class OrganismosForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["estado"].initial = True

    class Meta:
        model = Organismos
        exclude = ()
        widgets = {
            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "estado": forms.Select(choices=[(True, "Activo"), (False, "Inactivo")]),
        }


class PlanesSocialesForm(forms.ModelForm):
    class Meta:
        model = PlanesSociales
        exclude = ()
        widgets = {
            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "estado": forms.Select(choices=[(True, "Activo"), (False, "Inactivo")]),
        }


class AgentesExternosForm(forms.ModelForm):
    class Meta:
        model = AgentesExternos
        exclude = ()
        labels = {
            "fk_organismo": "Organismo",
            "telefono": "Teléfono",
        }

        widgets = {
            "estado": forms.Select(choices=[(True, "Activo"), (False, "Inactivo")])
        }


class GruposDestinatariosForm(forms.ModelForm):
    class Meta:
        model = GruposDestinatarios
        exclude = ()
        widgets = {
            "m2m_usuarios": forms.SelectMultiple(
                attrs={
                    "class": "select2 w-100",
                },
            ),
            "m2m_agentes_externos": forms.SelectMultiple(
                attrs={
                    "class": "select2 w-100",
                },
            ),
            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "estado": forms.Select(choices=[(True, "Activo"), (False, "Inactivo")]),
        }

        labels = {
            "m2m_usuarios": "usuarios",
            "m2m_agentes_externos": "Agentes externos",
        }


class CategoriaAlertasForm(forms.ModelForm):
    class Meta:
        model = CategoriaAlertas
        exclude = ()
        widgets = {
            # 'observaciones': forms.Textarea(
            #     attrs={
            #         'class': 'form-control',
            #         'rows': 3,
            #     }
            # ),
            "estado": forms.Select(choices=[(True, "Activo"), (False, "Inactivo")]),
        }
        labels = {"dimension": "Dimensión"}


class AlertasForm(forms.ModelForm):
    class Meta:
        model = Alertas
        exclude = ()
        widgets = {
            "estado": forms.Select(choices=[(True, "Activo"), (False, "Inactivo")]),
            "gravedad": forms.Select(),
        }
        labels = {"fk_categoria": "Categoría"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['gravedad'].queryset = CriterioAlerta.objects.all()
        self.fields['gravedad'].widget.choices = [(criterio.id, criterio.criterio) for criterio in CriterioAlerta.objects.all()]


class EquiposForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fk_programa"].label = "Programa"
        self.fields["m2m_usuarios"].label = "Integrantes"
        self.fields["fk_coordinador"].label = "Coordinador"

    class Meta:
        model = Equipos
        exclude = ()
        widgets = {
            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "estado": forms.Select(choices=[(True, "Activo"), (False, "Inactivo")]),
        }


class AccionesForm(forms.ModelForm):
    class Meta:
        model = Acciones
        exclude = ()
        widgets = {
            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
        }


class CriteriosForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["m2m_acciones"].label = ""
        self.fields["m2m_alertas"].label = ""
        self.fields["fk_sujeto"].label = "Sujeto de aplicación"

    class Meta:
        model = Criterios
        exclude = ("m2m_criterios",)
        widgets = {
            "m2m_acciones": forms.SelectMultiple(
                attrs={
                    "class": "select2 w-100",
                },
            ),
            "m2m_alertas": forms.SelectMultiple(
                attrs={
                    "class": "select2 w-100",
                },
            ),
            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
        }


class VacantesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fk_programa"].label = "Programa"
        self.fields["fk_organismo"].label = "Organismo"

    class Meta:
        model = Vacantes
        exclude = ()
        widgets = {
            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "estado": forms.Select(choices=[(True, "Activo"), (False, "Inactivo")]),
        }


class IndicesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["m2m_programas"].label = ""
        self.fields["nombre"].label = "Nombre del Índice"

    class Meta:
        model = Indices
        exclude = ("m2m_criterios",)
        widgets = {
            "m2m_programas": forms.SelectMultiple(
                attrs={
                    "class": "select2 w-100",
                },
            ),
            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
        }


class IndiceCriteriosForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fk_criterio"].label = ""
        self.fields["puntaje_base"].label = ""

    class Meta:
        model = IndiceCriterios
        exclude = ("fk_indice",)


IndicesFormset = inlineformset_factory(
    Indices, IndiceCriterios, form=IndiceCriteriosForm, extra=1, can_delete=True
)
