from django import forms
from .validators import MaxSizeFileValidator
from SIF_CDIF.models import Criterios_IVI
from .models import *


class MILD_PreadmisionesForm(forms.ModelForm):
    class Meta:
        model = MILD_PreAdmision
        fields = "__all__"
        widgets = {
            "emb_no_control_1": forms.CheckboxInput(),
            "emb_adolescente_1": forms.CheckboxInput(),
            "emb_riesgo_1": forms.CheckboxInput(),
            "cesareas_multip_1": forms.CheckboxInput(),
            "partos_multip_1": forms.CheckboxInput(),
            "partos_premat_1": forms.CheckboxInput(),
            "partos_menos18meses_1": forms.CheckboxInput(),
            "leer_1": forms.CheckboxInput(),
            "escribir_1": forms.CheckboxInput(),
            "retomar_estudios_1": forms.CheckboxInput(),
            "aprender_oficio_1": forms.CheckboxInput(),
            "leer_2": forms.CheckboxInput(),
            "escribir_2": forms.CheckboxInput(),
            "retomar_estudios_2": forms.CheckboxInput(),
            "aprender_oficio_2": forms.CheckboxInput(),
            "programa_Pilares_2": forms.CheckboxInput(),
            "leer_3": forms.CheckboxInput(),
            "escribir_3": forms.CheckboxInput(),
            "retomar_estudios_3": forms.CheckboxInput(),
            "aprender_oficio_3": forms.CheckboxInput(),
            "programa_Pilares_3": forms.CheckboxInput(),
            "leer_4": forms.CheckboxInput(),
            "escribir_4": forms.CheckboxInput(),
            "retomar_estudios_4": forms.CheckboxInput(),
            "aprender_oficio_4": forms.CheckboxInput(),
            "programa_Pilares_4": forms.CheckboxInput(),
            "leer_5": forms.CheckboxInput(),
            "escribir_5": forms.CheckboxInput(),
            "retomar_estudios_5": forms.CheckboxInput(),
            "aprender_oficio_5": forms.CheckboxInput(),
            "programa_Pilares_5": forms.CheckboxInput(),
            "fecha_nacimiento": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
            "ultimo_control": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
            "observaciones_salud": forms.Textarea(attrs={"rows": 3}),
            "observaciones_gral": forms.Textarea(attrs={"rows": 3}),
            "busca_embarazo": forms.CheckboxInput(),
            "conoce_metodos_anticon": forms.CheckboxInput(),
            "utilizo_alguno": forms.CheckboxInput(),
            "amigos_cercanos": forms.CheckboxInput(),
            "mismo_domicilio": forms.CheckboxInput(),
            "enf_recu_con_trata": forms.CheckboxInput(),
            "enf_recu_sin_trata": forms.CheckboxInput(),
            "enf_conta_con_trata": forms.CheckboxInput(),
            "enf_conta_sin_trata": forms.CheckboxInput(),
            "enf_mental_con_trata": forms.CheckboxInput(),
            "enf_mental_sin_trata": forms.CheckboxInput(),
            "capa_reducidas": forms.CheckboxInput(),
            "certif_discap": forms.CheckboxInput(),
            "medicamento": forms.CheckboxInput(),
            "bajo_peso": forms.CheckboxInput(),
            "sobrepeso": forms.CheckboxInput(),
            "prematuro": forms.CheckboxInput(),
            "interv_quirurgicas": forms.CheckboxInput(),
            "accidentes_domesticos": forms.CheckboxInput(),
            "colecho": forms.CheckboxInput(),
            "auditiva": forms.CheckboxInput(),
            "respiratoria": forms.CheckboxInput(),
            "visual": forms.CheckboxInput(),
            "traumatologica": forms.CheckboxInput(),
            "emocional": forms.CheckboxInput(),
            "psiquica": forms.CheckboxInput(),
            "digestiva": forms.CheckboxInput(),
            "alergias": forms.CheckboxInput(),
            "vacunas": forms.CheckboxInput(),
            "obra_social": forms.CheckboxInput(),
            "libreta_sanitaria": forms.CheckboxInput(),
        }
        labels = {
            "fk_legajo_1": "",
            "menores_a_cargo_1": "",
            "control_gine_1": "",
            "embarazos_1": "",
            "abortos_esp_1": "",
            "abortos_prov_1": "",
            "hijos_1": "",
            "emb_actualmente_1": "",
            "controles_1": "",
            "emb_actual_1": "",
            "educ_maximo_1": "",
            "educ_estado_1": "",
            "educ_maximo_2": "",
            "educ_estado_2": "",
            "educ_maximo_3": "",
            "educ_estado_3": "",
            "educ_maximo_4": "",
            "educ_estado_4": "",
            "educ_maximo_5": "",
            "educ_estado_5": "",
            "planes_sociales_1": "",
            "trabajo_actual_1": "",
            "ocupacion_1": "",
            "modo_contrat_1": "",
            "fk_legajo_2": "",
            "planes_sociales_2": "",
            "trabajo_actual_2": "",
            "modo_contrat_2": "",
            "ocupacion_2": "",
            "fk_legajo_3": "",
            "fk_legajo_4": "",
            "fk_legajo_5": "",
        }


class criterios_Ingreso(forms.ModelForm):
    class Meta:
        model = Criterios_Ingreso
        fields = "__all__"
        widgets = {}
        labels = {}


class MILD_IndiceIngresoForm(forms.ModelForm):
    class Meta:
        model = MILD_IndiceIngreso
        fields = "__all__"
        widgets = {}
        labels = {}


class MILD_IndiceIngresoHistorialForm(forms.ModelForm):
    class Meta:
        model = MILD_Foto_Ingreso
        fields = "__all__"
        widgets = {}
        labels = {}


class criterios_IVI(forms.ModelForm):
    class Meta:
        model = Criterios_IVI
        fields = "__all__"
        widgets = {}
        labels = {}


class MILD_IndiceIviForm(forms.ModelForm):
    class Meta:
        model = MILD_IndiceIVI
        fields = "__all__"
        widgets = {}
        labels = {}


class MILD_IndiceIviHistorialForm(forms.ModelForm):
    class Meta:
        model = MILD_Foto_IVI
        fields = "__all__"
        widgets = {}
        labels = {}


class MILD_IntervencionesForm(forms.ModelForm):
    class Meta:
        model = MILD_Intervenciones
        fields = "__all__"
        widgets = {
            "detalle": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "responsable": forms.SelectMultiple(
                attrs={"class": "select2 w-100", "multiple": True}
            ),
        }
        labels = {
            "criterio_modificable": "Criterio modificable trabajado",
            "impacto": "Impacto en el criterio",
            "accion": "Acción desarrollada",
            "detalle": "Detalles",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtra las opciones del campo criterio_modificable aquí
        self.fields["criterio_modificable"].queryset = Criterios_IVI.objects.filter(
            modificable="SI"
        )


class MILD_OpcionesResponsablesForm(forms.ModelForm):
    class Meta:
        model = OpcionesResponsables
        fields = "__all__"
        widgets = {}
        labels = {}
