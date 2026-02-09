from django import forms
from .models import Comunicado, ComunicadoAdjunto


class ComunicadoForm(forms.ModelForm):
    class Meta:
        model = Comunicado
        fields = [
            "titulo",
            "cuerpo",
            "destacado",
            "fecha_vencimiento",
        ]
        widgets = {
            "cuerpo": forms.Textarea(attrs={"rows": 6}),
            "fecha_vencimiento": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "destacado": forms.CheckboxInput(
                attrs={"class": "form-check-input", "role": "switch"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_styles()

        # Formatear fecha_vencimiento para el input datetime-local
        if self.instance and self.instance.fecha_vencimiento:
            self.initial["fecha_vencimiento"] = self.instance.fecha_vencimiento.strftime(
                "%Y-%m-%dT%H:%M"
            )

    def _apply_bootstrap_styles(self):
        text_like = (
            forms.TextInput,
            forms.NumberInput,
            forms.EmailInput,
            forms.URLInput,
            forms.PasswordInput,
            forms.DateInput,
            forms.TimeInput,
            forms.DateTimeInput,
            forms.Textarea,
        )
        select_like = (forms.Select, forms.SelectMultiple)
        for field in self.fields.values():
            widget = field.widget
            css = widget.attrs.get("class", "")
            if isinstance(widget, text_like):
                widget.attrs["class"] = f"{css} form-control".strip()
            elif isinstance(widget, select_like):
                widget.attrs["class"] = f"{css} form-select".strip()
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = f"{css} form-check-input".strip()


class ComunicadoAdjuntoForm(forms.ModelForm):
    class Meta:
        model = ComunicadoAdjunto
        fields = ["archivo"]
        widgets = {
            "archivo": forms.FileInput(attrs={"class": "form-control"}),
        }


# Formset para manejar múltiples adjuntos
ComunicadoAdjuntoFormSet = forms.inlineformset_factory(
    Comunicado,
    ComunicadoAdjunto,
    form=ComunicadoAdjuntoForm,
    extra=1,
    can_delete=True,
)
