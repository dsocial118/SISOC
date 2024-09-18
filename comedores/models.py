from django.db import models
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator

from legajos.models import LegajoLocalidad, LegajoMunicipio, LegajoProvincias, Legajos


class TipoModalidadPrestacion(models.Model):
    """
    Opciones de modalidades de prestacion de un comedor
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de Modalidad de Prestación"
        verbose_name_plural = "Tipos de Modalidades de Prestación"
        ordering = ["nombre"]


class TipoEspacio(models.Model):
    """
    Opciones de tipos de espacios fisicos para un comedor
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de espacio fisico"
        verbose_name_plural = "Tipos de espacios fisicos"
        ordering = ["nombre"]


class TipoCombustible(models.Model):
    """
    Opciones de tipos de abastecimiento de combustible de un comedor
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de abastecimiento de combustible"
        verbose_name_plural = "Tipos de abastecimientos de combustible"
        ordering = ["nombre"]


class TipoAgua(models.Model):
    """
    Opciones de tipos de abastecimiento de agua de un comedor
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de abastecimiento de agua"
        verbose_name_plural = "Tipos de abastecimientos de agua"
        ordering = ["nombre"]


class TipoDesague(models.Model):
    """
    Opciones de tipos de desagues de hinodoro de un comedor
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de desague del hinodoro"
        verbose_name_plural = "Tipos de desagues del hinodoro"
        ordering = ["nombre"]


class FrecuenciaLimpieza(models.Model):
    """
    Opciones de frecuencias de limpieza de un comedor
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Frecuencia de limpieza"
        verbose_name_plural = "Frecuencias de limpieza"
        ordering = ["nombre"]


class CantidadColaboradores(models.Model):
    """
    Opciones de cantidades de colaboradores de un comedor
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Cantidad de colaboradores"
        verbose_name_plural = "Cantidades de colaboradores"
        ordering = ["nombre"]


class FuncionamientoPrestacion(models.Model):
    """
    Informacion relacionada al funcionamiento del comedor
    """

    modalidad_prestacion = models.ForeignKey(
        TipoModalidadPrestacion,
        on_delete=models.PROTECT,
    )
    servicio_por_turnos = models.BooleanField(
        help_text="¿El servicio esta organizado por turnos?"
    )
    cantidad_turnos = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        verbose_name = "Funcionamiento de comedor"
        verbose_name_plural = "Funcionamientos de comedores"


class EspacioCocina(models.Model):
    """
    Informacion relacionada a la cocina y almacenamiento de alimentos
    """

    espacio_elaboracion_alimentos = models.BooleanField(
        help_text="¿Cuenta con un espacio específico para elaboración de alimentos?",
    )
    almacenamiento_alimentos_secos = models.BooleanField(
        help_text="¿El espacio posee un lugar para el almacenamiento de los alimentos secos que compra / recibe?",
    )
    refrigerador = models.BooleanField(help_text="¿Cuenta con heladera o freezer?")
    recipiente_residuos_organicos = models.BooleanField(
        help_text="¿La cocina cuenta con un espacio o recipientes destinados a la disposición de residuos orgánicos y asimilables?"
    )
    recipiente_residuos_reciclables = models.BooleanField(
        help_text="¿El comedor cuenta con un espacio o recipientes destinados a la disposición de residuos reciclables?"
    )
    recipiente_otros_residuos = models.BooleanField(
        help_text="¿El comedor genera otro tipo de residuos? ¿Cuenta con un espacio destinados a la disposición de dichos residuos?"
    )
    abastecimiento_combustible = models.ManyToManyField(
        to=TipoCombustible,
        related_name="espacios",
        help_text="¿Cómo se abastece de combustible?",
    )
    abastecimiento_agua = models.ForeignKey(
        to=TipoAgua,
        on_delete=models.PROTECT,
        help_text="¿Cómo se abastece de agua el comedor?",
    )
    instalacion_electrica = models.BooleanField()

    class Meta:
        verbose_name = "Espacio de cocina y almacenamiento de alimentos"
        verbose_name_plural = "Espacios de cocina y almacenamiento de alimentos"


class EspacioPrestacion(models.Model):
    """
    Informacion relacionada al espacio donde se brinda la prestacion del comedor
    """

    espacio_equipado = models.BooleanField(
        help_text="¿Cuenta con espacio y equipamiento (mesas, bancos o sillas)?"
    )
    tiene_ventilacion = models.BooleanField(
        help_text="¿El espacio donde tiene actividad el comedor cuenta con un sistema de ventilación adecuado?"
    )
    tiene_salida_emergencia = models.BooleanField(
        help_text="¿El espacio donde tiene actividad el comedor cuenta con salidas de emergencia?"
    )
    salida_emergencia_senializada = models.BooleanField(
        help_text="¿Están señalizadas las salidas de emergencia?"
    )
    tiene_equipacion_incendio = models.BooleanField(
        help_text="El lugar cuenta con elementos para apagar incendios (matafuegos / manguera)?"
    )
    tiene_botiquin = models.BooleanField(
        help_text="¿El lugar cuenta con un botiquín de primeros auxilios?"
    )
    tiene_buena_iluminacion = models.BooleanField(
        help_text="¿El espacio donde tiene actividad el comedor cuenta con buena iluminación?"
    )
    tiene_sanitarios = models.BooleanField(
        help_text="¿El lugar cuenta con baño para las personas que realizan tareas en el comedor y para los destinatarios?"
    )
    desague_hinodoro = models.ForeignKey(
        to=TipoDesague,
        on_delete=models.PROTECT,
        help_text="Si hay sanitarios, ¿cómo es el desagüe del hinodoro?",
    )
    tiene_buzon_quejas = models.BooleanField(
        help_text="¿El comedor cuenta con un buzón de quejas y reclamos en el lugar?"
    )
    tiene_gestion_quejas = models.BooleanField(
        help_text="¿Hay en el lugar cartelería con información sobre los mecanismos de gestión de quejas, reclamos y sugerencias del comedor?"
    )
    frecuencia_limpieza = models.ForeignKey(
        to=FrecuenciaLimpieza,
        on_delete=models.PROTECT,
        help_text="¿Con qué frecuencia se realiza la limpieza de las instalaciones?",
    )

    class Meta:
        verbose_name = "Espacio donde se brinda la prestacion del comedor"
        verbose_name_plural = "Espacios donde se brinda la prestacion del comedor"


class Colaboradores(models.Model):
    """
    Informacion relacionada a las personas que realizan tareas en el comedor
    """

    cantidad_colaboradores = models.ForeignKey(
        to=CantidadColaboradores,
        on_delete=models.PROTECT,
        help_text="¿Qué cantidad de personas realizan tareas en el Comedor?",
    )
    colaboradores_capacitados_alimentos = models.BooleanField(
        help_text="¿Cuentan con personas que realizan tareas capacitadas para la manipulación de alimentos?"
    )
    colaboradores_recibieron_capacitacion_alimentos = models.BooleanField(
        help_text="¿Los colaboradores recibieron capacitación sobre manipulación segura de alimentos?"
    )
    colaboradores_capacitados_salud_seguridad = models.BooleanField(
        help_text="¿Los colaboradores recibieron capacitación sobre salud y seguridad ocupacional?"
    )
    colaboradores_recibieron_capacitacion_emergencias = models.BooleanField(
        help_text="¿Los colaboradores recibieron capacitación sobre preparación y respuesta a las emergencias?"
    )
    colaboradores_recibieron_capacitacion_violencia = models.BooleanField(
        help_text=(
            "¿Los colaboradores recibieron capacitación sobre prevención de violencia de género "
            "incluyendo acoso sexual, explotación sexual y abuso infantil?"
        )
    )


class Espacio(models.Model):
    """
    Informacion relacionada al espacio fisico del comedor.
    Contiene la informacion de la cocina y la prestacion del comedor
    """

    tipo_espacio_fisico = models.ForeignKey(
        to=TipoEspacio,
        on_delete=models.PROTECT,
        help_text="¿En qué tipo de espacio físico funciona el comedor?",
    )
    espacio_fisico_otro = models.CharField(
        max_length=255, blank=True, null=True, help_text="Si eligió 'Otro', especificar"
    )

    cocina = models.OneToOneField(
        to=EspacioCocina,
        on_delete=models.PROTECT,
        help_text="Informacion relacionada a la cocina y almacenamiento de alimentos",
    )

    prestacion = models.OneToOneField(
        to=EspacioPrestacion,
        on_delete=models.PROTECT,
        help_text="Informacion relacionada al espacio donde se brinda la prestacion del comedor",
    )

    class Meta:
        verbose_name = "Espacio fisico de comedor"
        verbose_name_plural = "Espacios fisicos de comedores"


class FrecuenciaRecepcionRecursos(models.Model):
    """
    Opciones de frecuencias de recepcion de recursos para un comedor
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Frecuencia de recepcion de recursos"
        verbose_name_plural = "Frecuencias de recepcion de recursos"
        ordering = ["nombre"]


class TipoRecurso(models.Model):
    """
    Opciones de tipos de recursos recibidos por un comedor
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de recurso recibido"
        verbose_name_plural = "Tipos de recursos recibidos"
        ordering = ["nombre"]


class FuenteRecursos(models.Model):
    """
    Informacion relacionada a las fuentes de recursos del comedor
    """

    recibe_donaciones_particulares = models.BooleanField()
    frecuencia_donaciones_particulares = models.ForeignKey(
        to=FrecuenciaRecepcionRecursos,
        on_delete=models.PROTECT,
        help_text="Si recibe, ¿Con qué frecuencia recibe donaciones particulares?",
        related_name="frecuencia_donaciones_particulares",
    )
    recursos_donaciones_particulares = models.ForeignKey(
        to=TipoRecurso,
        on_delete=models.PROTECT,
        help_text="¿Qué tipo de recursos recibe de donaciones particulares?",
        related_name="tipo_donaciones_particulares",
    )

    recibe_estado_nacional = models.BooleanField()
    frecuencia_estado_nacional = models.ForeignKey(
        to=FrecuenciaRecepcionRecursos,
        on_delete=models.PROTECT,
        help_text="Si recibe, ¿Con qué frecuencia recibe del estado nacional?",
        related_name="frecuencia_estado_nacional",
    )
    recursos_estado_nacional = models.ForeignKey(
        to=TipoRecurso,
        on_delete=models.PROTECT,
        help_text="¿Qué tipo de recursos recibe del estado nacional?",
        related_name="tipo_estado_nacional",
    )

    recibe_estado_provincial = models.BooleanField()
    frecuencia_estado_provincial = models.ForeignKey(
        to=FrecuenciaRecepcionRecursos,
        on_delete=models.PROTECT,
        help_text="Si recibe, ¿Con qué frecuencia recibe del estado provincial?",
        related_name="frecuencia_estado_provincial",
    )
    recursos_estado_provincial = models.ForeignKey(
        to=TipoRecurso,
        on_delete=models.PROTECT,
        help_text="¿Qué tipo de recursos recibe del estado provincial?",
        related_name="tipo_estado_provincial",
    )

    recibe_estado_municipal = models.BooleanField()
    frecuencia_estado_municipal = models.ForeignKey(
        to=FrecuenciaRecepcionRecursos,
        on_delete=models.PROTECT,
        help_text="Si recibe, ¿Con qué frecuencia recibe del estado municipal?",
        related_name="frecuencia_estado_municipal",
    )
    recursos_estado_municipal = models.ForeignKey(
        to=TipoRecurso,
        on_delete=models.PROTECT,
        help_text="¿Qué tipo de recursos recibe del estado municipal?",
        related_name="tipo_estado_municipal",
    )

    recibe_otros = models.BooleanField()
    frecuencia_otros = models.ForeignKey(
        to=FrecuenciaRecepcionRecursos,
        on_delete=models.PROTECT,
        help_text="Si recibe, ¿Con qué frecuencia recibe de otras fuentes?",
        related_name="frecuencia_otros",
    )
    recursos_otros = models.ForeignKey(
        to=TipoRecurso,
        on_delete=models.PROTECT,
        help_text="¿Qué tipo de recursos recibe de otras fuentes?",
        related_name="tipo_otros",
    )

    class Meta:
        verbose_name = "Fuente de recursos"
        verbose_name_plural = "Fuentes de recursos"


class FuenteCompras(models.Model):
    """
    Informacion relacionada a la realizacion de compras para abastecer el comedor
    """

    almacen_cercano = models.BooleanField()
    verduleria = models.BooleanField()
    granja = models.BooleanField()
    carniceria = models.BooleanField()
    pescaderia = models.BooleanField()
    supermercado = models.BooleanField()
    mercado_central = models.BooleanField()
    ferias_comunales = models.BooleanField()
    mayoristas = models.BooleanField()
    otro = models.BooleanField()

    class Meta:
        verbose_name = "Fuente de compras"
        verbose_name_plural = "Fuentes de compras"


class TipoComida(models.Model):
    """
    Opciones de tipos de comidas por horario que se brindan en un comedor
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de comida"
        verbose_name_plural = "Tipos de comida"
        ordering = ["nombre"]


class NombreDia(models.Model):
    """
    Opciones de nombres de dias de la semana
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Nombre del dia"
        verbose_name_plural = "Nombre de los dias"
        ordering = ["nombre"]


class Prestacion(models.Model):
    """
    Modelo que representa una prestación brindada en un comedor.

    Atributos:
        relevamiento (ForeignKey): Relación con el relevamiento al que pertenece la prestación.
        tipo_comida (ForeignKey): Tipo de comida en que se brinda la prestación.
        nombre_dia (ForeignKey): Nombre del día en que se brinda la prestación.
        cantidad_actual_personas (PositiveIntegerField): Cantidad actual de personas que reciben la prestación.
        cantidad_personas_espera (PositiveIntegerField): Cantidad de personas en espera para recibir la prestación.
    """

    relevamiento = models.ForeignKey(
        to="Relevamiento",
        on_delete=models.CASCADE,
        help_text="Relevamiento al que pertenece la prestacion",
    )
    tipo_comida = models.ForeignKey(
        to=TipoComida,
        on_delete=models.PROTECT,
        help_text="Tipo de comida en que se brinda la prestacion",
    )
    nombre_dia = models.ForeignKey(
        to=NombreDia,
        on_delete=models.PROTECT,
        help_text="Nombre del dia en que se brinda la prestacion",
    )
    cantidad_actual_personas = models.PositiveIntegerField()
    cantidad_personas_espera = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Prestacion"
        verbose_name_plural = "Prestaciones"
        unique_together = ["relevamiento", "tipo_comida", "nombre_dia"]


class Comedor(models.Model):
    """
    Modelo que representa un comedor.

    Atributos:
        nombre (CharField): Nombre del comedor.
        comienzo (IntegerField): Año de inicio de la actividad del comedor.
        calle (CharField): Calle donde se encuentra el comedor.
        numero (PositiveIntegerField): Número de la calle donde se encuentra el comedor.
        entre_calle_1 (CharField): Primera calle entre la cual se encuentra el comedor.
        entre_calle_2 (CharField): Segunda calle entre la cual se encuentra el comedor.
        provincia (ForeignKey): Provincia donde se encuentra el comedor.
        municipio (ForeignKey): Municipio donde se encuentra el comedor.
        localidad (ForeignKey): Localidad donde se encuentra el comedor.
        partido (CharField): Partido donde se encuentra el comedor.
        barrio (CharField): Barrio donde se encuentra el comedor.
        codigo_postal (IntegerField): Código postal del comedor.
        referente (ForeignKey): Referente del comedor.
    """

    nombre = models.CharField(
        max_length=255,
    )
    comienzo = models.IntegerField(
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(timezone.now().year),
        ],
        help_text="Año de inicio de la actividad",
    )
    calle = models.CharField(max_length=255)
    numero = models.PositiveIntegerField()
    entre_calle_1 = models.CharField(max_length=255)
    entre_calle_2 = models.CharField(max_length=255)
    provincia = models.ForeignKey(to=LegajoProvincias, on_delete=models.PROTECT)
    municipio = models.ForeignKey(to=LegajoMunicipio, on_delete=models.PROTECT)
    localidad = models.ForeignKey(to=LegajoLocalidad, on_delete=models.PROTECT)
    partido = models.CharField(max_length=255)
    barrio = models.CharField(max_length=255)
    codigo_postal = models.IntegerField(
        default=1000,
        validators=[
            MinValueValidator(999),
            MaxValueValidator(100000),
        ],  # Entre 4 a 6 digitos
    )
    referente = models.ForeignKey(to=Legajos, on_delete=models.SET_NULL, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["nombre"]),
        ]
        verbose_name = "comedor"
        verbose_name_plural = "comedores"
        ordering = ["nombre"]


class Relevamiento(models.Model):
    """
    Modelo que representa un relevamiento realizado en un comedor.

    Atributos:
        comedor (ForeignKey): Relación con el comedor donde se realizó el relevamiento.
        fecha_visita (DateTimeField): Fecha y hora de la visita.
        funcionamiento (OneToOneField): Información relacionada al funcionamiento del comedor.
        espacio (OneToOneField): Información relacionada al espacio físico del comedor.
        colaboradores (OneToOneField): Información relacionada a las personas que realizan tareas en el comedor.
        recursos (OneToOneField): Información relacionada a las fuentes de recursos del comedor.
        compras (OneToOneField): Información relacionada a la realización de compras para abastecer el comedor.
    """

    comedor = models.ForeignKey(
        to=Comedor,
        on_delete=models.CASCADE,
    )
    fecha_visita = models.DateTimeField(default=timezone.now)
    funcionamiento = models.OneToOneField(
        to=FuncionamientoPrestacion,
        on_delete=models.PROTECT,
        help_text="Informacion relacionada al funcionamiento del comedor",
    )
    espacio = models.OneToOneField(
        to=Espacio,
        on_delete=models.PROTECT,
        help_text="Informacion relacionada al espacio fisico del comedor",
    )
    colaboradores = models.OneToOneField(
        to=Colaboradores,
        on_delete=models.PROTECT,
        help_text="Informacion relacionada a las personas que realizan tareas en el comedor",
    )
    recursos = models.OneToOneField(
        to=FuenteRecursos,
        on_delete=models.PROTECT,
        help_text="Informacion relacionada a las fuentes de recursos del comedor",
    )
    compras = models.OneToOneField(
        to=FuenteCompras,
        on_delete=models.PROTECT,
        help_text="Informacion relacionada a la realizacion de compras para abastecer el comedor",
    )

    class Meta:
        indexes = [
            models.Index(fields=["comedor"]),
        ]
        verbose_name = "Relevamiento"
        verbose_name_plural = "Relevamientos"


class Observacion(models.Model):
    """
    Modelo que representa una observación realizada en un comedor.
    """

    comedor = models.ForeignKey(
        to=Comedor,
        on_delete=models.CASCADE,
    )
    fecha = models.DateTimeField(auto_now=True)
    observacion = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=["comedor"]),
        ]
        verbose_name = "Observacion"
        verbose_name_plural = "Observaciones"