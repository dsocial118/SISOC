from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

from core.models import Municipio, Provincia
from pas.models import PasAviso, PasEstado


class PasTitularesImportForm(forms.Form):
    archivo = forms.FileField(
        label="Archivo CSV",
        validators=[FileExtensionValidator(allowed_extensions=["csv"])],
        widget=forms.FileInput(attrs={"accept": ".csv", "class": "form-control"}),
    )

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        if archivo.size > 10 * 1024 * 1024:
            raise ValidationError("El archivo CSV no puede superar los 10 MB.")
        return archivo


class PasRetornoSintysForm(forms.Form):
    EXTENSIONES_PERMITIDAS = {".xlsx", ".xls", ".csv"}
    TAMANIO_MAXIMO = 10 * 1024 * 1024

    archivo = forms.FileField(
        label="Archivo de retorno SINTyS",
        widget=forms.FileInput(
            attrs={"accept": ".xlsx,.xls,.csv", "class": "form-control"}
        ),
    )

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        nombre = (archivo.name or "").lower()
        if not any(
            nombre.endswith(extension) for extension in self.EXTENSIONES_PERMITIDAS
        ):
            raise ValidationError("El retorno debe ser un archivo XLSX, XLS o CSV.")
        if archivo.size > self.TAMANIO_MAXIMO:
            raise ValidationError("El archivo no puede superar los 10 MB.")
        return archivo


class PasDeclaracionJuradaForm(forms.Form):
    SI_NO = (("si", "Sí"), ("no", "No"))

    datos_mi_argentina_confirmados = forms.ChoiceField(
        label="¿Confirmás que tus datos de Mi Argentina son correctos?",
        choices=SI_NO,
        widget=forms.RadioSelect,
    )
    provincia = forms.ModelChoiceField(
        label="Provincia",
        queryset=Provincia.objects.order_by("nombre"),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    municipio = forms.ModelChoiceField(
        label="Municipio",
        queryset=Municipio.objects.order_by("nombre"),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    domicilio = forms.CharField(
        label="Domicilio",
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Calle y número"}
        ),
    )
    correo_electronico = forms.EmailField(
        label="Correo electrónico",
        required=False,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "nombre@correo.com"}
        ),
    )
    telefono_celular = forms.CharField(
        label="Teléfono celular",
        max_length=30,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "inputmode": "tel",
                "placeholder": "11 66 435632",
            }
        ),
    )
    embarazada = forms.ChoiceField(
        label="¿Estás embarazada?", choices=SI_NO, widget=forms.RadioSelect
    )
    controles_embarazo_cumplidos = forms.ChoiceField(
        label="¿Cumpliste con los controles de salud del embarazo?",
        choices=SI_NO,
        required=False,
        widget=forms.RadioSelect,
    )
    hijos_menores_a_cargo = forms.ChoiceField(
        label="¿Tenés hijos menores a cargo?", choices=SI_NO, widget=forms.RadioSelect
    )
    vacunacion_cumplida = forms.ChoiceField(
        label="¿Cumplieron con el Plan Nacional de Vacunación?",
        choices=SI_NO,
        required=False,
        widget=forms.RadioSelect,
    )
    regularidad_escolar_acreditada = forms.ChoiceField(
        label="¿Está acreditada su regularidad escolar?",
        choices=SI_NO,
        required=False,
        widget=forms.RadioSelect,
    )
    gastos_bajo_limite_smvm = forms.ChoiceField(
        label=(
            "En los últimos seis meses, ¿tu promedio mensual de gastos por medios "
            "electrónicos se mantuvo por debajo de un Salario Mínimo Vital y Móvil?"
        ),
        choices=SI_NO,
        widget=forms.RadioSelect,
    )
    no_accedio_mercado_cambios = forms.ChoiceField(
        label="¿Confirmás que no accediste al Mercado de Cambios para ahorrar?",
        choices=SI_NO,
        widget=forms.RadioSelect,
    )
    acepto_declaracion = forms.BooleanField(
        label=(
            "Confirmo que estos datos son correctos y acepto recibir notificaciones del Programa por estos medios."
        )
    )
    firma_nombre_completo = forms.CharField(
        label="Firma con tu nombre completo",
        max_length=255,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Nombre completo"}
        ),
    )

    def __init__(self, *args, persona=None, **kwargs):
        self.persona = persona
        super().__init__(*args, **kwargs)
        provincia_id = (
            self.data.get("provincia")
            if self.is_bound
            else getattr(persona, "provincia_id", None)
        )
        self.fields["municipio"].queryset = (
            Municipio.objects.filter(provincia_id=provincia_id).order_by("nombre")
            if provincia_id
            else Municipio.objects.none()
        )
        self.campos_datos_existentes = (
            {
                "provincia": bool(persona.provincia_id),
                "municipio": bool(persona.municipio_id),
                "domicilio": bool((persona.domicilio or "").strip()),
                "correo_electronico": bool((persona.correo_electronico or "").strip()),
                "telefono_celular": bool((persona.telefono_celular or "").strip()),
            }
            if persona
            else {}
        )
        for campo, existe in self.campos_datos_existentes.items():
            self.fields[campo].widget.attrs["data-pas-existente"] = (
                "true" if existe else "false"
            )
        if persona and not self.is_bound:
            self.initial.update(
                {
                    "provincia": persona.provincia_id,
                    "municipio": persona.municipio_id,
                    "domicilio": persona.domicilio,
                    "correo_electronico": persona.correo_electronico,
                    "telefono_celular": persona.telefono_celular,
                }
            )

    def clean(self):
        data = super().clean()
        confirma = data.get("datos_mi_argentina_confirmados") == "si"
        for campo in (
            "provincia",
            "municipio",
            "domicilio",
            "correo_electronico",
            "telefono_celular",
        ):
            if confirma and self.campos_datos_existentes.get(campo, False):
                data[campo] = getattr(self.persona, campo)
                self._errors.pop(campo, None)
            elif not data.get(campo):
                self.add_error(campo, "Este dato es obligatorio.")
        provincia = data.get("provincia")
        municipio = data.get("municipio")
        if provincia and municipio and municipio.provincia_id != provincia.id:
            self.add_error("municipio", "El municipio no pertenece a la provincia.")
        if data.get("embarazada") == "si" and not data.get(
            "controles_embarazo_cumplidos"
        ):
            self.add_error(
                "controles_embarazo_cumplidos", "Esta respuesta es obligatoria."
            )
        if data.get("embarazada") != "si":
            data["controles_embarazo_cumplidos"] = ""
        if data.get("hijos_menores_a_cargo") == "si":
            for campo in ("vacunacion_cumplida", "regularidad_escolar_acreditada"):
                if not data.get(campo):
                    self.add_error(campo, "Esta respuesta es obligatoria.")
        else:
            data["vacunacion_cumplida"] = ""
            data["regularidad_escolar_acreditada"] = ""
        return data


class PasInformeGenerarForm(forms.Form):
    fecha_creacion_desde = forms.DateField(
        label="Fecha creación desde",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    fecha_creacion_hasta = forms.DateField(
        label="Fecha creación hasta",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    fecha_cambio_desde = forms.DateField(
        label="Fecha de cambios desde",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    fecha_cambio_hasta = forms.DateField(
        label="Fecha de cambios hasta",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    estado_anterior = forms.ModelChoiceField(
        label="Estado anterior",
        required=False,
        queryset=PasEstado.objects.order_by("nombre"),
        empty_label="Todos",
        widget=forms.Select(attrs={"class": "form-select pas-select2"}),
    )
    estado_nuevo = forms.ModelChoiceField(
        label="Estado resultante",
        required=False,
        queryset=PasEstado.objects.order_by("nombre"),
        empty_label="Todos",
        widget=forms.Select(attrs={"class": "form-select pas-select2"}),
    )
    estado_actual = forms.ModelChoiceField(
        label="Estado actual",
        required=False,
        queryset=PasEstado.objects.order_by("nombre"),
        empty_label="Todos",
        widget=forms.Select(attrs={"class": "form-select pas-select2"}),
    )
    provincia = forms.ModelChoiceField(
        label="Provincia",
        required=False,
        queryset=Provincia.objects.order_by("nombre"),
        empty_label="Todas",
        widget=forms.Select(attrs={"class": "form-select pas-select2"}),
    )
    municipio = forms.ModelChoiceField(
        label="Municipio",
        required=False,
        queryset=Municipio.objects.none(),
        empty_label="Todos",
        widget=forms.Select(attrs={"class": "form-select pas-select2"}),
    )
    aviso_actual = forms.ModelChoiceField(
        label="Aviso actual",
        required=False,
        queryset=PasAviso.objects.order_by("codigo"),
        empty_label="Todos",
        widget=forms.Select(attrs={"class": "form-select pas-select2"}),
    )
    aviso_cambio = forms.ModelChoiceField(
        label="Aviso del cambio",
        required=False,
        queryset=PasAviso.objects.order_by("codigo"),
        empty_label="Todos",
        widget=forms.Select(attrs={"class": "form-select pas-select2"}),
    )
    dni = forms.IntegerField(
        label="DNI",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    id_persona = forms.IntegerField(
        label="IdPersona",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    usuario_cambio = forms.CharField(
        label="Usuario que modificó",
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Usuario, nombre o apellido"}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        provincia_id = None
        if self.is_bound:
            value = self.data.get(self.add_prefix("provincia"))
            provincia_id = int(value) if value and str(value).isdigit() else None
        if provincia_id:
            self.fields["municipio"].queryset = Municipio.objects.filter(
                provincia_id=provincia_id
            ).order_by("nombre")

    def clean(self):
        cleaned_data = super().clean()
        self._validar_rango(
            cleaned_data,
            "fecha_creacion_desde",
            "fecha_creacion_hasta",
            "La fecha de creación desde no puede ser posterior a la fecha hasta.",
        )
        self._validar_rango(
            cleaned_data,
            "fecha_cambio_desde",
            "fecha_cambio_hasta",
            "La fecha de cambios desde no puede ser posterior a la fecha hasta.",
        )
        provincia = cleaned_data.get("provincia")
        municipio = cleaned_data.get("municipio")
        if provincia and municipio and municipio.provincia_id != provincia.id:
            self.add_error(
                "municipio",
                "El municipio seleccionado no pertenece a la provincia elegida.",
            )
        return cleaned_data

    def _validar_rango(self, cleaned_data, desde_key, hasta_key, mensaje):
        desde = cleaned_data.get(desde_key)
        hasta = cleaned_data.get(hasta_key)
        if desde and hasta and desde > hasta:
            self.add_error(hasta_key, mensaje)
