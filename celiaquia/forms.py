# forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from celiaquia.models import (
    Expediente,
    ExpedienteCiudadano,
    Organismo,
    TipoCruce,
)

# Custom Validators


def validate_file_size(value):
    max_mb = 5
    if value.size > max_mb * 4024 * 4024:
        raise ValidationError(_(f"El archivo supera el tamaño máximo de {max_mb} MB."))


class BaseStyledForm(forms.ModelForm):
    """Applies uniform styling; skips placeholder for non-text fields."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Recorremos directamente los campos sin desempaquetar name
        for field in self.fields.values():
            widget = field.widget
            input_type = getattr(widget, "input_type", "")
            # Decidir clase CSS
            css_class = "form-control-file" if input_type == "file" else "form-control"
            widget.attrs.setdefault("class", css_class)
            # Placeholder sólo para tipos textuales
            if input_type in ("text", "number", "email", "date"):
                widget.attrs.setdefault("placeholder", field.label)


class ExpedienteForm(BaseStyledForm):
    excel_masivo = forms.FileField(
        label=_("Archivo Excel"),
        validators=[FileExtensionValidator(["xlsx"]), validate_file_size],
        widget=forms.ClearableFileInput(attrs={"accept": ".xlsx"}),
        required=True,
    )
    observaciones = forms.CharField(
        label=_("Observaciones"),
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
    )

    class Meta:
        model = Expediente
        fields = ["codigo", "observaciones", "excel_masivo"]


class ConfirmarEnvioForm(forms.Form):
    confirm = forms.BooleanField(
        label=_("¿Estás seguro de enviar este expediente?"),
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        required=True,
    )


class LegajoArchivoForm(BaseStyledForm):
    archivo = forms.FileField(
        label=_("Archivo de Legajo"),
        validators=[
            FileExtensionValidator(["pdf", "jpg", "jpeg", "png"]),
            validate_file_size,
        ],
        widget=forms.ClearableFileInput(attrs={"accept": ".pdf,.jpg,.jpeg,.png"}),
        required=True,
    )

    class Meta:
        model = ExpedienteCiudadano
        fields = ["archivo"]





