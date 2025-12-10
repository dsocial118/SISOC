from datetime import date

from django import forms

from auditlog.models import LogEntry


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
