from django import forms

from rendicioncuentasmensual.models import DocumentacionAdjunta, RendicionCuentaMensual


class RendicionCuentaMensualForm(forms.ModelForm):
    class Meta:
        model = RendicionCuentaMensual
        fields = "__all__"
        exclude = [
            "comedor",
            "etapa_proceso",
            "subestado_proceso",
            "monto_rendido",
            "fecha_validacion_territorial",
            "fecha_validacion_auditoria",
            "fecha_carga_auditoria",
            "fecha_auditada",
            "acta_auditoria",
            "fecha_regularizacion",
            "documento_regularizacion",
        ]
        widgets = {
            "mes": forms.Select(attrs={"class": "form-control"}),
            "anio": forms.NumberInput(attrs={"class": "form-control"}),
            "documento_adjunto": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        labels = {
            "mes": "Mes",
            "anio": "Año",
            "documento_adjunto": "Documento Adjunto",
            "observaciones": "Observaciones",
            "archivos_adjuntos": "Archivos Adjuntos",
        }


class DocumentacionAdjuntaForm(forms.ModelForm):
    class Meta:
        model = DocumentacionAdjunta
        fields = "__all__"
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "archivo": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
        labels = {
            "nombre": "Nombre del Documento",
            "archivo": "Archivo",
        }


class RendicionProcesoForm(forms.Form):
    accion_proceso = forms.CharField(widget=forms.HiddenInput)
    monto_rendido = forms.DecimalField(
        required=False,
        max_digits=15,
        decimal_places=2,
        min_value=0,
    )
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    acta_auditoria = forms.FileField(required=False)
    documento_regularizacion = forms.FileField(required=False)

    def clean(self):
        cleaned = super().clean()
        accion = cleaned.get("accion_proceso")
        if accion in {"finalizar_sin_observaciones", "finalizar_con_observaciones"}:
            if cleaned.get("monto_rendido") is None:
                self.add_error("monto_rendido", "Ingresá el monto rendido.")
            if not cleaned.get("acta_auditoria"):
                self.add_error("acta_auditoria", "Adjuntá el acta de auditoría.")
        if (
            accion == "finalizar_con_observaciones"
            and not (cleaned.get("observaciones") or "").strip()
        ):
            self.add_error("observaciones", "Ingresá las observaciones de auditoría.")
        if accion == "finalizar_regularizacion" and not cleaned.get(
            "documento_regularizacion"
        ):
            self.add_error(
                "documento_regularizacion",
                "Adjuntá la documentación de regularización.",
            )
        return cleaned
