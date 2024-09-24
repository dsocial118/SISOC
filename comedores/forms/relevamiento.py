from typing import Any
from django import forms
from django.utils import timezone, dateformat
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
    servicio_por_turnos = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="1.1.5 ¿El servicio está organizado por turnos?",
    )
    cantidad_turnos = forms.IntegerField(
        min_value=1, max_value=3, label="1.1.6 Cantidad de turnos"
    )

    class Meta:
        model = FuncionamientoPrestacion
        fields = "__all__"


class EspacioCocinaForm(forms.ModelForm):
    espacio_elaboracion_alimentos = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="2.2.1 ¿Cuenta con un espacio específico para elaboración de alimentos?",
    )
    almacenamiento_alimentos_secos = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="2.2.2 ¿El espacio posee un lugar para el almacenamiento de los alimentos secos que compra/recibe? ",
    )
    heladera = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="2.2.3 ¿El Comedor/Merendero cuenta con heladera?",
    )
    freezer = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="2.2.3 ¿El Comedor/Merendero cuenta con freezer?",
    )
    recipiente_residuos_organicos = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="2.2.4 ¿La cocina cuenta con un espacio o recipientes destinados a la disposición de residuos orgánicos y asimilables?",
    )
    recipiente_residuos_reciclables = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="2.2.5 ¿El Comedor/Merendero cuenta con un espacio o recipientes destinados a la disposición de residuos reciclables?",
    )
    recipiente_otros_residuos = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label=(
            "2.2.6 ¿Las actividades del Comedor/Merendero generan otro tipo de residuos? "
            "¿Cuenta con un espacio o recipientes destinados a la disposición de dichos residuos?"
        ),
    )
    instalacion_electrica = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="2.2.9 ¿Cuenta con instalación eléctrica adecuada? ",
    )

    class Meta:
        model = EspacioCocina
        fields = "__all__"


class EspacioPrestacionForm(forms.ModelForm):
    espacio_equipado = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="2.3.1 En caso de brindar la prestación de forma presencial ¿cuenta con espacio y equipamiento (mesas, bancos o sillas)?",
    )
    tiene_ventilacion = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="2.3.2 ¿El espacio donde tiene actividad el Comedor/Merendero cuenta con un sistema de ventilación?",
    )
    tiene_salida_emergencia = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="2.3.3 ¿El espacio donde tiene actividad el Comedor/Merendero cuenta con salidas de emergencia?",
    )
    salida_emergencia_senializada = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="2.3.4 ¿Las salidas de emergencia mencionadas en la respuesta anterior se encuentran correctamente señalizadas? ",
    )
    tiene_equipacion_incendio = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="2.3.5 ¿El lugar cuenta con elementos para apagar incendios (matafuegos, etc.)?",
    )
    tiene_botiquin = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="2.3.6 ¿El lugar cuenta con un botiquín de primeros auxilios?",
    )
    tiene_buena_iluminacion = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="2.3.7 ¿El espacio donde tiene actividad el Comedor/Merendero cuenta con iluminación?",
    )
    tiene_sanitarios = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="2.3.8 ¿El lugar cuenta con baño para las personas que realizan tareas en el comedor/merendero y para los destinatarios?",
    )
    tiene_buzon_quejas = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="2.3.10 ¿El Comedor y/o Merendero cuenta con alguna forma de registro de los reclamos sobre la prestación alimentaria?",
    )
    tiene_gestion_quejas = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label=(
            "2.3.11 ¿Hay en el lugar cartelería con información sobre los mecanismos "
            "de gestión de quejas, reclamos y sugerencias del Comedor y/o Merendero?"
        ),
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
        label="3.1.2 ¿El Comedor/Merendero cuentan con personas que realizan tareas capacitadas para la manipulación de alimentos?",
    )
    colaboradores_recibieron_capacitacion_alimentos = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="3.1.3 ¿Las personas que realizan tareas en el Comedor/Merendero recibieron capacitación sobre seguridad e higiene de alimentos?",
    )
    colaboradores_capacitados_salud_seguridad = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="3.1.4 ¿Las personas que realizan tareas en el Comedor/Merendero recibieron capacitación sobre salud y prevención de accidentes?",
    )
    colaboradores_recibieron_capacitacion_emergencias = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="3.1.5 ¿Las personas que realizan tareas en el Comedor/Merendero recibió capacitación sobre preparación y respuesta a las emergencias?",
    )
    colaboradores_recibieron_capacitacion_violencia = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label=(
            "3.1.6 ¿Las personas que realizan tareas en el Comedor/Merendero recibieron capacitación "
            "sobre prevención de violencia de género incluyendo acoso sexual, explotación sexual y/o abuso infantil?"
        ),
    )

    class Meta:
        model = Colaboradores
        fields = "__all__"


class FuenteRecursosForm(forms.ModelForm):
    recibe_donaciones_particulares = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="4.1.1 Donaciones de particulares",
    )
    recibe_estado_nacional = forms.ChoiceField(
        choices=BOOLEAN_CHOICE, widget=forms.Select, label="4.1.2 Estado Nacional"
    )
    recibe_estado_provincial = forms.ChoiceField(
        choices=BOOLEAN_CHOICE, widget=forms.Select, label="4.1.3 Estado Provincial"
    )
    recibe_estado_municipal = forms.ChoiceField(
        choices=BOOLEAN_CHOICE, widget=forms.Select, label="4.1.4 Estado Municipal"
    )
    recibe_otros = forms.ChoiceField(
        choices=BOOLEAN_CHOICE, widget=forms.Select, label="4.1.5 Otros "
    )

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
    fecha_visita_ui = forms.CharField(
        disabled=True,
        label="1.1.1 Fecha y horario de la visita",
        initial=dateformat.format(timezone.now(), "H:i d/m/Y"),
    )
    comedor = forms.ModelChoiceField(
        queryset=Comedor.objects.none(),
        disabled=True,
        label="1.1.2 Nombre del Comedor/Merendero",
    )
    comienzo = forms.CharField(
        required=True, disabled=True, label="1.1.3 ¿En qué año comenzó a funcionar?"
    )
    calle = forms.CharField(required=True, disabled=True, label="1.2.1 Calle")
    numero = forms.CharField(required=True, disabled=True, label="1.2.2 Número")
    entre_calle_1 = forms.CharField(
        required=False, disabled=True, label="1.2.3 Entre calle 1"
    )
    entre_calle_2 = forms.CharField(
        required=False, disabled=True, label="1.2.4 Entre calle 2"
    )
    provincia = forms.CharField(required=True, disabled=True, label="1.2.10 Provincia")
    municipio = forms.CharField(required=True, disabled=True, label="1.2.8 Municipio")
    localidad = forms.CharField(required=True, disabled=True, label="1.2.7 Localidad")
    partido = forms.CharField(
        required=True, disabled=True, label="1.2.9 Departamento/Partido"
    )
    barrio = forms.CharField(required=True, disabled=True, label="1.2.5 Barrio")
    codigo_postal = forms.CharField(
        required=True, disabled=True, label="1.2.6 Código Postal"
    )
    referente_nombre = forms.CharField(
        required=True, disabled=True, label="1.3.1 Nombre del referente/responsable"
    )
    referente_apellido = forms.CharField(
        required=True, disabled=True, label="1.3.5 Apellido del referente/responsable"
    )
    referente_mail = forms.CharField(
        required=True, disabled=True, label="1.3.2 Mail del referente/responsable"
    )
    referente_celular = forms.CharField(
        required=True, disabled=True, label="1.3.3 Celular del referente/responsable"
    )
    referente_documento = forms.CharField(
        required=True, disabled=True, label="1.3.4 DNI del referente/responsable"
    )

    def __init__(self, *args, **kwargs):
        comedor_id = kwargs.pop("pk", None)
        super().__init__(*args, **kwargs)

        self.popular_informacion_comedor(comedor_id)

    def popular_informacion_comedor(self, comedor_id):
        comedor = Comedor.objects.get(pk=comedor_id)

        self.fields["comedor"].initial = comedor
        self.fields["comedor"].queryset = Comedor.objects.filter(pk=comedor_id)

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
        self.fields["referente_celular"].initial = comedor.referente.celular
        self.fields["referente_documento"].initial = comedor.referente.documento

    class Meta:
        model = Relevamiento
        fields = [
            "comedor",
        ]
