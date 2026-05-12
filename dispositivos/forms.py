from django import forms
from django.core.exceptions import ValidationError

from core.models import Municipio, Provincia

from .models import Dispositivo
from .validators import DOCUMENTACION_ACCEPT_ATTR, DOCUMENTACION_UPLOAD_FIELDS


class DispositivoForm(forms.ModelForm):
    DIAS_ATENCION_CHOICES = [
        ("lunes", "Lunes"),
        ("martes", "Martes"),
        ("miercoles", "Miércoles"),
        ("jueves", "Jueves"),
        ("viernes", "Viernes"),
        ("sabado", "Sábado"),
        ("domingo", "Domingo"),
    ]
    HORARIOS_FUNCIONAMIENTO_CHOICES = [
        ("manana", "Mañana (06:00 a 12:00)"),
        ("tarde", "Tarde (12:00 a 18:00)"),
        ("noche", "Noche (18:00 a 00:00)"),
        ("madrugada", "Madrugada (00:00 a 06:00)"),
    ]

    POBLACION_DESTINATARIA_CHOICES = [
        ("hombres", "Hombres"),
        ("mujeres", "Mujeres"),
        ("familia_monoparental", "Familia monoparental"),
        ("familia_nuclear", "Familia nuclear"),
        ("lgbtiq", "Personas LGBTIQ+"),
        ("otro", "Otro"),
    ]
    FRANJA_ETARIA_CHOICES = [
        ("nnya", "Niñas/niños/adolescentes"),
        ("jovenes", "Jóvenes (18 a 29 años)"),
        ("adultos", "Adultos (30 a 59 años)"),
        ("adultos_mayores", "Adultos mayores (60 años o más)"),
    ]
    MODALIDAD_INGRESO_CHOICES = [
        ("derivacion_institucional", "Derivación institucional"),
        ("llegada_espontanea", "Llegada espontánea"),
        ("turnos_previos", "Turnos previos"),
        ("derivacion_org_social", "Derivación de organizaciones sociales"),
        ("otro", "Otro"),
    ]
    DOCUMENTACION_INGRESO_CHOICES = [
        ("dni", "DNI"),
        ("derivacion", "Derivación"),
        ("estudios_medicos", "Estudios/Informes Médicos"),
        ("antecedentes_penales", "Antecedentes penales"),
        ("certificado_domicilio", "Certificado de domicilio"),
        ("informe_social", "Informe Social"),
        ("otro", "Otro"),
    ]
    REQUISITOS_INGRESO_CHOICES = [
        ("horario_ingreso", "El dispositivo tiene horario de ingreso"),
        ("acta_convivencia", "Requiere firma de acta/acuerdo de convivencia"),
        (
            "sin_sustancias",
            "No permite el ingreso de personas bajo efectos de alcohol u otras sustancias",
        ),
        ("pertenencias_personales", "Permite el ingreso con pertenencias personales"),
        ("mascotas", "Permite el ingreso con mascotas"),
        ("otro", "Otro"),
    ]
    SERVICIOS_BRINDADOS_CHOICES = [
        ("alojamiento_nocturno", "Alojamiento nocturno"),
        ("alimentacion", "Alimentación"),
        ("duchas_higiene", "Duchas / higiene"),
        ("roperia", "Ropería"),
        ("acompanamiento_social", "Acompañamiento social"),
        ("aps", "Atención primaria de salud"),
        ("salud_mental", "Atención en salud mental"),
        ("consumos_problematicos", "Abordaje de consumos problemáticos"),
        ("gestion_documentacion", "Gestión de documentación"),
        ("actividades_recreativas", "Actividades recreativas"),
        ("inclusion_laboral", "Inclusión laboral / capacitación"),
        ("otro", "Otro"),
    ]
    TIPO_ACTIVIDADES_FORMATIVAS_CHOICES = [
        (
            "habilidades_vida",
            "Talleres de habilidades o saberes para la vida cotidiana",
        ),
        ("recreativos_culturales", "Talleres recreativos o culturales"),
        ("oficios", "Capacitación en oficios"),
        ("inclusion_laboral", "Programas de inclusión laboral"),
        ("apoyo_escolar", "Apoyo escolar"),
        ("alfabetizacion", "Alfabetización"),
        ("terminalidad", "Terminalidad educativa (primaria o secundaria)"),
        ("ninguna", "Ninguna de las anteriores"),
        ("otro", "Otro"),
    ]
    TIPO_INFO_REGISTRADA_CHOICES = [
        ("datos_basicos", "Datos personales básicos"),
        ("fecha_ingreso", "Fecha de ingreso"),
        ("fecha_egreso", "Fecha de egreso"),
        ("trayectoria_situacion_calle", "Trayectoria de Situación de calle"),
        ("derivaciones", "Derivaciones institucionales"),
        ("salud", "Información de salud"),
        ("ingresos", "Información de ingresos económicos"),
        ("grupo_familiar", "Información de grupo familiar"),
        ("otro", "Otro"),
    ]
    INFRAESTRUCTURA_DISPONIBLE_CHOICES = [
        ("cocina", "Cocina"),
        ("comedor", "Comedor"),
        ("dormitorios", "Dormitorios"),
        ("banos", "Baños"),
        ("lavanderia", "Lavandería"),
        ("consultorio", "Consultorio"),
        ("oficina", "Oficina administrativa"),
        ("espacios_recreativos", "Espacios recreativos"),
        ("internet", "Conexión Internet"),
        ("otro", "Otro"),
    ]
    INFRAESTRUCTURA_ACCESIBILIDAD_CHOICES = [
        ("rampa", "Rampa de acceso"),
        ("banos_adaptados", "Baños adaptados"),
        ("camas_accesibles", "Habitaciones o camas accesibles"),
        ("mobiliario_adaptado", "Mobiliario adaptado"),
        ("senaletica", "Señalética accesible"),
        ("braille", "Comunicación en Braille"),
        (
            "discapacidad_visual_auditiva",
            "Accesibilidad para personas con discapacidad visual o auditiva",
        ),
        ("otro", "Otro"),
    ]
    ARTICULACIONES_CHOICES = [
        ("salud", "Salud"),
        ("consumos", "Consumos problemáticos"),
        ("desarrollo_social", "Desarrollo social"),
        ("justicia", "Justicia y asesoramiento legal"),
        ("ninez", "Niñez y adolescencia"),
        ("genero", "Género y violencias"),
        ("empleo", "Empleo y formación laboral"),
        ("discapacidad", "Discapacidad"),
        ("seguridad", "Seguridad"),
        ("organizaciones_comunitarias", "Organizaciones comunitarias"),
        ("documentacion", "Organismos de documentación/migraciones"),
        ("ninguna", "Ninguna de las anteriores"),
        ("otro", "Otro"),
    ]

    dias_atencion = forms.MultipleChoiceField(
        required=False,
        choices=DIAS_ATENCION_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    horarios_funcionamiento = forms.MultipleChoiceField(
        required=False,
        choices=HORARIOS_FUNCIONAMIENTO_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    poblacion_destinataria = forms.MultipleChoiceField(
        required=False,
        choices=POBLACION_DESTINATARIA_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    franja_etaria_destinataria = forms.MultipleChoiceField(
        required=False,
        choices=FRANJA_ETARIA_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    modalidad_ingreso = forms.MultipleChoiceField(
        required=False,
        choices=MODALIDAD_INGRESO_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    documentacion_ingreso = forms.MultipleChoiceField(
        required=False,
        choices=DOCUMENTACION_INGRESO_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    requisitos_ingreso = forms.MultipleChoiceField(
        required=False,
        choices=REQUISITOS_INGRESO_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    servicios_brindados = forms.MultipleChoiceField(
        required=False,
        choices=SERVICIOS_BRINDADOS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    tipos_actividades_formativas = forms.MultipleChoiceField(
        required=False,
        choices=TIPO_ACTIVIDADES_FORMATIVAS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    tipo_informacion_registrada = forms.MultipleChoiceField(
        required=False,
        choices=TIPO_INFO_REGISTRADA_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    infraestructura_disponible = forms.MultipleChoiceField(
        required=False,
        choices=INFRAESTRUCTURA_DISPONIBLE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    infraestructura_accesibilidad = forms.MultipleChoiceField(
        required=False,
        choices=INFRAESTRUCTURA_ACCESIBILIDAD_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    articulaciones_institucionales = forms.MultipleChoiceField(
        required=False,
        choices=ARTICULACIONES_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Dispositivo
        fields = [
            "nombre_institucion",
            "tipo_gestion",
            "tipo_gestion_otra",
            "razon_social",
            "cuit_institucion",
            "provincia",
            "municipio",
            "domicilio_institucion",
            "telefono_contacto",
            "correo_electronico",
            "responsable_nombre_completo",
            "responsable_dni",
            "tipo_dispositivo",
            "tipo_dispositivo_otro",
            "modalidad_funcionamiento",
            "dias_atencion",
            "horarios_funcionamiento",
            "capacidad_total_plazas",
            "poblacion_destinataria",
            "poblacion_destinataria_otro",
            "franja_etaria_destinataria",
            "tiempo_permanencia_promedio",
            "tiempo_permanencia_otro",
            "modalidad_ingreso",
            "modalidad_ingreso_otro",
            "documentacion_ingreso",
            "documentacion_ingreso_otro",
            "requisitos_ingreso",
            "requisitos_ingreso_otro",
            "servicios_brindados",
            "servicios_brindados_otro",
            "ofrece_actividades_formativas",
            "tipos_actividades_formativas",
            "tipos_actividades_formativas_otro",
            "actividades_certificacion_oficial",
            "registra_informacion_personas",
            "modo_registro",
            "modo_registro_otro",
            "tipo_informacion_registrada",
            "tipo_informacion_registrada_otro",
            "infraestructura_disponible",
            "infraestructura_disponible_otro",
            "infraestructura_accesibilidad",
            "infraestructura_accesibilidad_otro",
            "principales_limitaciones",
            "necesidades_prioritarias",
            "articulaciones_institucionales",
            "articulaciones_institucionales_otro",
            "observaciones_adicionales",
            "documentacion_dispositivo",
            "documentacion_dispositivo_adicional_1",
            "documentacion_dispositivo_adicional_2",
            "documentacion_dispositivo_adicional_3",
            "documentacion_dispositivo_adicional_4",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._configure_geography_fields()
        self.fields["documentacion_dispositivo"].label = "Documentación del dispositivo"
        self.fields["documentacion_dispositivo_adicional_1"].label = (
            "Documentación adicional 1"
        )
        self.fields["documentacion_dispositivo_adicional_2"].label = (
            "Documentación adicional 2"
        )
        self.fields["documentacion_dispositivo_adicional_3"].label = (
            "Documentación adicional 3"
        )
        self.fields["documentacion_dispositivo_adicional_4"].label = (
            "Documentación adicional 4"
        )
        for field_name in DOCUMENTACION_UPLOAD_FIELDS:
            self.fields[field_name].widget.attrs["accept"] = DOCUMENTACION_ACCEPT_ATTR
            self.fields[field_name].help_text = "PDF, JPG o PNG. Máximo 10 MB."
        self._apply_widgets()

    def _apply_widgets(self):
        for field_name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs["class"] = (
                    f'{widget.attrs.get("class", "")} form-select'.strip()
                )
            elif isinstance(widget, forms.CheckboxSelectMultiple):
                widget.attrs["class"] = "list-unstyled mb-0"
            else:
                widget.attrs["class"] = (
                    f'{widget.attrs.get("class", "")} form-control'.strip()
                )

    def _configure_geography_fields(self):
        def parse_pk(value):
            return int(value) if value and str(value).isdigit() else None

        provincia = Provincia.objects.filter(
            pk=parse_pk(self.data.get(self.add_prefix("provincia")))
        ).first() or getattr(self.instance, "provincia", None)

        self.fields["provincia"].queryset = Provincia.objects.all().order_by("nombre")
        if provincia:
            self.fields["provincia"].initial = provincia
            self.fields["municipio"].queryset = Municipio.objects.filter(
                provincia=provincia
            ).order_by("nombre")
        else:
            self.fields["municipio"].queryset = Municipio.objects.none()

        municipio = Municipio.objects.filter(
            pk=parse_pk(self.data.get(self.add_prefix("municipio")))
        ).first() or getattr(self.instance, "municipio", None)

        if municipio:
            self.fields["municipio"].initial = municipio

    def clean_cuit_institucion(self):
        cuit = "".join(
            ch
            for ch in (self.cleaned_data.get("cuit_institucion") or "")
            if ch.isdigit()
        )
        if len(cuit) != 11:
            raise ValidationError("Ingrese un CUIT válido de 11 dígitos.")
        return cuit

    def clean_responsable_dni(self):
        dni = "".join(
            ch
            for ch in (self.cleaned_data.get("responsable_dni") or "")
            if ch.isdigit()
        )
        if len(dni) not in (7, 8):
            raise ValidationError("Ingrese un DNI válido (solo números).")
        return dni

    def _validate_otro_required(self, list_field, other_field, cleaned_data):
        selected = cleaned_data.get(list_field) or []
        if "otro" in selected and not (cleaned_data.get(other_field) or "").strip():
            self.add_error(
                other_field, "Este campo es obligatorio cuando selecciona 'Otro'."
            )

    def clean(self):
        cleaned_data = super().clean()
        self._validate_otro_required(
            "poblacion_destinataria",
            "poblacion_destinataria_otro",
            cleaned_data,
        )
        self._validate_otro_required(
            "modalidad_ingreso",
            "modalidad_ingreso_otro",
            cleaned_data,
        )
        self._validate_otro_required(
            "documentacion_ingreso",
            "documentacion_ingreso_otro",
            cleaned_data,
        )
        self._validate_otro_required(
            "requisitos_ingreso",
            "requisitos_ingreso_otro",
            cleaned_data,
        )
        self._validate_otro_required(
            "servicios_brindados",
            "servicios_brindados_otro",
            cleaned_data,
        )
        self._validate_otro_required(
            "tipos_actividades_formativas",
            "tipos_actividades_formativas_otro",
            cleaned_data,
        )
        self._validate_otro_required(
            "tipo_informacion_registrada",
            "tipo_informacion_registrada_otro",
            cleaned_data,
        )
        self._validate_otro_required(
            "infraestructura_disponible",
            "infraestructura_disponible_otro",
            cleaned_data,
        )
        self._validate_otro_required(
            "infraestructura_accesibilidad",
            "infraestructura_accesibilidad_otro",
            cleaned_data,
        )
        self._validate_otro_required(
            "articulaciones_institucionales",
            "articulaciones_institucionales_otro",
            cleaned_data,
        )

        if (
            cleaned_data.get("tipo_gestion") == Dispositivo.TipoGestion.OTRA
            and not (cleaned_data.get("tipo_gestion_otra") or "").strip()
        ):
            self.add_error(
                "tipo_gestion_otra",
                "Este campo es obligatorio cuando el tipo de gestión es 'Otra'.",
            )

        if (
            cleaned_data.get("tipo_dispositivo") == Dispositivo.TipoDispositivo.OTRO
            and not (cleaned_data.get("tipo_dispositivo_otro") or "").strip()
        ):
            self.add_error(
                "tipo_dispositivo_otro",
                "Este campo es obligatorio cuando el tipo de dispositivo es 'Otro'.",
            )

        if (
            cleaned_data.get("tiempo_permanencia_promedio")
            == Dispositivo.TiempoPermanenciaPromedio.OTRO
            and not (cleaned_data.get("tiempo_permanencia_otro") or "").strip()
        ):
            self.add_error(
                "tiempo_permanencia_otro",
                "Este campo es obligatorio cuando el tiempo de permanencia es 'Otro'.",
            )

        if (
            cleaned_data.get("modo_registro") == Dispositivo.ModoRegistro.OTRO
            and not (cleaned_data.get("modo_registro_otro") or "").strip()
        ):
            self.add_error(
                "modo_registro_otro",
                "Complete el detalle cuando el modo de registro es 'Otro'.",
            )

        return cleaned_data
