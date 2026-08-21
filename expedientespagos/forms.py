from decimal import Decimal

from django import forms
from admisiones.models.admisiones import Admision
from expedientespagos.models import ExpedientePago


class AdmisionPorExpedienteChoiceField(forms.ModelChoiceField):
    """Identifica las admisiones por su expediente y no por su nombre.

    ``Admision.__str__`` devuelve el nombre, que no sirve para elegir el convenio
    al que corresponde un pago.
    """

    def label_from_instance(self, obj):
        etiqueta = obj.num_expediente or f"Admisión #{obj.id}"
        convenio = getattr(getattr(obj, "acompanamiento", None), "nro_convenio", "")
        if convenio:
            etiqueta = f"{etiqueta} — Conv. {convenio}"
        if not obj.activa:
            etiqueta = f"{etiqueta} (cerrada)"
        return etiqueta


class ExpedientePagoForm(forms.ModelForm):
    admision = AdmisionPorExpedienteChoiceField(
        queryset=Admision.objects.none(),
        required=False,
        label="Admisión",
        help_text=(
            "Si se deja vacío, se intenta resolver automáticamente a partir del "
            "expediente del convenio."
        ),
    )

    def __init__(self, *args, **kwargs):
        self._es_area_legales = kwargs.pop("es_area_legales", None)
        self._es_tecnico_comedor = kwargs.pop("es_tecnico_comedor", None)
        self._comedor = kwargs.pop("comedor", None)
        super().__init__(*args, **kwargs)
        self._configure_required_fields()
        self._configure_admision_field()

    def _configure_admision_field(self):
        """Acota el selector de admisión a las del comedor del expediente.

        El expediente del convenio se cargaba a mano y a ciegas; el selector
        permite elegir de las admisiones reales del comedor. Se deja opcional
        para no bloquear la carga cuando la admisión todavía no está en SISOC.
        """
        campo = self.fields.get("admision")
        if campo is None:
            return

        comedor = self._comedor or getattr(self.instance, "comedor", None)

        if comedor is None:
            campo.queryset = Admision.objects.none()
        else:
            campo.queryset = (
                Admision.objects.filter(comedor=comedor)
                .select_related("acompanamiento")
                .order_by("-id")
            )

        campo.required = False
        campo.empty_label = "Resolver automáticamente por número de expediente"
        campo.widget.attrs.setdefault("class", "form-control")

    def _configure_required_fields(self):
        if self._es_area_legales is False:
            for field in (
                "expediente_pago",
                "expediente_convenio",
                "anexo",
                "if_cantidad_de_prestaciones",
                "if_pagado",
            ):
                if field in self.fields:
                    self.fields[field].required = False

        if self._es_tecnico_comedor is False:
            for field in (
                "total",
                "total_prestaciones",
                "gastos_accesorios",
                "mes_pago",
                "ano",
                "organizacion_creacion",
                "numero_orden_pago",
                "fecha_pago_al_banco",
                "fecha_acreditacion",
                "observaciones",
                "prestaciones_mensuales_desayuno",
                "prestaciones_mensuales_almuerzo",
                "prestaciones_mensuales_merienda",
                "prestaciones_mensuales_cena",
                "monto_mensual_desayuno",
                "monto_mensual_almuerzo",
                "monto_mensual_merienda",
                "monto_mensual_cena",
            ):
                if field in self.fields:
                    self.fields[field].required = False

        if self._es_tecnico_comedor is True:
            for field in (
                "ano",
                "prestaciones_mensuales_desayuno",
                "prestaciones_mensuales_almuerzo",
                "prestaciones_mensuales_merienda",
                "prestaciones_mensuales_cena",
                "monto_mensual_desayuno",
                "monto_mensual_almuerzo",
                "monto_mensual_merienda",
                "monto_mensual_cena",
            ):
                if field in self.fields:
                    self.fields[field].required = True

    def clean(self):
        cleaned_data = super().clean()
        if self._es_area_legales is False:
            expediente_convenio = cleaned_data.get("expediente_convenio")
            if not expediente_convenio:
                cleaned_data["expediente_convenio"] = (
                    cleaned_data.get("expediente_pago") or ""
                )

        if self._es_tecnico_comedor is False:
            for field in (
                "prestaciones_mensuales_desayuno",
                "prestaciones_mensuales_almuerzo",
                "prestaciones_mensuales_merienda",
                "prestaciones_mensuales_cena",
            ):
                if cleaned_data.get(field) in (None, ""):
                    cleaned_data[field] = 0
            for field in (
                "monto_mensual_desayuno",
                "monto_mensual_almuerzo",
                "monto_mensual_merienda",
                "monto_mensual_cena",
            ):
                if cleaned_data.get(field) in (None, ""):
                    cleaned_data[field] = Decimal("0")
        return cleaned_data

    class Meta:
        model = ExpedientePago
        fields = "__all__"
        exclude = ["comedor", "mes_convenio"]
        widgets = {
            "usuario": forms.Select(attrs={"class": "form-control"}),
            "fecha_pago_al_banco": forms.DateInput(
                format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"}
            ),
            "fecha_acreditacion": forms.DateInput(
                format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"}
            ),
        }
        labels = {
            "nombre": "Nombre del Expediente",
            "usuario": "Usuario Responsable",
            "estado": "Estado del Expediente",
        }
