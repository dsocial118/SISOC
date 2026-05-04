from django import forms

from comedores.models import ComedorDatosConvenioPnud


class ComedorDatosConvenioPnudForm(forms.ModelForm):
    class Meta:
        model = ComedorDatosConvenioPnud
        fields = [
            "monto_total_conveniado",
            "nro_convenio",
            "monto_total_convenio_por_espacio",
            "prestaciones_financiadas_mensuales",
            "personas_conveniadas",
            "cantidad_modulos",
        ]
        labels = {
            "monto_total_conveniado": "Monto total conveniado",
            "nro_convenio": "Nro convenio",
            "monto_total_convenio_por_espacio": "Monto total de convenio por espacio",
            "prestaciones_financiadas_mensuales": "Prestaciones financiadas mensuales",
            "personas_conveniadas": "Personas conveniadas",
            "cantidad_modulos": "Cantidad modulos",
        }
