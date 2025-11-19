import re
from django import forms
from django.core.exceptions import ValidationError
from ciudadanos.models import Ciudadano
from ciudadanos.forms import CiudadanoForm
from comedores.models import (
    Comedor,
    Referente,
    ImagenComedor,
    Nomina,
    EstadoActividad,
    EstadoProceso,
    EstadoDetalle,
)
from comedores.services.estado_manager import registrar_cambio_estado

from core.models import Municipio, Provincia
from core.models import Localidad
from organizaciones.models import Organizacion


class ReferenteForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        comedor_id = kwargs.pop("comedor_pk", None)
        if comedor_id:
            comedor = Comedor.objects.get(pk=comedor_id)
            self.fields["referente_nombre"].initial = comedor.referente.nombre
            self.fields["referente_apellido"].initial = comedor.referente.apellido
            self.fields["referente_mail"].initial = comedor.referente.mail
            self.fields["referente_celular"].initial = comedor.referente.celular
            self.fields["referente_documento"].initial = comedor.referente.documento
            self.fields["referente_funcion"].initial = comedor.referente.funcion

    def clean_mail(self):
        mail = self.cleaned_data.get("mail")
        if not mail:
            return mail
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not isinstance(mail, str):
            raise ValidationError("El correo electrónico debe ser una cadena válida.")
        if not re.match(email_regex, mail):
            raise ValidationError("Por favor, ingresa un correo electrónico válido.")
        return mail

    class Meta:
        model = Referente
        fields = "__all__"


class NominaForm(forms.ModelForm):
    estado = forms.ChoiceField(
        choices=Nomina.ESTADO_CHOICES, widget=forms.Select(attrs={"class": "form-control"})
    )

    class Meta:
        model = Nomina
        fields = ["estado", "observaciones"]
        widgets = {
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class NominaExtraForm(NominaForm):
    pass


class CiudadanoFormParaNomina(forms.ModelForm):
    class Meta:
        model = Ciudadano
        fields = [
            "apellido",
            "nombre",
            "fecha_nacimiento",
            "tipo_documento",
            "documento",
            "sexo",
        ]
        widgets = {
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date"}),
        }


class ComedorForm(forms.ModelForm):
    estado_general = forms.ModelChoiceField(
        label="Estado general",
        queryset=EstadoActividad.objects.none(),
        required=True,
        empty_label="Seleccione un estado general",
    )
    subestado = forms.ModelChoiceField(
        label="Subestado",
        queryset=EstadoProceso.objects.none(),
        required=True,
        empty_label="Seleccione un subestado",
        widget=forms.Select(attrs={"data-placeholder": "Seleccione un subestado"}),
    )
    motivo = forms.ModelChoiceField(
        label="Motivo",
        queryset=EstadoDetalle.objects.none(),
        required=False,
        empty_label="Seleccione un motivo",
        widget=forms.Select(attrs={"data-placeholder": "Seleccione un motivo"}),
    )
    comienzo = forms.IntegerField(min_value=1900, required=False)
    longitud = forms.FloatField(min_value=-180, max_value=180, required=False)
    latitud = forms.FloatField(min_value=-90, max_value=90, required=False)
    codigo_postal = forms.IntegerField(min_value=1000, max_value=999999, required=False)
    codigo_de_proyecto = forms.CharField(max_length=7, required=False)

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.previous_estado_chain = self._resolve_instance_estados()
        self.estado_tree = self._build_estado_tree()
        self._configure_estado_fields()
        self.popular_campos_ubicacion()

        # Ordenar organizaciones alfabéticamente
        self.fields["organizacion"].queryset = Organizacion.objects.all().order_by(
            "nombre"
        )

    def popular_campos_ubicacion(self):

        def pk_formatter(value):
            return int(value) if value and value.isdigit() else None

        provincia = Provincia.objects.filter(
            pk=pk_formatter(self.data.get("provincia"))
        ).first() or getattr(self.instance, "provincia", None)
        municipio = Municipio.objects.filter(
            pk=pk_formatter(self.data.get("municipio"))
        ).first() or getattr(self.instance, "municipio", None)
        localidad = Localidad.objects.filter(
            pk=pk_formatter(self.data.get("localidad"))
        ).first() or getattr(self.instance, "localidad", None)

        if provincia:
            self.fields["provincia"].initial = Provincia.objects.get(id=provincia.id)
            self.fields["provincia"].queryset = Provincia.objects.all()
            self.fields["provincia"].queryset = Provincia.objects.all().order_by(
                "nombre"
            )
            self.fields["municipio"].queryset = Municipio.objects.filter(
                provincia=provincia
            ).order_by("nombre")

        else:
            self.fields["provincia"].queryset = Provincia.objects.all()
            self.fields["provincia"].queryset = Provincia.objects.all().order_by(
                "nombre"
            )
            self.fields["municipio"].queryset = Municipio.objects.none()
            self.fields["localidad"].queryset = Localidad.objects.none()

        if municipio:
            self.fields["municipio"].initial = municipio
            self.fields["localidad"].queryset = Localidad.objects.filter(
                municipio=municipio
            ).order_by("nombre")

        if localidad:
            self.fields["localidad"].initial = localidad

    def _configure_estado_fields(self):
        actividad_prev, proceso_prev, detalle_prev = self.previous_estado_chain
        if not self.is_bound:
            if actividad_prev:
                self.fields["estado_general"].initial = actividad_prev.pk
            if proceso_prev:
                self.fields["subestado"].initial = proceso_prev.pk
            if detalle_prev:
                self.fields["motivo"].initial = detalle_prev.pk
        self.fields["estado_general"].queryset = EstadoActividad.objects.order_by(
            "estado"
        )
        selected_actividad = self._get_selected_actividad()
        if selected_actividad:
            self.fields["subestado"].queryset = EstadoProceso.objects.filter(
                estado_actividad=selected_actividad
            ).order_by("estado")
        else:
            self.fields["subestado"].queryset = EstadoProceso.objects.none()
        selected_proceso = self._get_selected_proceso(selected_actividad)
        if selected_proceso:
            self.fields["motivo"].queryset = EstadoDetalle.objects.filter(
                estado_proceso=selected_proceso
            ).order_by("estado")
        else:
            self.fields["motivo"].queryset = EstadoDetalle.objects.none()

    def _get_bound_value(self, field_name: str):
        if self.is_bound:
            return self.data.get(self.add_prefix(field_name))
        if field_name in self.initial and self.initial[field_name] not in (None, ""):
            return self.initial[field_name]
        return self.fields[field_name].initial

    def _get_selected_actividad(self):
        value = self._get_bound_value("estado_general")
        queryset = (
            self.fields["estado_general"].queryset or EstadoActividad.objects.all()
        )
        if value:
            try:
                return queryset.get(pk=value)
            except (ValueError, EstadoActividad.DoesNotExist):
                return None
        return self.previous_estado_chain[0]

    def _get_selected_proceso(self, actividad=None):
        value = self._get_bound_value("subestado")
        queryset = EstadoProceso.objects.all()
        if actividad:
            queryset = queryset.filter(estado_actividad=actividad)
        if value:
            try:
                return queryset.get(pk=value)
            except (ValueError, EstadoProceso.DoesNotExist):
                return None
        return self.previous_estado_chain[1]

    def _get_selected_detalle(self, proceso=None):
        value = self._get_bound_value("motivo")
        queryset = EstadoDetalle.objects.all()
        if proceso:
            queryset = queryset.filter(estado_proceso=proceso)
        if value:
            try:
                return queryset.get(pk=value)
            except (ValueError, EstadoDetalle.DoesNotExist):
                return None
        return self.previous_estado_chain[2]

    def _resolve_instance_estados(self):
        actividad = proceso = detalle = None
        historial = getattr(self.instance, "ultimo_estado", None)
        if historial and getattr(historial, "estado_general_id", None):
            estado_general = historial.estado_general
            if estado_general:
                actividad = estado_general.estado_actividad
                proceso = estado_general.estado_proceso
                detalle = estado_general.estado_detalle
                return actividad, proceso, detalle
        return actividad, proceso, detalle

    def _build_estado_tree(self):
        tree = {}
        procesos = (
            EstadoProceso.objects.select_related("estado_actividad")
            .prefetch_related("estadodetalle_set")
            .order_by("estado_actividad_id", "id")
        )
        for proceso in procesos:
            actividad_id = str(proceso.estado_actividad_id)
            actividad_entry = tree.setdefault(
                actividad_id,
                {
                    "id": proceso.estado_actividad_id,
                    "label": proceso.estado_actividad.estado,
                    "procesos": [],
                },
            )
            detalles = [
                {"id": detalle.id, "label": detalle.estado}
                for detalle in sorted(
                    proceso.estadodetalle_set.all(), key=lambda detalle: detalle.id
                )
            ]
            actividad_entry["procesos"].append(
                {
                    "id": proceso.id,
                    "label": proceso.estado,
                    "detalles": detalles,
                }
            )
        return tree

    def clean(self):
        cleaned_data = super().clean()
        estado_actividad = cleaned_data.get("estado_general")
        estado_proceso = cleaned_data.get("subestado")
        estado_detalle = cleaned_data.get("motivo")
        if not estado_actividad:
            self.add_error("estado_general", "Seleccione un estado general.")
            return cleaned_data
        if not estado_proceso:
            self.add_error("subestado", "Seleccione un subestado.")
            return cleaned_data
        if estado_proceso.estado_actividad_id != estado_actividad.id:
            self.add_error(
                "subestado",
                "El subestado seleccionado no pertenece al estado general elegido.",
            )
        if estado_detalle:
            if estado_detalle.estado_proceso_id != estado_proceso.id:
                self.add_error(
                    "motivo",
                    "El motivo seleccionado no pertenece al subestado elegido.",
                )
        return cleaned_data

    def save(self, commit=True):
        comedor = super().save(commit=False)
        estado_actividad = self.cleaned_data.get("estado_general")
        estado_proceso = self.cleaned_data.get("subestado")
        estado_detalle = self.cleaned_data.get("motivo")
        if commit:
            comedor.save()
            self.save_m2m()
            self._sync_estado_historial(
                comedor, estado_actividad, estado_proceso, estado_detalle
            )
        return comedor

    def _sync_estado_historial(self, comedor, actividad, proceso, detalle):
        if not actividad or not proceso:
            return
        previous = tuple(obj.id if obj else None for obj in self.previous_estado_chain)
        current = (
            actividad.id if actividad else None,
            proceso.id if proceso else None,
            detalle.id if detalle else None,
        )
        if previous == current:
            return
        registrar_cambio_estado(
            comedor=comedor,
            actividad=actividad,
            proceso=proceso,
            detalle=detalle,
            usuario=self.current_user,
        )

    class Meta:
        model = Comedor
        fields = "__all__"
        labels = {
            "tipocomedor": "Tipo comedor",
        }


class ImagenComedorForm(forms.ModelForm):
    class Meta:
        model = ImagenComedor
        fields = "__all__"
