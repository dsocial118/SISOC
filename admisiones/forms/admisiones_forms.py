from django import forms

from admisiones.models.admisiones import (
    Admision,
    InformeTecnico,
    FormularioProyectoDisposicion,
    FormularioProyectoDeConvenio,
    DocumentosExpediente,
    Anexo,
)


class AdmisionForm(forms.ModelForm):
    class Meta:
        model = Admision
        fields = "__all__"


class InformeTecnicoJuridicoForm(forms.ModelForm):
    class Meta:
        model = InformeTecnico
        exclude = [
            "admision",
            "estado",
            "tipo",
            "declaracion_jurada_recepcion_subsidios",
            "constancia_inexistencia_percepcion_otros_subsidios",
            "organizacion_avalista_1",
            "organizacion_avalista_2",
            "material_difusion_vinculado",
        ]
        labels = {
            "IF_relevamiento_territorial": "IF Relevamiento Territorial",
            "if_relevamiento": "IF Relevamiento",
        }

    def __init__(self, *args, **kwargs):
        admision = kwargs.pop("admision", None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True

        letras_fields = [
            "prestaciones_desayuno_letras",
            "prestaciones_almuerzo_letras",
            "prestaciones_merienda_letras",
            "prestaciones_cena_letras",
        ]

        for field_name in letras_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs["readonly"] = True
                self.fields[field_name].initial = "Cero"

        if admision:
            try:
                anexo = Anexo.objects.filter(admision=admision).last()
                nombre = anexo.responsable_nombre or ""
                apellido = anexo.responsable_apellido or ""
                comedor = admision.comedor
                organizacion = comedor.organizacion

                self.fields["expediente_nro"].initial = anexo.expediente
                self.fields["nombre_organizacion"].initial = organizacion.nombre
                self.fields["cuit_organizacion"].initial = organizacion.cuit
                self.fields["mail_organizacion"].initial = organizacion.email
                self.fields["nombre_espacio"].initial = anexo.efector
                self.fields["tipo_espacio"].initial = anexo.tipo_espacio
                self.fields["barrio_espacio"].initial = comedor.barrio
                self.fields["localidad_espacio"].initial = comedor.localidad
                self.fields["partido_espacio"].initial = comedor.partido
                self.fields["provincia_espacio"].initial = comedor.provincia
                self.fields["domicilio_espacio"].initial = anexo.domicilio
                self.fields["responsable_tarjeta_nombre"].initial = (
                    f"{nombre} {apellido}".strip()
                )
                self.fields["responsable_tarjeta_domicilio"].initial = (
                    anexo.responsable_domicilio
                )
                self.fields["responsable_tarjeta_mail"].initial = anexo.responsable_mail

            except Anexo.DoesNotExist:
                pass


class InformeTecnicoBaseForm(forms.ModelForm):
    class Meta:
        model = InformeTecnico
        exclude = [
            "admision",
            "estado",
            "tipo",
            "validacion_registro_nacional",
            "IF_relevamiento_territorial",
        ]

    def __init__(self, *args, **kwargs):
        admision = kwargs.pop("admision", None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True

        letras_fields = [
            "prestaciones_desayuno_letras",
            "prestaciones_almuerzo_letras",
            "prestaciones_merienda_letras",
            "prestaciones_cena_letras",
        ]

        for field_name in letras_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs["readonly"] = True
                self.fields[field_name].initial = "Cero"

        if admision:
            try:
                anexo = Anexo.objects.filter(admision=admision).last()
                nombre = anexo.responsable_nombre or ""
                apellido = anexo.responsable_apellido or ""
                comedor = admision.comedor
                organizacion = comedor.organizacion

                self.fields["expediente_nro"].initial = anexo.expediente
                self.fields["nombre_organizacion"].initial = organizacion.nombre
                self.fields["cuit_organizacion"].initial = organizacion.cuit
                self.fields["mail_organizacion"].initial = organizacion.email
                self.fields["nombre_espacio"].initial = anexo.efector
                self.fields["tipo_espacio"].initial = anexo.tipo_espacio
                self.fields["tipo_espacio"].initial = anexo.tipo_espacio
                self.fields["barrio_espacio"].initial = comedor.barrio
                self.fields["localidad_espacio"].initial = comedor.localidad
                self.fields["partido_espacio"].initial = comedor.partido
                self.fields["provincia_espacio"].initial = comedor.provincia
                self.fields["domicilio_espacio"].initial = anexo.domicilio
                self.fields["responsable_tarjeta_nombre"].initial = (
                    f"{nombre} {apellido}".strip()
                )
                self.fields["responsable_tarjeta_domicilio"].initial = (
                    anexo.responsable_domicilio
                )
                self.fields["responsable_tarjeta_mail"].initial = anexo.responsable_mail

            except Anexo.DoesNotExist:
                pass


class InformeTecnicoEstadoForm(forms.Form):
    ESTADOS = [
        ("A subsanar", "A subsanar"),
        ("Validado", "Validado"),
    ]
    estado = forms.ChoiceField(choices=ESTADOS, required=True)
    campos_a_subsanar = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=[],
    )
    observacion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, **kwargs):
        campos_choices = kwargs.pop("campos_choices", [])
        super().__init__(*args, **kwargs)
        self.fields["campos_a_subsanar"].choices = campos_choices

    def clean(self):
        cleaned_data = super().clean()
        estado = cleaned_data.get("estado")
        campos = cleaned_data.get("campos_a_subsanar")

        if estado == "A subsanar" and not campos:
            raise forms.ValidationError(
                "Debe marcar al menos un campo para subsanar cuando el estado es 'A subsanar'."
            )
        return cleaned_data


class CaratularForm(forms.ModelForm):

    num_expediente = forms.CharField(required=True, label="Número de Expediente")

    class Meta:
        model = Admision
        fields = ["num_expediente"]


class LegalesRectificarForm(forms.ModelForm):
    class Meta:
        model = Admision
        fields = ["observaciones"]
        widgets = {
            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Detalle sus observaciones.",
                    "rows": 4,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class ProyectoDisposicionForm(forms.ModelForm):
    class Meta:
        model = FormularioProyectoDisposicion
        exclude = ["admision", "creado", "creado_por", "archivo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class ProyectoConvenioForm(forms.ModelForm):
    class Meta:
        model = FormularioProyectoDeConvenio
        exclude = ["admision", "creado", "creado_por", "archivo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class LegalesNumIFForm(forms.ModelForm):
    class Meta:
        model = Admision
        fields = ["legales_num_if"]
        labels = {
            "legales_num_if": "Numero IF",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class DocumentosExpedienteForm(forms.ModelForm):
    class Meta:
        model = DocumentosExpediente
        fields = ["value", "tipo"]
        labels = {
            "value": "",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class AnexoForm(forms.ModelForm):
    class Meta:
        model = Anexo
        exclude = ["admision"]
        error_messages = {
            "responsable_cuit": {
                "max_value": "El CUIT/CUIL debe tener como máximo 11 dígitos.",
                "invalid": "Ingresá solo números sin puntos ni guiones.",
                "required": "El campo CUIT/CUIL es obligatorio.",
            }
        }
        widgets = {
            "desayuno_lunes": forms.NumberInput(
                attrs={"min": 0, "class": "form-control"}
            ),
            "desayuno_martes": forms.NumberInput(
                attrs={"min": 0, "class": "form-control"}
            ),
            "desayuno_miercoles": forms.NumberInput(
                attrs={"min": 0, "class": "form-control"}
            ),
            "desayuno_jueves": forms.NumberInput(
                attrs={"min": 0, "class": "form-control"}
            ),
            "desayuno_viernes": forms.NumberInput(
                attrs={"min": 0, "class": "form-control"}
            ),
            "desayuno_sabado": forms.NumberInput(
                attrs={"min": 0, "class": "form-control"}
            ),
            "desayuno_domingo": forms.NumberInput(
                attrs={"min": 0, "class": "form-control"}
            ),
            "almuerzo_lunes": forms.NumberInput(
                attrs={"min": 0, "class": "form-control"}
            ),
            "almuerzo_martes": forms.NumberInput(
                attrs={"min": 0, "class": "form-control"}
            ),
            "almuerzo_miercoles": forms.NumberInput(
                attrs={"min": 0, "class": "form-control"}
            ),
            "almuerzo_jueves": forms.NumberInput(
                attrs={"min": 0, "class": "form-control"}
            ),
            "almuerzo_viernes": forms.NumberInput(
                attrs={"min": 0, "class": "form-control"}
            ),
            "almuerzo_sabado": forms.NumberInput(
                attrs={"min": 0, "class": "form-control"}
            ),
            "almuerzo_domingo": forms.NumberInput(
                attrs={"min": 0, "class": "form-control"}
            ),
            "merienda_lunes": forms.NumberInput(
                attrs={"min": 0, "class": "form-control", "value": 0}
            ),
            "merienda_martes": forms.NumberInput(
                attrs={"min": 0, "class": "form-control"}
            ),
            "merienda_miercoles": forms.NumberInput(
                attrs={"min": 0, "class": "form-control"}
            ),
            "merienda_jueves": forms.NumberInput(
                attrs={"min": 0, "class": "form-control"}
            ),
            "merienda_viernes": forms.NumberInput(
                attrs={"min": 0, "class": "form-control"}
            ),
            "merienda_sabado": forms.NumberInput(
                attrs={"min": 0, "class": "form-control"}
            ),
            "merienda_domingo": forms.NumberInput(
                attrs={"min": 0, "class": "form-control"}
            ),
            "cena_lunes": forms.NumberInput(attrs={"min": 0, "class": "form-control"}),
            "cena_martes": forms.NumberInput(attrs={"min": 0, "class": "form-control"}),
            "cena_miercoles": forms.NumberInput(
                attrs={"min": 0, "class": "form-control"}
            ),
            "cena_jueves": forms.NumberInput(attrs={"min": 0, "class": "form-control"}),
            "cena_viernes": forms.NumberInput(
                attrs={"min": 0, "class": "form-control"}
            ),
            "cena_sabado": forms.NumberInput(attrs={"min": 0, "class": "form-control"}),
            "cena_domingo": forms.NumberInput(
                attrs={"min": 0, "class": "form-control"}
            ),
        }

    def __init__(self, *args, **kwargs):
        admision = kwargs.pop("admision", None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.NumberInput):
                if self.initial.get(field_name) is None:
                    field.widget.attrs.setdefault("value", 0)

        if admision and admision.comedor:
            comedor = admision.comedor
            calle = getattr(comedor, "calle", "")
            numero = getattr(comedor, "numero", "")

            self.fields["efector"].initial = comedor.nombre
            self.fields["domicilio"].initial = f"{calle} {numero}".strip()
            self.fields["expediente"].initial = admision.num_expediente
