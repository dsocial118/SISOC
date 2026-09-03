from django import forms

from datacalle.models import Relevamiento
from datacalle.services import (
    get_dispositivos_para_usuario,
    get_entrevistadores_para_usuario,
    get_provincias_para_usuario,
)
from users.services_datacalle import get_relevador_calle_users_for_provincia


class RelevamientoForm(forms.ModelForm):
    """Planificación de un operativo (D2.2).

    El alcance del actor acota provincia, dispositivos y equipo: un coordinador
    sólo puede planificar en su provincia y armar el equipo con los
    entrevistadores de esa misma provincia.
    """

    class Meta:
        model = Relevamiento
        fields = [
            "denominacion",
            "provincia",
            "municipio",
            "localidad",
            "fase",
            "area_operativa",
            "dispositivo",
            "fecha_inicio",
            "fecha_fin",
            "modalidad_papel",
            "equipo",
            "observaciones",
        ]
        widgets = {
            "provincia": forms.Select(attrs={"class": "select2"}),
            "municipio": forms.Select(attrs={"class": "select2"}),
            "localidad": forms.Select(attrs={"class": "select2"}),
            "fase": forms.Select(attrs={"class": "select2"}),
            "dispositivo": forms.Select(attrs={"class": "select2"}),
            "equipo": forms.SelectMultiple(attrs={"class": "select2"}),
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "fecha_fin": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "observaciones": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.actor = actor
        self.fields["provincia"].queryset = get_provincias_para_usuario(actor)
        self.fields["municipio"].required = False
        self.fields["localidad"].required = False

        # Ambos se acotan por el alcance del actor, no por la provincia elegida:
        # para un coordinador ya es el padrón de su provincia y evita una cascada.
        self.fields["dispositivo"].queryset = get_dispositivos_para_usuario(actor)
        self.fields["equipo"].queryset = get_entrevistadores_para_usuario(actor)
        self.fields["equipo"].label_from_instance = self._etiqueta_entrevistador

    @staticmethod
    def _etiqueta_entrevistador(user):
        nombre = f"{user.first_name} {user.last_name}".strip() or user.username
        dni = getattr(getattr(user, "profile", None), "dni", "")
        return f"{nombre} ({dni})" if dni else nombre

    def clean(self):
        cleaned = super().clean()
        provincia = cleaned.get("provincia")
        equipo = cleaned.get("equipo")

        if not equipo:
            self.add_error("equipo", "Elegí al menos un entrevistador para el equipo.")
        elif provincia:
            habilitados = set(
                get_relevador_calle_users_for_provincia(provincia.id).values_list(
                    "id", flat=True
                )
            )
            fuera = [u for u in equipo if u.id not in habilitados]
            if fuera:
                self.add_error(
                    "equipo",
                    "Hay integrantes que no son entrevistadores de DataCalle en "
                    "esa provincia: "
                    + ", ".join(sorted(u.username for u in fuera))
                    + ".",
                )

        # La fase decide qué campo de lugar corresponde; limpiamos el otro.
        if cleaned.get("fase") == Relevamiento.Fase.ESPACIO_PUBLICO:
            cleaned["dispositivo"] = None
        elif cleaned.get("fase") == Relevamiento.Fase.DISPOSITIVO_ALOJAMIENTO:
            cleaned["area_operativa"] = ""
        return cleaned
