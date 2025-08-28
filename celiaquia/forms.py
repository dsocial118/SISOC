from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from celiaquia.models import (
    Expediente,
    ExpedienteCiudadano,
)


def validate_file_size(value):
    max_mb = 5
    if value.size > max_mb * 1024 * 1024:
        raise ValidationError(_(f"El archivo supera el tamaño máximo de {max_mb} MB."))


class BaseStyledForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            input_type = getattr(widget, "input_type", "")
            css_class = "form-control-file" if input_type == "file" else "form-control"
            widget.attrs.setdefault("class", css_class)
            if input_type in ("text", "number", "email", "date"):
                widget.attrs.setdefault("placeholder", field.label)


class StyledForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            input_type = getattr(widget, "input_type", "")
            css_class = "form-control-file" if input_type == "file" else "form-control"
            widget.attrs.setdefault("class", css_class)
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
        fields = ["observaciones", "excel_masivo"]


class ConfirmarEnvioForm(forms.Form):
    confirm = forms.BooleanField(
        label=_("¿Estás seguro de enviar este expediente?"),
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        required=True,
    )


class LegajoArchivoForm(BaseStyledForm):
    archivo1 = forms.FileField(
        label=_("Archivo 1"),
        validators=[
            FileExtensionValidator(["pdf", "jpg", "jpeg", "png"]),
            validate_file_size,
        ],
        widget=forms.ClearableFileInput(attrs={"accept": ".pdf,.jpg,.jpeg,.png"}),
        required=True,
    )
    archivo2 = forms.FileField(
        label=_("Archivo 2"),
        validators=[
            FileExtensionValidator(["pdf", "jpg", "jpeg", "png"]),
            validate_file_size,
        ],
        widget=forms.ClearableFileInput(attrs={"accept": ".pdf,.jpg,.jpeg,.png"}),
        required=True,
    )
    archivo3 = forms.FileField(
        label=_("Archivo 3"),
        validators=[
            FileExtensionValidator(["pdf", "jpg", "jpeg", "png"]),
            validate_file_size,
        ],
        widget=forms.ClearableFileInput(attrs={"accept": ".pdf,.jpg,.jpeg,.png"}),
        required=True,
    )

    class Meta:
        model = ExpedienteCiudadano
        fields = ["archivo1", "archivo2", "archivo3"]


class LegajoSubsanacionUploadForm(BaseStyledForm):
    archivo1 = forms.FileField(
        label=_("Archivo 1"),
        validators=[
            FileExtensionValidator(["pdf", "jpg", "jpeg", "png"]),
            validate_file_size,
        ],
        widget=forms.ClearableFileInput(attrs={"accept": ".pdf,.jpg,.jpeg,.png"}),
        required=False,
    )
    archivo2 = forms.FileField(
        label=_("Archivo 2"),
        validators=[
            FileExtensionValidator(["pdf", "jpg", "jpeg", "png"]),
            validate_file_size,
        ],
        widget=forms.ClearableFileInput(attrs={"accept": ".pdf,.jpg,.jpeg,.png"}),
        required=False,
    )
    archivo3 = forms.FileField(
        label=_("Archivo 3"),
        validators=[
            FileExtensionValidator(["pdf", "jpg", "jpeg", "png"]),
            validate_file_size,
        ],
        widget=forms.ClearableFileInput(attrs={"accept": ".pdf,.jpg,.jpeg,.png"}),
        required=False,
    )

    class Meta:
        model = ExpedienteCiudadano
        fields = ["archivo1", "archivo2", "archivo3"]

    def clean(self):
        cleaned = super().clean()
        a1 = cleaned.get("archivo1")
        a2 = cleaned.get("archivo2")
        a3 = cleaned.get("archivo3")
        if not any([a1, a2, a3]):
            raise ValidationError(_("Debés subir al menos un archivo para subsanar."))
        return cleaned


class SubsanacionSolicitudForm(StyledForm):
    motivo = forms.CharField(
        label=_("Motivo de la subsanación"),
        widget=forms.Textarea(attrs={"rows": 3}),
        required=True,
    )
    
class PagoRespuestaUploadForm(forms.Form):
    archivo = forms.FileField(required=True, label="Respuesta de Sintys (XLSX/CSV)")

class CupoBajaLegajoForm(StyledForm):
    motivo = forms.CharField(
        label=_("Motivo de la baja"),
        widget=forms.Textarea(attrs={"rows": 2}),
        required=True,
    )


class CupoSuspenderLegajoForm(StyledForm):
    motivo = forms.CharField(
        label=_("Motivo de la suspensión"),
        widget=forms.Textarea(attrs={"rows": 2}),
        required=True,
    )
