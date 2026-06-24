from django import forms

from comedores.models import ComedorDatosConvenioPnud


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
        ]
        labels = {
            "monto_total_conveniado": "Monto total conveniado",
            "nro_convenio": "Nro convenio",
            "monto_convenio_prestaciones_alimentarias": "Monto total de convenio por Espacio - Prestaciones Alimentarias",
            "monto_convenio_siph": "Monto total de convenio por Espacio - Servicio Integral de Promoción Humana",
            "prestaciones_financiadas_mensuales": "Prestaciones financiadas mensuales",
            "personas_conveniadas": "Personas conveniadas",
            "cantidad_modulos": "Cantidad modulos",
        }
