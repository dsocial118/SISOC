from typing import Any
from django import forms
from django.utils import timezone
from django.forms import inlineformset_factory

from comedores.models import (
    Comedor,
    Relevamiento,
    FuncionamientoPrestacion,
    Espacio,
    EspacioCocina,
    EspacioPrestacion,
    Colaboradores,
    FuenteRecursos,
    FuenteCompras,
    Prestacion,
)

BOOLEAN_CHOICE = [
    (False, "No"),
    (True, "Si"),
]


class FuncionamientoPrestacionForm(forms.ModelForm):
    servicio_por_turnos = forms.ChoiceField(choices=BOOLEAN_CHOICE, widget=forms.Select)

    class Meta:
        model = FuncionamientoPrestacion
        fields = "__all__"


class EspacioCocinaForm(forms.ModelForm):
    espacio_elaboracion_alimentos = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Cuenta con un espacio específico para elaboración de alimentos?",
    )
    almacenamiento_alimentos_secos = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Cuenta con un lugar para el almacenamiento de los alimentos secos que compra/recibe?",
    )
    refrigerador = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Cuenta con heladera o freezer?",
    )
    recipiente_residuos_organicos = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Cuenta con recipientes destinados a la disposición de residuos orgánicos y asimilables?",
    )
    recipiente_residuos_reciclables = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Cuenta con un recipientes destinados a la disposición de residuos reciclables?",
    )
    recipiente_otros_reciduos = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Generan otro tipo de residuos? ¿Cuenta con recipientes destinados a la disposición de dichos residuos?",
    )
    instalacion_electrica = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Cuenta con instalación eléctrica?",
    )

    class Meta:
        model = EspacioCocina
        fields = "__all__"


class EspacioPrestacionForm(forms.ModelForm):
    espacio_equipado = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Cuenta con espacio y equipamiento (mesas, bancos o sillas)?",
    )
    tiene_ventilacion = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿El espacio donde tiene actividad el comedor cuenta con un sistema de ventilación adecuado?",
    )
    tiene_salida_emergencia = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿El espacio donde tiene actividad el comedor cuenta con salidas de emergencia?",
    )
    salida_emergencia_senializada = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Están señalizadas las salidas de emergencia?",
    )
    tiene_equipacion_incendio = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿El lugar cuenta con elementos para apagar incendios (matafuegos / manguera)?",
    )
    tiene_botiquin = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿El lugar cuenta con un botiquín de primeros auxilios?",
    )
    tiene_buena_iluminacion = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿El espacio donde tiene actividad el comedor cuenta con buena iluminación?",
    )
    tiene_sanitarios = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿El lugar cuenta con baño para las personas que realizan tareas en el comedor y para los destinatarios?",
    )
    tiene_buzon_quejas = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿El comedor cuenta con un buzón de quejas y reclamos en el lugar?",
    )
    tiene_gestion_quejas = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Hay en el lugar cartelería con información sobre los mecanismos de gestión de quejas, reclamos y sugerencias del comedor?",
    )

    class Meta:
        model = EspacioPrestacion
        fields = "__all__"


class EspacioForm(forms.ModelForm):
    class Meta:
        model = Espacio
        fields = "__all__"


class ColaboradoresForm(forms.ModelForm):
    colaboradores_capacitados_alimentos = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Cuentan con personas que realizan tareas capacitadas para la manipulación de alimentos?",
    )
    colaboradores_recibieron_capacitacion_alimentos = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Los colaboradores recibieron capacitación sobre manipulación segura de alimentos?",
    )
    colaboradores_capacitados_salud_seguridad = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Los colaboradores recibieron capacitación sobre salud y seguridad ocupacional?",
    )
    colaboradores_recibieron_capacitacion_emergencias = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Los colaboradores recibieron capacitación sobre preparación y respuesta a las emergencias?",
    )
    colaboradores_recibieron_capacitacion_violencia = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label=(
            "¿Los colaboradores recibieron capacitación sobre prevención de violencia de género "
            "incluyendo acoso sexual, explotación sexual y abuso infantil?"
        ),
    )

    class Meta:
        model = Colaboradores
        fields = "__all__"


class FuenteRecursosForm(forms.ModelForm):
    recibe_donaciones_particulares = forms.ChoiceField(
        choices=BOOLEAN_CHOICE, widget=forms.Select
    )
    recibe_estado_nacional = forms.ChoiceField(
        choices=BOOLEAN_CHOICE, widget=forms.Select
    )
    recibe_estado_provincial = forms.ChoiceField(
        choices=BOOLEAN_CHOICE, widget=forms.Select
    )
    recibe_estado_municipal = forms.ChoiceField(
        choices=BOOLEAN_CHOICE, widget=forms.Select
    )
    recibe_otros = forms.ChoiceField(choices=BOOLEAN_CHOICE, widget=forms.Select)

    class Meta:
        model = FuenteRecursos
        fields = "__all__"


class FuenteComprasForm(forms.ModelForm):
    almacen_cercano = forms.ChoiceField(choices=BOOLEAN_CHOICE, widget=forms.Select)
    verduleria = forms.ChoiceField(choices=BOOLEAN_CHOICE, widget=forms.Select)
    granja = forms.ChoiceField(choices=BOOLEAN_CHOICE, widget=forms.Select)
    carniceria = forms.ChoiceField(choices=BOOLEAN_CHOICE, widget=forms.Select)
    pescaderia = forms.ChoiceField(choices=BOOLEAN_CHOICE, widget=forms.Select)
    supermercado = forms.ChoiceField(choices=BOOLEAN_CHOICE, widget=forms.Select)
    mercado_central = forms.ChoiceField(choices=BOOLEAN_CHOICE, widget=forms.Select)
    ferias_comunales = forms.ChoiceField(choices=BOOLEAN_CHOICE, widget=forms.Select)
    mayoristas = forms.ChoiceField(choices=BOOLEAN_CHOICE, widget=forms.Select)
    otro = forms.ChoiceField(choices=BOOLEAN_CHOICE, widget=forms.Select)

    class Meta:
        model = FuenteCompras
        fields = "__all__"


class PrestacionForm(forms.ModelForm):

    class Meta:
        model = Prestacion
        fields = "__all__"


PrestacionFormSet = inlineformset_factory(
    Relevamiento, Prestacion, form=PrestacionForm, extra=1, can_delete=False
)


class RelevamientoForm(forms.ModelForm):
    comedor = forms.ModelChoiceField(
        queryset=Comedor.objects.none(), disabled=True, label="Comedor"
    )
    comienzo = forms.CharField(
        required=True, disabled=True, label="¿En qué año comenzó a funcionar?"
    )
    calle = forms.CharField(required=True, disabled=True, label="Calle")
    numero = forms.CharField(required=True, disabled=True, label="Numero")
    entre_calle_1 = forms.CharField(required=True, disabled=True, label="Entre calle 1")
    entre_calle_2 = forms.CharField(required=True, disabled=True, label="Entre calle 2")
    provincia = forms.CharField(required=True, disabled=True, label="Provincia")
    municipio = forms.CharField(required=True, disabled=True, label="Municipio")
    localidad = forms.CharField(required=True, disabled=True, label="Localidad")
    partido = forms.CharField(required=True, disabled=True, label="Partido")
    barrio = forms.CharField(required=True, disabled=True, label="Barrio")
    codigo_postal = forms.CharField(required=True, disabled=True, label="Codigo Postal")
    referente_nombre = forms.CharField(required=True, disabled=True, label="Nombre")
    referente_apellido = forms.CharField(required=True, disabled=True, label="Apellido")
    referente_mail = forms.CharField(required=True, disabled=True, label="Mail")
    referente_numero = forms.CharField(required=True, disabled=True, label="Celular")
    referente_documento = forms.CharField(required=True, disabled=True, label="DNI")

    def __init__(self, *args, **kwargs):
        comedor_id = kwargs.pop("pk", None)
        super().__init__(*args, **kwargs)

        if comedor_id is not None:
            self.popular_informacion_comedor(comedor_id)

    def popular_informacion_comedor(self, comedor_id):
        comedor = Comedor.objects.get(pk=comedor_id)

        self.fields["comedor"].initial = comedor
        self.fields["comedor"].queryset = Comedor.objects.filter(pk=comedor_id)

        self.fields["fecha_visita"].initial = timezone.now
        self.fields["fecha_visita"].widget.attrs["disabled"] = True

        self.fields["comienzo"].initial = comedor.comienzo
        self.fields["calle"].initial = comedor.calle
        self.fields["numero"].initial = comedor.numero
        self.fields["entre_calle_1"].initial = comedor.entre_calle_1
        self.fields["entre_calle_2"].initial = comedor.entre_calle_2
        self.fields["provincia"].initial = comedor.provincia
        self.fields["municipio"].initial = comedor.municipio
        self.fields["localidad"].initial = comedor.localidad
        self.fields["partido"].initial = comedor.partido
        self.fields["barrio"].initial = comedor.barrio
        self.fields["codigo_postal"].initial = comedor.codigo_postal
        self.fields["referente_nombre"].initial = comedor.referente.nombre
        self.fields["referente_apellido"].initial = comedor.referente.apellido
        self.fields["referente_mail"].initial = comedor.referente.mail
        self.fields["referente_numero"].initial = comedor.referente.numero
        self.fields["referente_documento"].initial = comedor.referente.documento

    class Meta:
        model = Relevamiento
        fields = [
            "fecha_visita",
            "comedor",
        ]
        field_order = ["fecha_visita", "comedor", "comienzo"]
