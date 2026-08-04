from django import forms

from comedores.models import ComedorDatosConvenioPnud
from comedores.utils import (
    is_abordaje_comunitario_linea_secos_program,
    is_abordaje_comunitario_linea_tradicional_program,
)


PRESTACIONES_APROBADAS_DIAS = (
    "lunes",
    "martes",
    "miercoles",
    "jueves",
    "viernes",
    "sabado",
    "domingo",
)
PRESTACIONES_APROBADAS_COMIDAS = (
    "desayuno",
    "almuerzo",
    "merienda",
    "merienda_reforzada",
    "cena",
)
PRESTACIONES_APROBADAS_FIELDS = [
    f"aprobadas_{comida}_{dia}"
    for dia in PRESTACIONES_APROBADAS_DIAS
    for comida in PRESTACIONES_APROBADAS_COMIDAS
]


class ComedorDatosConvenioPnudForm(forms.ModelForm):
    PRESTACIONES_DIARIAS_FIELDS = [
        "prestaciones_financiadas_diarias_desayuno",
        "prestaciones_financiadas_diarias_almuerzo",
        "prestaciones_financiadas_diarias_merienda",
        "prestaciones_financiadas_diarias_merienda_reforzada",
        "prestaciones_financiadas_diarias_cena",
    ]

    def __init__(self, *args, comedor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if is_abordaje_comunitario_linea_secos_program(comedor):
            for field_name in [
                "prestaciones_financiadas_mensuales",
                *PRESTACIONES_APROBADAS_FIELDS,
                *self.PRESTACIONES_DIARIAS_FIELDS,
            ]:
                self.fields.pop(field_name, None)
        elif is_abordaje_comunitario_linea_tradicional_program(comedor):
            self.fields.pop("prestaciones_financiadas_mensuales", None)
            self.fields.pop("cantidad_modulos", None)
        else:
            for field_name in [
                *self.PRESTACIONES_DIARIAS_FIELDS,
                *[
                    name
                    for name in PRESTACIONES_APROBADAS_FIELDS
                    if "merienda_reforzada" in name
                ],
            ]:
                self.fields.pop(field_name, None)

    class Meta:
        model = ComedorDatosConvenioPnud
        fields = [
            "monto_total_conveniado",
            "nro_convenio",
            "monto_convenio_prestaciones_alimentarias",
            "monto_convenio_siph",
            "prestaciones_financiadas_mensuales",
            "prestaciones_financiadas_diarias_desayuno",
            "prestaciones_financiadas_diarias_almuerzo",
            "prestaciones_financiadas_diarias_merienda",
            "prestaciones_financiadas_diarias_merienda_reforzada",
            "prestaciones_financiadas_diarias_cena",
            "personas_conveniadas",
            "cantidad_modulos",
        ] + PRESTACIONES_APROBADAS_FIELDS
        labels = {
            "monto_total_conveniado": "Monto total conveniado",
            "nro_convenio": "Nro convenio",
            "monto_convenio_prestaciones_alimentarias": "Monto total de convenio por Espacio - Prestaciones Alimentarias",
            "monto_convenio_siph": "Monto total de convenio por Espacio - Servicio Integral de Promoción Humana",
            "prestaciones_financiadas_mensuales": "Prestaciones financiadas mensuales",
            "prestaciones_financiadas_diarias_desayuno": "Prestaciones Financiadas Diarias - Desayuno",
            "prestaciones_financiadas_diarias_almuerzo": "Prestaciones Financiadas Diarias - Almuerzo",
            "prestaciones_financiadas_diarias_merienda": "Prestaciones Financiadas Diarias - Merienda",
            "prestaciones_financiadas_diarias_merienda_reforzada": "Prestaciones Financiadas Diarias - Merienda Reforzada",
            "prestaciones_financiadas_diarias_cena": "Prestaciones Financiadas Diarias - Cena",
            "personas_conveniadas": "Personas conveniadas",
            "cantidad_modulos": "Cantidad Módulos Mensuales",
        }
        widgets = {
            field_name: forms.NumberInput(
                attrs={"class": "form-control form-control-sm", "min": "0"}
            )
            for field_name in PRESTACIONES_APROBADAS_FIELDS
        }
