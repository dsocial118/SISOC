from django import forms
from django.core.exceptions import ValidationError

from intervenciones.constants import PROGRAMA_ALIASES_COMEDORES
from intervenciones.models.intervenciones import (
    Intervencion,
    SubIntervencion,
    TipoIntervencion,
)


def _normalize_programa_aliases(aliases):
    if aliases is None:
        return tuple(PROGRAMA_ALIASES_COMEDORES)
    if isinstance(aliases, str):
        aliases = (aliases,)
    normalized = []
    seen = set()
    for alias in aliases:
        if not alias:
            continue
        if alias in seen:
            continue
        seen.add(alias)
        normalized.append(alias)
    return tuple(normalized)


def build_programa_aliases(programa_nombre=None):
    return _normalize_programa_aliases((*PROGRAMA_ALIASES_COMEDORES, programa_nombre))


def _to_int_or_none(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class IntervencionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        programa_aliases = kwargs.pop("programa_aliases", None)
        super().__init__(*args, **kwargs)
        selected_tipo_id = _to_int_or_none(
            self.data.get("tipo_intervencion")
        ) or getattr(self.instance, "tipo_intervencion_id", None)
        selected_subintervencion_id = getattr(self.instance, "subintervencion_id", None)
        normalized_aliases = _normalize_programa_aliases(programa_aliases)
        self.fields["tipo_intervencion"].queryset = TipoIntervencion.para_programas(
            *normalized_aliases,
            include_ids=[selected_tipo_id] if selected_tipo_id else None,
        )
        self.fields["subintervencion"].queryset = SubIntervencion.para_tipo(
            selected_tipo_id,
            include_ids=(
                [selected_subintervencion_id] if selected_subintervencion_id else None
            ),
        )

    class Meta:
        model = Intervencion
        fields = [
            "tipo_intervencion",
            "subintervencion",
            "destinatario",
            "fecha",
            "forma_contacto",
            "observaciones",
            "tiene_documentacion",
            "documentacion",
        ]
        widgets = {
            "tipo_intervencion": forms.Select(attrs={"class": "form-control"}),
            "subintervencion": forms.Select(attrs={"class": "form-control"}),
            "destinatario": forms.Select(attrs={"class": "form-control"}),
            "fecha": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "forma_contacto": forms.Select(attrs={"class": "form-control"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "documentacion": forms.FileInput(attrs={"class": "form-control"}),
        }
        labels = {
            "tipo_intervencion": "Tipo de Intervención",
            "subintervencion": "Subtipo de Intervención",
            "destinatario": "Destinatario",
            "fecha": "Fecha",
            "forma_contacto": "Forma de Contacto",
            "observaciones": "Descripción",
            "tiene_documentacion": "Documentación Adjunta",
            "documentacion": "Cargar Documentación",
        }

    def clean_fecha(self):
        """Validar que la fecha esté entre los años 2000 y 2100."""
        fecha = self.cleaned_data.get("fecha")

        if fecha:
            anio = fecha.year

            if anio < 2000:
                raise ValidationError(
                    "El año de la fecha debe ser mayor o igual a 2000."
                )

            if anio > 2100:
                raise ValidationError(
                    "El año de la fecha debe ser menor o igual a 2100."
                )

        return fecha

    def clean(self):
        cleaned_data = super().clean()
        tipo_intervencion = cleaned_data.get("tipo_intervencion")
        subintervencion = cleaned_data.get("subintervencion")

        if not tipo_intervencion:
            return cleaned_data

        if not tipo_intervencion.subintervenciones.exists():
            cleaned_data["subintervencion"] = None
            return cleaned_data

        if not subintervencion:
            self.add_error("subintervencion", "Debe seleccionar una subintervencion.")
            return cleaned_data

        if subintervencion.tipo_intervencion_id != tipo_intervencion.id:
            self.add_error(
                "subintervencion",
                "La subintervencion seleccionada no corresponde al tipo de intervencion.",
            )

        return cleaned_data
