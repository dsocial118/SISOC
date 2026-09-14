from django import forms
from django.core.exceptions import ValidationError as DjangoValidationError

from rendicioncuentasmensual.models import DocumentacionAdjunta, RendicionCuentaMensual
from rendicioncuentasmensual.services import RendicionCuentaMensualService


def _coerce_booleano_nullable(valor):
    if valor in (True, "True"):
        return True
    if valor in (False, "False"):
        return False
    return None


class RendicionActaMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        proyecto = str(obj.proyecto) if obj.proyecto else "Sin proyecto"
        convenio = obj.convenio or "Sin convenio"
        numero = obj.numero_rendicion or "Sin número"
        if obj.periodo_inicio and obj.periodo_fin:
            periodo = f"{obj.periodo_inicio:%d/%m/%Y} al {obj.periodo_fin:%d/%m/%Y}"
        else:
            periodo = "Sin período"
        return f"{proyecto} - {convenio} - {numero} - {periodo}"


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


class RendicionDatosForm(forms.ModelForm):
    """Edición de los datos generales de una rendición ya cargada.

    Actualización parcial (issue #2377): ningún campo es obligatorio para
    guardar. Un campo que llega vacío conserva el valor persistido; `nombre` es
    la excepción, porque es opcional en el modelo y por lo tanto se puede
    limpiar a propósito. Las reglas de convenio, número y período son las mismas
    del alta: se delegan en `RendicionCuentaMensualService`.
    """

    CAMPOS_QUE_CONSERVAN_VALOR = (
        "convenio",
        "numero_rendicion",
        "periodo_inicio",
        "periodo_fin",
    )

    convenio = forms.ChoiceField(
        required=False,
        choices=[("", "---------")]
        + [(valor, valor) for valor in RendicionCuentaMensualService.CONVENIOS_VALIDOS],
    )
    numero_rendicion = forms.TypedChoiceField(
        required=False,
        coerce=int,
        empty_value=None,
        choices=[("", "---------")]
        + [
            (numero, str(numero))
            for numero in range(
                RendicionCuentaMensualService.NUMERO_RENDICION_MIN,
                RendicionCuentaMensualService.NUMERO_RENDICION_MAX + 1,
            )
        ],
    )
    # `<input type="date">` solo acepta un value en ISO. Sin `format` Django lo
    # renderiza como dd/mm/aaaa, el navegador descarta el valor y el campo se ve
    # vacío: esa era la causa de que la edición apareciera en blanco.
    periodo_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    periodo_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )

    class Meta:
        model = RendicionCuentaMensual
        fields = (
            "convenio",
            "numero_rendicion",
            "periodo_inicio",
            "periodo_fin",
            "nombre",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se captura antes de que `_post_clean` vuelque cleaned_data sobre la
        # instancia, para poder distinguir "no cambió el número" de "lo cambió".
        self._numero_persistido = (
            self.instance.numero_rendicion if self.instance.pk else None
        )

    def _volcar_errores_de_dominio(self, error):
        for campo, mensajes in error.message_dict.items():
            destino = campo if campo in self.fields else None
            for mensaje in mensajes:
                self.add_error(destino, mensaje)

    def clean(self):
        cleaned = super().clean()

        for campo in self.CAMPOS_QUE_CONSERVAN_VALOR:
            if cleaned.get(campo) in (None, ""):
                cleaned[campo] = getattr(self.instance, campo, None)

        cleaned["nombre"] = (cleaned.get("nombre") or "").strip() or None

        convenio = cleaned.get("convenio")
        numero_rendicion = cleaned.get("numero_rendicion")

        # Una rendición histórica sin convenio ni número se guarda como está: no
        # hay contra qué validar y el issue pide no exigir datos para editar.
        if not convenio or not numero_rendicion:
            return cleaned

        try:
            RendicionCuentaMensualService.validar_datos_generales(
                comedor=self.instance.comedor,
                proyecto=self.instance.proyecto,
                convenio=convenio,
                numero_rendicion=numero_rendicion,
                periodo=(cleaned.get("periodo_inicio"), cleaned.get("periodo_fin")),
                linea_programatica=self.instance.linea_programatica,
                excluir_pk=self.instance.pk,
                numero_actual=self._numero_persistido,
            )
        except DjangoValidationError as error:
            self._volcar_errores_de_dominio(error)

        return cleaned


class RendicionProcesoForm(forms.Form):
    accion_proceso = forms.CharField(widget=forms.HiddenInput)
    monto_rendido = forms.DecimalField(
        required=False,
        max_digits=15,
        decimal_places=2,
        min_value=0,
        label="Monto rendido",
    )
    monto_observado = forms.DecimalField(
        required=False,
        max_digits=15,
        decimal_places=2,
        min_value=0,
        label="Monto observado",
    )
    genera_acta_auditoria = forms.TypedChoiceField(
        required=False,
        choices=((True, "Sí"), (False, "No")),
        coerce=_coerce_booleano_nullable,
        empty_value=None,
        widget=forms.RadioSelect,
        label="¿Se genera acta de auditoría?",
        error_messages={"invalid_choice": "Seleccioná una opción válida."},
    )
    rendiciones_incluidas = RendicionActaMultipleChoiceField(
        required=False,
        queryset=RendicionCuentaMensual.objects.none(),
        label="Rendiciones incluidas en el acta",
        error_messages={
            "invalid_choice": "Seleccioná una rendición válida.",
            "invalid_list": "La selección de rendiciones no es válida.",
            "invalid_pk_value": (
                "El valor “%(pk)s” no corresponde a una rendición válida."
            ),
        },
    )
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    acta_auditoria = forms.FileField(required=False)
    documento_regularizacion = forms.FileField(required=False)

    def __init__(self, *args, rendicion=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.rendicion = rendicion
        self.es_linea_tradicional = bool(
            rendicion
            and getattr(rendicion, "linea_programatica", None)
            == RendicionCuentaMensual.LINEA_TRADICIONAL
        )
        if self.es_linea_tradicional and rendicion.pk:
            self.fields["rendiciones_incluidas"].queryset = (
                RendicionCuentaMensualService.rendiciones_elegibles_para_acta(rendicion)
            )

    def clean(self):
        cleaned = super().clean()
        accion = cleaned.get("accion_proceso")
        if accion in {"finalizar_sin_observaciones", "finalizar_con_observaciones"}:
            if cleaned.get("monto_rendido") is None:
                self.add_error("monto_rendido", "Ingresá el monto rendido.")
            genera_acta = cleaned.get("genera_acta_auditoria")
            rendiciones_incluidas = cleaned.get("rendiciones_incluidas")
            if self.es_linea_tradicional and genera_acta is None:
                self.add_error(
                    "genera_acta_auditoria",
                    "Indicá si se genera acta de auditoría.",
                )
            if genera_acta is False and rendiciones_incluidas:
                self.add_error(
                    "rendiciones_incluidas",
                    "No se pueden seleccionar rendiciones si no se genera acta de auditoría.",
                )
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
