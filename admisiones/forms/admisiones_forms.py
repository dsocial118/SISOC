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
            "estado_formulario",
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
        widgets = {
            "fecha_vencimiento_mandatos": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            )
        }

    def __init__(self, *args, **kwargs):
        admision = kwargs.pop("admision", None)
        self.require_full = kwargs.pop("require_full", False)
        super().__init__(*args, **kwargs)

        if self.require_full:
            for field in self.fields.values():
                field.required = True
        else:
            for field in self.fields.values():
                field.required = False

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
                anexo = Anexo.objects.filter(admision=admision).last()
                comedor = admision.comedor
                organizacion = comedor.organizacion if comedor else None

                self.fields["expediente_nro"].initial = admision.num_expediente
                calle = getattr(comedor, "calle", "")
                numero = getattr(comedor, "numero", "")

                self.fields["nombre_espacio"].initial = comedor.nombre
                self.fields["domicilio_espacio"].initial = f"{calle} {numero}".strip()
                self.fields["barrio_espacio"].initial = getattr(comedor, "barrio", "")
                self.fields["localidad_espacio"].initial = getattr(
                    comedor, "localidad", ""
                )
                self.fields["partido_espacio"].initial = getattr(comedor, "partido", "")
                self.fields["provincia_espacio"].initial = getattr(
                    comedor, "provincia", ""
                )

                if anexo:
                    nombre = anexo.responsable_nombre or ""
                    apellido = anexo.responsable_apellido or ""

                    self.fields["nombre_espacio"].initial = anexo.efector
                    self.fields["tipo_espacio"].initial = anexo.tipo_espacio
                    self.fields["domicilio_espacio"].initial = anexo.domicilio
                    self.fields["responsable_tarjeta_nombre"].initial = (
                        f"{nombre} {apellido}".strip()
                    )
                    self.fields["responsable_tarjeta_domicilio"].initial = (
                        anexo.responsable_domicilio
                    )
                    self.fields["responsable_tarjeta_mail"].initial = (
                        anexo.responsable_mail
                    )

                if organizacion:
                    self.fields["nombre_organizacion"].initial = organizacion.nombre
                    self.fields["cuit_organizacion"].initial = organizacion.cuit
                    self.fields["mail_organizacion"].initial = organizacion.email
                    self.fields["telefono_organizacion"].initial = organizacion.telefono
                    self.fields["domicilio_organizacion"].initial = (
                        organizacion.domicilio
                    )
                    self.fields["localidad_organizacion"].initial = (
                        organizacion.localidad
                    )
                    self.fields["provincia_organizacion"].initial = (
                        organizacion.provincia
                    )
                    self.fields["partido_organizacion"].initial = organizacion.partido
                    self.fields["fecha_vencimiento_mandatos"].initial = (
                        organizacion.fecha_vencimiento
                    )


class InformeTecnicoBaseForm(forms.ModelForm):
    class Meta:
        model = InformeTecnico
        exclude = [
            "admision",
            "estado",
            "estado_formulario",
            "tipo",
            "validacion_registro_nacional",
            "IF_relevamiento_territorial",
        ]
        widgets = {
            "fecha_vencimiento_mandatos": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        admision = kwargs.pop("admision", None)
        self.require_full = kwargs.pop("require_full", False)
        super().__init__(*args, **kwargs)

        if self.require_full:
            for field in self.fields.values():
                field.required = True
        else:
            for field in self.fields.values():
                field.required = False

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
                anexo = Anexo.objects.filter(admision=admision).last()
                comedor = admision.comedor
                organizacion = comedor.organizacion if comedor else None

                if anexo:
                    nombre = anexo.responsable_nombre or ""
                    apellido = anexo.responsable_apellido or ""
                    self.fields["expediente_nro"].initial = anexo.expediente
                    self.fields["nombre_espacio"].initial = anexo.efector
                    self.fields["tipo_espacio"].initial = anexo.tipo_espacio
                    self.fields["barrio_espacio"].initial = getattr(
                        comedor, "barrio", ""
                    )
                    self.fields["localidad_espacio"].initial = getattr(
                        comedor, "localidad", ""
                    )
                    self.fields["partido_espacio"].initial = getattr(
                        comedor, "partido", ""
                    )
                    self.fields["provincia_espacio"].initial = getattr(
                        comedor, "provincia", ""
                    )
                    self.fields["domicilio_espacio"].initial = anexo.domicilio
                    self.fields["responsable_tarjeta_nombre"].initial = (
                        f"{nombre} {apellido}".strip()
                    )
                    self.fields["responsable_tarjeta_domicilio"].initial = (
                        anexo.responsable_domicilio
                    )
                    self.fields["responsable_tarjeta_mail"].initial = (
                        anexo.responsable_mail
                    )

                if organizacion:
                    self.fields["nombre_organizacion"].initial = organizacion.nombre
                    self.fields["cuit_organizacion"].initial = organizacion.cuit
                    self.fields["mail_organizacion"].initial = organizacion.email
                    self.fields["telefono_organizacion"].initial = organizacion.telefono
                    self.fields["domicilio_organizacion"].initial = (
                        organizacion.domicilio
                    )
                    self.fields["localidad_organizacion"].initial = (
                        organizacion.localidad
                    )
                    self.fields["provincia_organizacion"].initial = (
                        organizacion.provincia
                    )
                    self.fields["partido_organizacion"].initial = organizacion.partido
                    self.fields["fecha_vencimiento_mandatos"].initial = (
                        organizacion.fecha_vencimiento
                    )


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
        exclude = [
            "admision",
            "creado",
            "creado_por",
            "archivo",
            "numero_if",
            "archivo_docx",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class ProyectoConvenioForm(forms.ModelForm):
    class Meta:
        model = FormularioProyectoDeConvenio
        exclude = [
            "admision",
            "creado",
            "creado_por",
            "archivo",
            "numero_if",
            "archivo_docx",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class LegalesNumIFForm(forms.ModelForm):
    class Meta:
        model = Admision
        fields = ["legales_num_if"]
        labels = {
            "legales_num_if": "Número de expediente",
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
        exclude = [
            "admision",
            "expediente",
            "efector",
            "tipo_espacio",
            "domicilio",
            "barrio",
            "mail",
        ]
        error_messages = {
            "responsable_cuit": {
                "max_value": "El CUIT/CUIL debe tener como máximo 11 dígitos.",
                "invalid": "Ingresá solo números sin puntos ni guiones.",
                "required": "El campo CUIT/CUIL es obligatorio.",
            },
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
        self.require_full = kwargs.pop("require_full", False)
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.required = self.require_full

        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.NumberInput):
                if self.initial.get(field_name) is None:
                    field.widget.attrs.setdefault("value", 0)

        if not self.instance.pk:
            self.fields["total_acreditaciones"].initial = "6"
            self.fields["plazo_ejecucion"].initial = "6 meses"


class ConvenioNumIFFORM(forms.ModelForm):
    class Meta:
        model = FormularioProyectoDeConvenio
        fields = ["numero_if"]
        labels = {
            "numero_if": "Número de IF de Proyecto de Convenio",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class DisposicionNumIFFORM(forms.ModelForm):
    class Meta:
        model = FormularioProyectoDisposicion
        fields = ["numero_if"]
        labels = {
            "numero_if": "Número de IF de Proyecto Disposición",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class IntervencionJuridicosForm(forms.ModelForm):
    class Meta:
        model = Admision
        fields = [
            "intervencion_juridicos",
            "rechazo_juridicos_motivo",
            "dictamen_motivo",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["intervencion_juridicos"].required = True
        self.fields["rechazo_juridicos_motivo"].required = False
        self.fields["dictamen_motivo"].required = False

    def clean(self):
        cleaned_data = super().clean()
        intervencion = cleaned_data.get("intervencion_juridicos")
        motivo = cleaned_data.get("rechazo_juridicos_motivo")
        dictamen = cleaned_data.get("dictamen_motivo")

        if intervencion == "rechazado":
            if not motivo:
                self.add_error(
                    "rechazo_juridicos_motivo",
                    "Debe especificar el motivo cuando la intervención jurídica es Rechazado.",
                )
            elif motivo == "dictamen" and not dictamen:
                self.add_error(
                    "dictamen_motivo",
                    "Debe especificar el detalle cuando el motivo de rechazo es Dictamen.",
                )

        return cleaned_data


class InformeSGAForm(forms.ModelForm):
    class Meta:
        model = Admision
        fields = ["informe_sga"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class ConvenioForm(forms.ModelForm):
    class Meta:
        model = Admision
        fields = ["numero_convenio", "archivo_convenio"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class DisposicionForm(forms.ModelForm):
    class Meta:
        model = Admision
        fields = ["numero_disposicion", "archivo_disposicion"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class ReinicioExpedienteForm(forms.ModelForm):
    class Meta:
        model = Admision
        fields = ["observaciones_reinicio_expediente"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True
