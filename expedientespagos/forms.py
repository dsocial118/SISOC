from decimal import Decimal

from django import forms
from expedientespagos.models import ExpedientePago


class ExpedientePagoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self._es_area_legales = kwargs.pop("es_area_legales", None)
        self._es_tecnico_comedor = kwargs.pop("es_tecnico_comedor", None)
        super().__init__(*args, **kwargs)
        self._configure_required_fields()

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
        exclude = ["comedor"]
        widgets = {
            "usuario": forms.Select(attrs={"class": "form-control"}),
            "fecha_pago_al_banco": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "fecha_acreditacion": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }
        labels = {
            "nombre": "Nombre del Expediente",
            "usuario": "Usuario Responsable",
            "estado": "Estado del Expediente",
        }
