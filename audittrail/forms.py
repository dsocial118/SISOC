from datetime import date

from django import forms

from auditlog.models import LogEntry

ORIGIN_CHOICES = [
    ("", "Todos los orígenes"),
    ("web", "Web"),
    ("command", "Comando"),
    ("system", "Sistema/Proceso"),
]

MAX_TEXT_SEARCH_RANGE_DAYS = 93
MAX_EXPORT_RANGE_DAYS = 31


ACTION_CHOICES = [
    ("", "Todos los eventos"),
    (LogEntry.Action.CREATE, "Creación"),
    (LogEntry.Action.UPDATE, "Actualización"),
    (LogEntry.Action.DELETE, "Eliminación"),
]


class AuditLogFilterForm(forms.Form):
    model = forms.CharField(
        required=False,
        label="Modelo",
        widget=forms.TextInput(attrs={"placeholder": "app o modelo"}),
    )
    object_pk = forms.CharField(
        required=False,
        label="ID de instancia",
        widget=forms.TextInput(attrs={"placeholder": "PK"}),
    )
    actor = forms.CharField(
        required=False,
        label="Usuario",
        widget=forms.TextInput(attrs={"placeholder": "usuario"}),
    )
    field_name = forms.CharField(
        required=False,
        max_length=80,
        label="Campo",
        widget=forms.TextInput(attrs={"placeholder": "campo exacto o parcial"}),
    )
    keyword = forms.CharField(
        required=False,
        max_length=120,
        label="Texto en cambios",
        widget=forms.TextInput(attrs={"placeholder": "campo, valor o fragmento"}),
    )
    origin = forms.ChoiceField(
        choices=ORIGIN_CHOICES,
        required=False,
        label="Origen",
    )
    batch_key = forms.CharField(
        required=False,
        max_length=255,
        label="Batch key",
        widget=forms.TextInput(attrs={"placeholder": "lote/correlación"}),
    )
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        required=False,
        label="Evento",
    )
    start_date = forms.DateField(
        required=False,
        label="Desde",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    end_date = forms.DateField(
        required=False,
        label="Hasta",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = date.today().isoformat()
        self.fields["start_date"].widget.attrs["max"] = today
        self.fields["end_date"].widget.attrs["max"] = today
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-control")

    def clean_keyword(self):
        """
        Normaliza espacios para el filtro por texto en `changes`.
        """
        keyword = (self.cleaned_data.get("keyword") or "").strip()
        if not keyword:
            return ""
        terms = [term for term in keyword.split() if term]
        if len(terms) > 8:
            raise forms.ValidationError(
                "Máximo 8 palabras para la búsqueda en cambios."
            )
        return " ".join(terms)

    def clean_field_name(self):
        value = (self.cleaned_data.get("field_name") or "").strip()
        return " ".join(value.split())

    def clean_batch_key(self):
        value = (self.cleaned_data.get("batch_key") or "").strip()
        return value[:255]

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        keyword = cleaned_data.get("keyword")
        field_name = cleaned_data.get("field_name")

        if start_date and end_date and start_date > end_date:
            self.add_error(
                "end_date", "La fecha 'Hasta' no puede ser anterior a 'Desde'."
            )
            return cleaned_data

        if not (keyword or field_name):
            return cleaned_data

        if not start_date or not end_date:
            raise forms.ValidationError(
                "Para buscar por texto o campo en cambios, indicá un rango de fechas (Desde y Hasta)."
            )

        if (end_date - start_date).days > MAX_TEXT_SEARCH_RANGE_DAYS:
            raise forms.ValidationError(
                f"El rango máximo para búsqueda por texto/campo es de {MAX_TEXT_SEARCH_RANGE_DAYS} días."
            )

        return cleaned_data
