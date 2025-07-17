# forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from celiaquia.models import (
    Expediente,
    ExpedienteCiudadano,
    ArchivoCruce,
    InformePago,
    Organismo,
    TipoCruce
)

# Custom Validators

def validate_file_size(value):
    max_mb = 5
    if value.size > max_mb * 1024 * 1024:
        raise ValidationError(_(f"El archivo supera el tamaño máximo de {max_mb} MB."))

class BaseStyledForm(forms.ModelForm):
    """Applies uniform styling; skips placeholder for non-text fields."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            # decide CSS class
            if getattr(widget, 'input_type', '') == 'file':
                css = 'form-control-file'
            else:
                css = 'form-control'

            # apply classes
            widget.attrs.setdefault('class', css)
            # apply placeholder for text inputs only
            if getattr(widget, 'input_type', '') in ('text', 'number', 'email', 'date'):
                widget.attrs.setdefault('placeholder', field.label)

class ExpedienteForm(BaseStyledForm):
    excel_masivo = forms.FileField(
        label=_('Archivo Excel'),
        validators=[
            FileExtensionValidator(['xlsx']),
            validate_file_size
        ],
        widget=forms.ClearableFileInput(attrs={'accept': '.xlsx'}),
        required=True
    )
    observaciones = forms.CharField(
        label=_('Observaciones'),
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )

    class Meta:
        model = Expediente
        fields = ['codigo', 'observaciones', 'excel_masivo']

class ConfirmarEnvioForm(forms.Form):
    confirm = forms.BooleanField(
        label=_('¿Estás seguro de enviar este expediente?'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=True
    )

class LegajoArchivoForm(BaseStyledForm):
    archivo = forms.FileField(
        label=_('Archivo de Legajo'),
        validators=[
            FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png']),
            validate_file_size
        ],
        widget=forms.ClearableFileInput(attrs={'accept': '.pdf,.jpg,.jpeg,.png'}),
        required=True
    )

    class Meta:
        model = ExpedienteCiudadano
        fields = ['archivo']

class CruceUploadForm(BaseStyledForm):
    organismo = forms.ModelChoiceField(
        label=_('Organismo'),
        queryset=Organismo.objects.none(),  # set in __init__
        widget=forms.Select(attrs={'class': 'form-select select2'})
    )
    tipo = forms.ModelChoiceField(
        label=_('Tipo de Cruce'),
        queryset=TipoCruce.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    archivo = forms.FileField(
        label=_('Archivo de Cruce'),
        validators=[
            FileExtensionValidator(['xlsx']),
            validate_file_size
        ],
        widget=forms.ClearableFileInput(attrs={'accept': '.xlsx'}),
        required=True
    )

    class Meta:
        model = ArchivoCruce
        fields = ['organismo', 'tipo', 'archivo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # dynamic, ordered queryset
        self.fields['organismo'].queryset = Organismo.objects.order_by('nombre')

class PagoForm(BaseStyledForm):
    fecha_pago = forms.DateField(
        label=_('Fecha de Pago'),
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    monto = forms.DecimalField(
        label=_('Monto'),
        widget=forms.NumberInput(attrs={'step': '0.01'})
    )
    observaciones = forms.CharField(
        label=_('Observaciones'),
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False
    )

    class Meta:
        model = InformePago
        fields = ['fecha_pago', 'monto', 'observaciones']
