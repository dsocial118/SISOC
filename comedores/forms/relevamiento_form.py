from typing import Any

from django import forms
from django.forms import inlineformset_factory
from django.utils import dateformat, timezone

from comedores.models.relevamiento import Relevamiento
from comedores.models.comedor import (
    Comedor,
)
from comedores.models.relevamiento import (
    Anexo,
    Colaboradores,
    Espacio,
    EspacioCocina,
    EspacioPrestacion,
    FuenteCompras,
    FuenteRecursos,
    FuncionamientoPrestacion,
    Prestacion,
    PuntoEntregas,
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
        min_value=1, max_value=3, label="1.1.6 Cantidad de turnos", required=False
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
    otros_residuos = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="2.2.6 ¿Las actividades del Comedor/Merendero generan otro tipo de residuos?",
    )
    recipiente_otros_residuos = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Cuenta con un espacio o recipientes destinados a la disposición de dichos residuos?",
    )
    instalacion_electrica = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="2.2.9 ¿Cuenta con instalación eléctrica adecuada? ",
    )

    class Meta:
        model = EspacioCocina
        fields = "__all__"
        widgets = {
            "abastecimiento_combustible": forms.SelectMultiple(
                attrs={"class": "select2 w-100", "multiple": True}
            ),
        }


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
    informacion_quejas = forms.ChoiceField(
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.label = False

    class Meta:
        model = Prestacion
        fields = "__all__"


class AnexoForm(forms.ModelForm):
    comedor_merendero = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿El comedor/merendero existe?",
    )
    insumos_organizacion = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="Durante el año 2024, ¿recibió insumos por parte de la organización?",
    )
    servicio_internet = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="En el comedor, ¿hay servicio de internet?",
    )
    zona_inundable = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿El comedor se encuentra en zona inundable?",
    )
    actividades_jardin_maternal = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿En el comedor se realizan actividades propias de un jardín maternal?",
    )
    actividades_jardin_infantes = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿En el comedor se realizan actividades propias de un jardín de infantes/preescolar?",
    )
    apoyo_escolar = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿En el comedor se realizan actividades de apoyo escolar?",
    )
    alfabetizacion_terminalidad = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿En el comedor se realizan actividades propias de alfabetización/terminalidad educativa?",
    )
    capacitaciones_talleres = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿En el comedor se realizan capacitaciones y/o talleres de oficio?",
    )
    promocion_salud = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿En el comedor se realizan actividades para la promoción de la salud?",
    )
    actividades_discapacidad = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿En el comedor se realizan actividades orientadas a personas con discapacidad?",
    )
    necesidades_alimentarias = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿En el comedor se realizan actividades orientadas a personas con necesidades alimentarias especiales (celiaquía, diabetes, etc.)?",
    )
    actividades_recreativas = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿En el comedor se realizan actividades Recreativas/deportivas?",
    )
    actividades_culturales = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿En el comedor se realizan actividades culturales?",
    )
    emprendimientos_productivos = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿En el comedor se realizan emprendimientos productivos/de servicios (ej: elaboración de panificados, dulces y conservas, textil, peluquería, etc)?",
    )
    actividades_religiosas = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿En el comedor se realizan actividades religiosas?",
    )
    actividades_huerta = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿En el comedor se realizan actividades de huerta?",
    )
    espacio_huerta = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Cuenta con espacio para realizar ese tipo de actividades?",
        required=False,
    )
    otras_actividades = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿En el comedor se realizan otras actividades?",
    )
    cuales_otras_actividades = forms.CharField(
        required=False, widget=forms.Textarea, label="¿Cuales? (Campo de texto libre)"
    )

    class Meta:
        model = Anexo
        fields = "__all__"


class PuntosEntregaForm(forms.ModelForm):
    existe_punto_entregas = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Existe un punto de entrega de alimentos en el comedor/merendero?",
    )
    funciona_punto_entregas = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿El punto de entrega de alimentos funciona en el comedor/merendero?",
    )
    observa_entregas = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Observa las entregas de alimentos en el comedor/merendero?",
    )
    retiran_mercaderias_distribucion = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Retiran mercaderías de la distribución?",
    )
    retiran_mercaderias_comercio = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Retiran mercaderías de comercios?",
    )
    reciben_dinero = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Reciben dinero por la entrega de alimentos?",
    )
    registran_entrega_bolsones = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Registran la entrega de bolsones?",
    )

    class Meta:
        model = PuntoEntregas
        fields = "__all__"


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
        required=False, disabled=True, label="1.1.3 ¿En qué año comenzó a funcionar?"
    )
    calle = forms.CharField(required=False, disabled=True, label="1.2.1 Calle")
    numero = forms.CharField(required=False, disabled=True, label="1.2.2 Número")
    entre_calle_1 = forms.CharField(
        required=False, disabled=True, label="1.2.3 Entre calle 1"
    )
    entre_calle_2 = forms.CharField(
        required=False, disabled=True, label="1.2.4 Entre calle 2"
    )
    provincia = forms.CharField(required=False, disabled=True, label="1.2.10 Provincia")
    municipio = forms.CharField(required=False, disabled=True, label="1.2.8 Municipio")
    localidad = forms.CharField(required=False, disabled=True, label="1.2.7 Localidad")
    partido = forms.CharField(
        required=False, disabled=True, label="1.2.9 Departamento/Partido"
    )
    barrio = forms.CharField(required=False, disabled=True, label="1.2.5 Barrio")
    codigo_postal = forms.CharField(
        required=False, disabled=True, label="1.2.6 Código Postal"
    )
    responsable_es_referente = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿El responsable es el referente del comedor/merendero?",
    )

    def __init__(self, *args, **kwargs):
        comedor_id = kwargs.pop("comedor_pk", None)
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

    class Meta:
        model = Relevamiento
        fields = ["comedor", "observacion"]
