from django import forms

from comedores.models import ComedorDatosConvenioPnud


PRESTACIONES_APROBADAS_FIELDS = [
    "aprobadas_desayuno_lunes",
    "aprobadas_almuerzo_lunes",
    "aprobadas_merienda_lunes",
    "aprobadas_cena_lunes",
    "aprobadas_desayuno_martes",
    "aprobadas_almuerzo_martes",
    "aprobadas_merienda_martes",
    "aprobadas_cena_martes",
    "aprobadas_desayuno_miercoles",
    "aprobadas_almuerzo_miercoles",
    "aprobadas_merienda_miercoles",
    "aprobadas_cena_miercoles",
    "aprobadas_desayuno_jueves",
    "aprobadas_almuerzo_jueves",
    "aprobadas_merienda_jueves",
    "aprobadas_cena_jueves",
    "aprobadas_desayuno_viernes",
    "aprobadas_almuerzo_viernes",
    "aprobadas_merienda_viernes",
    "aprobadas_cena_viernes",
    "aprobadas_desayuno_sabado",
    "aprobadas_almuerzo_sabado",
    "aprobadas_merienda_sabado",
    "aprobadas_cena_sabado",
    "aprobadas_desayuno_domingo",
    "aprobadas_almuerzo_domingo",
    "aprobadas_merienda_domingo",
    "aprobadas_cena_domingo",
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
