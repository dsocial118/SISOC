from django import forms
from django.contrib.auth.models import Group
from duplas.models import Dupla


class DuplaForm(forms.ModelForm):
    # Sobrescribimos los campos para personalizar la visualización
    tecnico = forms.ModelMultipleChoiceField(
        queryset=None,
        required=True,
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-control js-tecnico",
                "data-role": "select2",
                "data-placeholder": "Selecciona hasta 2 técnicos",
                "aria-label": "Selecciona hasta 2 técnicos",
            }
        ),
    )

    abogado = forms.ModelChoiceField(
        queryset=None,
        required=True,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filtrar_campos_tecnico_abogado()
        # Aplicar el label personalizado
        self.fields["tecnico"].label_from_instance = self.label_from_instance_custom
        self.fields["abogado"].label_from_instance = self.label_from_instance_custom

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

    def label_from_instance_custom(self, user):
        """
        Genera el label personalizado para los usuarios en formato:
        Apellido/s Nombre/s - usuario
        Ejemplo: Dolesor Roman - rdolesor
        """
        full_name = f"{user.last_name} {user.first_name}".strip()
        if full_name:
            return f"{full_name} - {user.username}"
        return user.username

    class Meta:
        model = Dupla
        # Excluimos coordinador porque se asigna SOLO desde el ABM de usuarios
        fields = ["nombre", "tecnico", "abogado", "estado"]
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
