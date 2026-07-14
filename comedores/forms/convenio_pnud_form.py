from django import forms

from comedores.models import ComedorDatosConvenioPnud


PRESTACIONES_APROBADAS_DIAS = (
    "lunes",
    "martes",
    "miercoles",
    "jueves",
    "viernes",
    "sabado",
    "domingo",
)
PRESTACIONES_APROBADAS_COMIDAS = ("desayuno", "almuerzo", "merienda", "cena")
PRESTACIONES_APROBADAS_FIELDS = [
    f"aprobadas_{comida}_{dia}"
    for dia in PRESTACIONES_APROBADAS_DIAS
    for comida in PRESTACIONES_APROBADAS_COMIDAS
]


class ComedorDatosConvenioPnudForm(forms.ModelForm):
    class Meta:
        model = ComedorDatosConvenioPnud
        fields = [
            "monto_total_conveniado",
            "nro_convenio",
            "monto_convenio_prestaciones_alimentarias",
            "monto_convenio_siph",
            "prestaciones_financiadas_mensuales",
            "personas_conveniadas",
            "cantidad_modulos",
        ] + PRESTACIONES_APROBADAS_FIELDS
        labels = {
            "monto_total_conveniado": "Monto total conveniado",
            "nro_convenio": "Nro convenio",
            "monto_convenio_prestaciones_alimentarias": "Monto total de convenio por Espacio - Prestaciones Alimentarias",
            "monto_convenio_siph": "Monto total de convenio por Espacio - Servicio Integral de Promoción Humana",
            "prestaciones_financiadas_mensuales": "Prestaciones financiadas mensuales",
            "personas_conveniadas": "Personas conveniadas",
            "cantidad_modulos": "Cantidad Módulos Mensuales",
        }
        widgets = {
            field_name: forms.NumberInput(
                attrs={"class": "form-control form-control-sm", "min": "0"}
            )
            for field_name in PRESTACIONES_APROBADAS_FIELDS
        }
