from datetime import time
from pathlib import Path

from django import forms

from core.models import Provincia
from ver_para_ser_libre.models import (
    CasoLaboratorioVPSL,
    ChecklistJornadaVPSL,
    CierreDiarioVPSL,
    EstadoEvaluacionVPSL,
    EstadoItinerario,
    EstadoLaboratorio,
    EvaluacionSedeItinerarioVPSL,
    ItinerarioVPSL,
    JornadaVPSL,
    RegistroNominalVPSL,
    ResultadoAtencion,
    SedeVPSL,
)
from ver_para_ser_libre.services import workflow


class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.setdefault("class", "form-control")
            else:
                field.widget.attrs.setdefault("class", "form-control")


class VPSLClearableFileInput(forms.ClearableFileInput):
    template_name = "ver_para_ser_libre/widgets/clearable_file_input.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if value:
            context["widget"]["file_name"] = Path(
                getattr(value, "name", str(value))
            ).name
        return context


class ItinerarioVPSLForm(BootstrapModelForm):
    localidad_filtro = forms.ChoiceField(
        required=False,
        label="Localidad",
        choices=(("", "Todas"),),
    )
    sedes = forms.ModelMultipleChoiceField(
        queryset=SedeVPSL.objects.none(),
        required=True,
        label="Sedes tentativas *",
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-control select2-sedes-vpsl",
                "data-placeholder": "Buscar por nombre, cueanexo o domicilio",
            }
        ),
    )

    class Meta:
        model = ItinerarioVPSL
        fields = [
            "provincia",
            "fecha_inicio",
            "fecha_fin",
            "localidad_filtro",
            "sedes",
            "referente_nombre",
            "referente_apellido",
            "referente_telefono",
            "referente_email",
            "carta_archivo",
            "observaciones",
        ]
        widgets = {
            "fecha_inicio": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"},
            ),
            "fecha_fin": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"},
            ),
            "observaciones": forms.Textarea(attrs={"rows": 3}),
            "carta_archivo": VPSLClearableFileInput(),
        }

    def __init__(self, *args, **kwargs):
        self.freeze_completed_fields = kwargs.pop("freeze_completed_fields", False)
        self.provincia_bloqueada = kwargs.pop("provincia_bloqueada", None)
        self.subsanacion_only = kwargs.pop("subsanacion_only", False)
        self.subsanacion_sede_fields = []
        self.subsanacion_carta_archivo = False
        super().__init__(*args, **kwargs)
        selected_ids = []
        if self.instance and self.instance.pk:
            selected_ids = list(self.instance.sedes.values_list("pk", flat=True))
        raw_ids = self.data.getlist("sedes") if self.is_bound else selected_ids
        self.fields["sedes"].queryset = SedeVPSL.objects.filter(pk__in=raw_ids)
        self.fields["carta_archivo"].required = not bool(
            self.instance and self.instance.carta_archivo
        )
        self.fields["carta_archivo"].help_text = "Adjunte la carta obligatoria."
        self.fields["referente_nombre"].label = "Nombre referente"
        self.fields["referente_apellido"].label = "Apellido referente"
        self.fields["referente_telefono"].label = "Telefono referente"
        self.fields["referente_email"].label = "Email referente"
        self._set_localidad_choices()
        if self.provincia_bloqueada:
            self.fields["provincia"].initial = self.provincia_bloqueada.pk
            self.fields["provincia"].disabled = True
            css_class = self.fields["provincia"].widget.attrs.get("class", "")
            self.fields["provincia"].widget.attrs[
                "class"
            ] = f"{css_class} bg-dark text-white".strip()
            self.fields["provincia"].help_text = (
                "Provincia asignada al usuario provincial."
            )
        if self.freeze_completed_fields:
            self._freeze_completed_fields()
        if self.subsanacion_only:
            self._configure_subsanacion_fields()

    def _set_localidad_choices(self):
        provincia = self.provincia_bloqueada
        if not provincia and self.instance and self.instance.provincia_id:
            provincia = self.instance.provincia
        if not provincia and self.is_bound:
            provincia_id = self.data.get("provincia")
            try:
                provincia = Provincia.objects.filter(pk=provincia_id).first()
            except (TypeError, ValueError):
                provincia = None
        sedes = SedeVPSL.objects.all()
        if provincia:
            sedes = sedes.filter(jurisdiccion__icontains=provincia.nombre)
        localidades = (
            sedes.exclude(localidad="")
            .order_by("localidad")
            .values_list("localidad", flat=True)
            .distinct()
        )
        self.fields["localidad_filtro"].choices = [
            ("", "Todas"),
            *[(localidad, localidad) for localidad in localidades],
        ]

    def _freeze_completed_fields(self):
        for field_name in self.fields:
            current_value = getattr(self.instance, field_name, None)
            has_value = bool(current_value)
            if field_name == "sedes":
                has_value = self.instance.sedes.exists()
            if field_name == "carta_archivo":
                has_value = bool(self.instance.carta_archivo)
            if has_value:
                self.fields[field_name].disabled = True
                css_class = self.fields[field_name].widget.attrs.get("class", "")
                self.fields[field_name].widget.attrs[
                    "class"
                ] = f"{css_class} bg-dark text-white".strip()
                self.fields[field_name].help_text = (
                    "Este campo ya estaba completo al aprobarse y no puede modificarse."
                )

    def _configure_subsanacion_fields(self):
        allowed_fields = []
        if self.instance.carta_archivo_estado == EstadoEvaluacionVPSL.SUBSANAR:
            allowed_fields.append("carta_archivo")
            self.subsanacion_carta_archivo = True
            self.fields["carta_archivo"].required = True
            self.fields["carta_archivo"].label = "Nueva carta archivo *"
            self.fields["carta_archivo"].help_text = (
                "Adjunte el archivo corregido solicitado por Nacion."
            )

        for field_name in list(self.fields):
            if field_name not in allowed_fields:
                self.fields.pop(field_name)

        evaluaciones = self.instance.evaluaciones_sedes.select_related("sede").filter(
            estado=EstadoEvaluacionVPSL.SUBSANAR
        )
        for evaluacion in evaluaciones:
            field_name = f"subsanar_sede_{evaluacion.pk}"
            queryset = SedeVPSL.objects.all()
            if self.instance.provincia_id:
                queryset = queryset.filter(
                    jurisdiccion__icontains=self.instance.provincia.nombre
                )
            sedes_actuales = self.instance.sedes.exclude(
                pk=evaluacion.sede_id
            ).values_list("pk", flat=True)
            queryset = queryset.exclude(pk__in=sedes_actuales)
            self.fields[field_name] = forms.ModelChoiceField(
                queryset=queryset.order_by("localidad", "nombre"),
                required=True,
                label=f"Reemplazar sede: {evaluacion.sede.nombre}",
                initial=evaluacion.sede_id,
                help_text=(
                    evaluacion.observacion
                    or "Seleccione la sede corregida para reevaluacion de Nacion."
                ),
                widget=forms.Select(
                    attrs={
                        "class": "form-control select2-sede-subsanacion-vpsl",
                        "data-placeholder": "Buscar sede por nombre, CUE o domicilio",
                        "data-provincia": self.instance.provincia_id or "",
                        "data-current-sede": evaluacion.sede_id,
                    }
                ),
            )
            self.subsanacion_sede_fields.append((field_name, evaluacion))

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit and self.subsanacion_only:
            if self.subsanacion_carta_archivo:
                instance.carta_archivo_estado = EstadoEvaluacionVPSL.PENDIENTE
                instance.save(update_fields=["carta_archivo_estado"])
            for field_name, evaluacion in self.subsanacion_sede_fields:
                nueva_sede = self.cleaned_data.get(field_name)
                if not nueva_sede:
                    continue
                sede_anterior = evaluacion.sede
                if nueva_sede.pk != sede_anterior.pk:
                    instance.sedes.remove(sede_anterior)
                    instance.sedes.add(nueva_sede)
                    evaluacion.delete()
                    evaluacion, _ = EvaluacionSedeItinerarioVPSL.objects.get_or_create(
                        itinerario=instance,
                        sede=nueva_sede,
                    )
                evaluacion.estado = EstadoEvaluacionVPSL.PENDIENTE
                evaluacion.observacion = ""
                evaluacion.save(update_fields=["estado", "observacion", "updated_at"])
        return instance

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")
        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            self.add_error(
                "fecha_fin", "La fecha de fin no puede ser anterior al inicio."
            )
        if self.instance and self.instance.estado == EstadoItinerario.APROBADO:
            return cleaned_data
        if not cleaned_data.get("carta_archivo") and not (
            self.instance and self.instance.carta_archivo
        ):
            self.add_error("carta_archivo", "Debe adjuntar Carta archivo.")
        return cleaned_data


class JornadaVPSLForm(BootstrapModelForm):
    SEXO_CHOICES = (
        ("", "Seleccionar"),
        ("M", "Masculino"),
        ("F", "Femenino"),
        ("X", "X"),
    )

    class Meta:
        model = JornadaVPSL
        fields = [
            "fecha",
            "sede_vpsl",
            "vehiculo",
            "horario_inicio",
            "horario_fin",
            "referente_dni",
            "referente_sexo",
            "referente_telefono",
            "referente_email",
            "observaciones",
        ]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "horario_inicio": forms.TimeInput(attrs={"type": "time"}),
            "horario_fin": forms.TimeInput(attrs={"type": "time"}),
            "observaciones": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        self.itinerario = kwargs.pop("itinerario", None)
        super().__init__(*args, **kwargs)
        if self.itinerario:
            self.fields["sede_vpsl"].queryset = workflow.sedes_aprobadas_itinerario(
                self.itinerario
            )
            self.fields["fecha"].widget.attrs.update(
                {
                    "min": self.itinerario.fecha_inicio.isoformat(),
                    "max": self.itinerario.fecha_fin.isoformat(),
                }
            )
        self.fields["sede_vpsl"].label = "Sede *"
        self.fields["sede_vpsl"].required = True
        self.fields["vehiculo"].label = "Vehiculo"
        self.fields["vehiculo"].widget.attrs.update({"class": "form-control"})
        self.fields["referente_dni"].label = "DNI referente"
        self.fields["referente_sexo"].label = "Sexo referente"
        self.fields["referente_sexo"].widget = forms.Select(
            choices=self.SEXO_CHOICES,
            attrs={"class": "form-control"},
        )
        if not self.is_bound and not self.instance.pk:
            self.fields["horario_inicio"].initial = time(9, 0)
            self.fields["horario_fin"].initial = time(18, 0)


class ChecklistSedeVPSLForm(forms.Form):
    ITEMS = (
        (
            ChecklistJornadaVPSL.Item.ELECTRICIDAD,
            "Electricidad e infraestructura",
        ),
        (ChecklistJornadaVPSL.Item.VIANDAS, "Provision de viandas"),
        (
            ChecklistJornadaVPSL.Item.SEGURIDAD,
            "Seguridad y resguardo del movil",
        ),
    )

    def __init__(self, *args, sede=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.sede = sede
        existing = {
            item.item: item
            for item in (
                sede.checklist.all() if sede else ChecklistJornadaVPSL.objects.none()
            )
        }
        for item_code, label in self.ITEMS:
            checklist = existing.get(item_code)
            prefix = item_code
            self.fields[f"{prefix}_cumple"] = forms.TypedChoiceField(
                label=f"{label} *",
                choices=(("", "Seleccionar"), ("true", "Si"), ("false", "No")),
                coerce=lambda value: value == "true",
                required=True,
                widget=forms.Select(attrs={"class": "form-control"}),
                initial=(
                    None
                    if checklist is None or checklist.cumple is None
                    else str(checklist.cumple).lower()
                ),
            )
            self.fields[f"{prefix}_observacion"] = forms.CharField(
                label="Observacion",
                required=False,
                widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
                initial=getattr(checklist, "observacion", ""),
            )
            self.fields[f"{prefix}_evidencia"] = forms.FileField(
                label="Evidencia",
                required=False,
                widget=forms.FileInput(attrs={"class": "form-control"}),
            )
        self.field_groups = [
            {
                "title": label,
                "cumple": self[f"{item_code}_cumple"],
                "observacion": self[f"{item_code}_observacion"],
                "evidencia": self[f"{item_code}_evidencia"],
            }
            for item_code, label in self.ITEMS
        ]


class RegistroNominalVPSLForm(BootstrapModelForm):
    SEXO_CHOICES = (
        ("", "Seleccionar"),
        ("M", "Masculino"),
        ("F", "Femenino"),
        ("X", "X"),
    )
    DIAGNOSTICO_CHOICES = (
        ("", "Seleccionar"),
        ("diagnostico 1", "diagnostico 1"),
        ("diagnostico 2", "diagnostico 2"),
        ("diagnostico 3", "Diagnostico 3"),
    )
    prescripcion = forms.ChoiceField(
        choices=DIAGNOSTICO_CHOICES,
        required=False,
        label="Prescripcion",
    )

    @staticmethod
    def siguiente_numero_acta(jornada):
        registros = list(jornada.registros.order_by("created_at", "pk"))
        siguiente = len(registros) + 1
        if not registros:
            return "-1"
        acta_base = registros[0].numero_acta or ""
        base, separador, sufijo = acta_base.rpartition("-")
        if separador and sufijo.isdigit():
            acta_base = base
        return f"{acta_base}-{siguiente}" if acta_base else f"-{siguiente}"

    class Meta:
        model = RegistroNominalVPSL
        fields = [
            "dni",
            "sexo",
            "identificador_alternativo",
            "nombre",
            "apellido",
            "edad",
            "genero",
            "telefono",
            "escuela_sede",
            "numero_acta",
            "numero_sobre",
            "fecha_atencion",
            "prescripcion",
            "resultado",
            "cantidad_lentes",
            "adjunto",
            "primera_vez_anteojos",
            "observaciones",
        ]
        widgets = {
            "fecha_atencion": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"},
            ),
            "observaciones": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, jornada=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.jornada = jornada
        self.fields["sexo"].widget = forms.Select(
            choices=self.SEXO_CHOICES,
            attrs={"class": "form-control"},
        )
        self.fields["sexo"].label = "Sexo"
        self.fields["genero"].label = "Sexo"
        self.fields["primera_vez_anteojos"].label = "Primera vez que utiliza anteojos"
        self.fields["cantidad_lentes"].widget.attrs.update({"min": "0", "max": "2"})
        for field_name in ("nombre", "apellido", "edad", "genero"):
            attrs = self.fields[field_name].widget.attrs
            attrs["readonly"] = "readonly"
            attrs["title"] = (
                "Este campo se completa automaticamente al verificar RENAPER."
            )
            css_class = attrs.get("class", "")
            attrs["class"] = f"{css_class} bg-dark text-white".strip()
        if jornada and not self.is_bound and not self.instance.pk:
            self.fields["fecha_atencion"].initial = jornada.fecha
            self.fields["escuela_sede"].initial = jornada.sede
            numero_acta = self.siguiente_numero_acta(jornada)
            self.initial["numero_acta"] = numero_acta
            self.fields["numero_acta"].initial = numero_acta

    def clean(self):
        cleaned_data = super().clean()
        resultado = cleaned_data.get("resultado")
        cantidad_lentes = cleaned_data.get("cantidad_lentes") or 0
        if resultado == ResultadoAtencion.NO_REQUIERE:
            cleaned_data["cantidad_lentes"] = 0
        elif cantidad_lentes > 2:
            self.add_error("cantidad_lentes", "La cantidad maxima de lentes es 2.")
        return cleaned_data


class SedeVPSLForm(BootstrapModelForm):
    class Meta:
        model = SedeVPSL
        fields = [
            "jurisdiccion",
            "sector",
            "ambito",
            "departamento",
            "codigo_departamento",
            "localidad",
            "codigo_localidad",
            "cueanexo",
            "nombre",
            "domicilio",
            "codigo_postal",
            "telefono",
            "mail",
            "latitud",
            "longitud",
        ]


class CasoLaboratorioVPSLForm(BootstrapModelForm):
    fecha = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    responsable = forms.CharField(required=True, max_length=255)

    class Meta:
        model = CasoLaboratorioVPSL
        fields = ["estado", "fecha", "responsable"]

    def __init__(self, *args, next_state=None, **kwargs):
        super().__init__(*args, **kwargs)
        if next_state:
            self.fields["estado"].initial = next_state
            self.fields["estado"].disabled = True
        self.fields["estado"].choices = EstadoLaboratorio.choices


class CierreDiarioVPSLForm(BootstrapModelForm):
    class Meta:
        model = CierreDiarioVPSL
        fields = [
            "cantidad_atenciones_registradas",
            "cantidad_lentes_entregados_dia",
            "cantidad_casos_laboratorio_reportados",
            "responsable_cierre",
            "acta_adjunta",
            "observaciones",
        ]
        widgets = {"observaciones": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required_labels = {
            "cantidad_atenciones_registradas",
            "cantidad_lentes_entregados_dia",
            "cantidad_casos_laboratorio_reportados",
            "responsable_cierre",
            "acta_adjunta",
        }
        for name in required_labels:
            self.fields[name].required = True
            self.fields[name].label = f"{self.fields[name].label} *"
