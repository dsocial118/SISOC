from django import forms
from django.contrib.auth.models import Group
from duplas.models import Dupla


class DuplaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filtrar_campos_tecnico_abogado()

    def filtrar_campos_tecnico_abogado(self):
        grupo_tecnico = Group.objects.filter(name="Tecnico Comedor").first()
        if grupo_tecnico:
            usuarios_asignados = Dupla.objects.exclude(pk=self.instance.pk).values_list(
                "tecnico", flat=True
            )
            usuarios_asignados = [u for u in usuarios_asignados if u is not None]
            self.fields["tecnico"].queryset = grupo_tecnico.user_set.exclude(
                id__in=usuarios_asignados
            )
        else:
            self.fields["tecnico"].queryset = self.fields["tecnico"].queryset.none()

        grupo_abogado = Group.objects.filter(name="Abogado Dupla").first()
        if grupo_abogado:
            self.fields["abogado"].queryset = grupo_abogado.user_set.all()
        else:
            self.fields["abogado"].queryset = self.fields["abogado"].queryset.none()

    class Meta:
        model = Dupla
        fields = "__all__"
        widgets = {
            "tecnico": forms.SelectMultiple(
                attrs={
                    "class": "form-control js-tecnico",
                    "data-role": "select2",
                    "data-placeholder": "Selecciona hasta 2 técnicos",
                    "aria-label": "Selecciona hasta 2 técnicos",
                }
            ),
            "abogado": forms.Select(attrs={"class": "form-control"}),
        }
        labels = {
            "nombre": "Nombre",
            "tecnico": "Técnico",
            "abogado": "Abogado",
            "estado": "Estado",
        }

    def clean_tecnico(self):
        """Valida que se seleccionen como máximo 2 técnicos.

        Select2 evita más de 2 en el UI, pero reforzamos la validación
        del lado del servidor por seguridad y consistencia.
        """
        tecnicos = self.cleaned_data.get("tecnico")
        # `tecnicos` es un QuerySet/iterable de usuarios seleccionados
        if tecnicos is not None and len(tecnicos) > 2:
            raise forms.ValidationError("Selecciona como máximo 2 técnicos.")
        return tecnicos
