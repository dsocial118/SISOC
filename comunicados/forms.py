from django import forms
from .models import Comunicado, ComunicadoAdjunto, TipoComunicado, SubtipoComunicado
from .permissions import (
    es_tecnico, is_admin, get_comedores_del_usuario,
    can_create_comunicado_interno
)


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        # Si no hay datos, retornar lista vacía
        if not data:
            return []

        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            # Filtrar valores vacíos/None de la lista
            result = [single_file_clean(d, initial) for d in data if d]
        else:
            # Un solo archivo
            result = [single_file_clean(data, initial)]
        return result


class ComunicadoForm(forms.ModelForm):
    # Campo para subir múltiples archivos a la vez
    archivos_adjuntos = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={"class": "form-control", "multiple": True}),
    )

    class Meta:
        model = Comunicado
        fields = [
            "titulo",
            "cuerpo",
            "tipo",
            "subtipo",
            "destacado",
            "para_todos_comedores",
            "comedores",
            "fecha_vencimiento",
        ]
        widgets = {
            "cuerpo": forms.Textarea(attrs={"rows": 6}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "subtipo": forms.Select(attrs={"class": "form-select"}),
            "fecha_vencimiento": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "destacado": forms.CheckboxInput(
                attrs={"class": "form-check-input", "role": "switch"}
            ),
            "para_todos_comedores": forms.CheckboxInput(
                attrs={"class": "form-check-input", "role": "switch"}
            ),
            "comedores": forms.SelectMultiple(attrs={"class": "form-select", "size": "6"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self._apply_bootstrap_styles()
        self._configure_fields_for_user()

        # Formatear fecha_vencimiento para el input datetime-local
        if self.instance and self.instance.fecha_vencimiento:
            self.initial["fecha_vencimiento"] = self.instance.fecha_vencimiento.strftime(
                "%Y-%m-%dT%H:%M"
            )

    def _configure_fields_for_user(self):
        """Configura los campos según los permisos del usuario."""
        if not self.user:
            return

        # Filtrar comedores según permisos del usuario
        self.fields['comedores'].queryset = get_comedores_del_usuario(self.user)

        # Si es técnico (no admin), solo puede crear comunicados externos a comedores
        if es_tecnico(self.user) and not is_admin(self.user):
            self.fields['tipo'].choices = [
                (TipoComunicado.EXTERNO, 'Comunicación Externa')
            ]
            self.fields['tipo'].initial = TipoComunicado.EXTERNO
            self.fields['subtipo'].choices = [
                (SubtipoComunicado.COMEDORES, 'Comunicación a Comedores')
            ]
            self.fields['subtipo'].initial = SubtipoComunicado.COMEDORES
            # Ocultar destacado para técnicos (solo aplica a internos)
            self.fields['destacado'].widget = forms.HiddenInput()
            self.fields['destacado'].initial = False

        # Si no puede crear internos, forzar externo
        elif not can_create_comunicado_interno(self.user):
            self.fields['tipo'].choices = [
                (TipoComunicado.EXTERNO, 'Comunicación Externa')
            ]
            self.fields['tipo'].initial = TipoComunicado.EXTERNO

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
