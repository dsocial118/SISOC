from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator

from legajos.models import LegajoLocalidad, LegajoMunicipio, LegajoProvincias, Legajos
from usuarios.models import Usuarios

class TipoModalidadPrestacion(models.Model):
    """
    Opciones de modalidades de prestacion de un Comedor/Merendero
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
    Opciones de tipos de espacios fisicos para un Comedor/Merendero
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
    Opciones de tipos de abastecimiento de combustible de un Comedor/Merendero
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
    Opciones de tipos de abastecimiento de agua de un Comedor/Merendero
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
    Opciones de tipos de desagues de hinodoro de un Comedor/Merendero
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
    Opciones de frecuencias de limpieza de un Comedor/Merendero
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
    Opciones de cantidades de colaboradores de un Comedor/Merendero
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
    Informacion relacionada al funcionamiento del Comedor/Merendero
    """

    modalidad_prestacion = models.ForeignKey(
        TipoModalidadPrestacion,
        on_delete=models.PROTECT,
        verbose_name="1.1.4 Modalidad de prestación",
    )
    servicio_por_turnos = models.BooleanField()
    cantidad_turnos = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(3),
        ],
    )

    class Meta:
        verbose_name = "Funcionamiento de comedor"
        verbose_name_plural = "Funcionamientos de comedores"


class EspacioCocina(models.Model):
    """
    Informacion relacionada a la cocina y almacenamiento de alimentos
    """

    espacio_elaboracion_alimentos = models.BooleanField()
    almacenamiento_alimentos_secos = models.BooleanField()
    heladera = models.BooleanField()
    freezer = models.BooleanField()
    recipiente_residuos_organicos = models.BooleanField()
    recipiente_residuos_reciclables = models.BooleanField()
    recipiente_otros_residuos = models.BooleanField()
    abastecimiento_combustible = models.ManyToManyField(
        to=TipoCombustible,
        related_name="espacios",
        verbose_name="2.2.7 Para cocinar utiliza",
    )
    abastecimiento_agua = models.ForeignKey(
        to=TipoAgua,
        on_delete=models.PROTECT,
        verbose_name="2.2.8 El abastecimiento del agua es con",
    )
    instalacion_electrica = models.BooleanField()

    class Meta:
        verbose_name = "Espacio de cocina y almacenamiento de alimentos"
        verbose_name_plural = "Espacios de cocina y almacenamiento de alimentos"


class EspacioPrestacion(models.Model):
    """
    Informacion relacionada al espacio donde se brinda la prestacion del Comedor/Merendero
    """

    espacio_equipado = models.BooleanField()
    tiene_ventilacion = models.BooleanField()
    tiene_salida_emergencia = models.BooleanField()
    salida_emergencia_senializada = models.BooleanField()
    tiene_equipacion_incendio = models.BooleanField()
    tiene_botiquin = models.BooleanField()
    tiene_buena_iluminacion = models.BooleanField()
    tiene_sanitarios = models.BooleanField()
    desague_hinodoro = models.ForeignKey(
        to=TipoDesague,
        on_delete=models.PROTECT,
        verbose_name="2.3.9 Si la respuesta anterior es SI, el desagüe del inodoro es",
        blank=True,
        null=True,
    )
    tiene_buzon_quejas = models.BooleanField()
    tiene_gestion_quejas = models.BooleanField(
        verbose_name=(
            "¿Hay en el lugar cartelería con información sobre los mecanismos "
            "de gestión de quejas, reclamos y sugerencias del Comedor/Merendero/Merendero?"
        )
    )
    frecuencia_limpieza = models.ForeignKey(
        to=FrecuenciaLimpieza,
        on_delete=models.PROTECT,
        verbose_name="2.4.1 ¿Con qué frecuencia se realiza la limpieza de las instalaciones?",
    )

    class Meta:
        verbose_name = "Espacio donde se brinda la prestacion del Comedor/Merendero"
        verbose_name_plural = (
            "Espacios donde se brinda la prestacion del Comedor/Merendero"
        )


class Colaboradores(models.Model):
    """
    Informacion relacionada a las personas que realizan tareas en el Comedor/Merendero
    """

    cantidad_colaboradores = models.ForeignKey(
        to=CantidadColaboradores,
        on_delete=models.PROTECT,
        verbose_name="3.1.1 ¿Qué cantidad de personas realizan tareas en el Comedor / Merendero?",
    )
    colaboradores_capacitados_alimentos = models.BooleanField(
        verbose_name="3.1.2 ¿El Comedor/Merendero cuentan con personas que realizan tareas capacitadas para la manipulación de alimentos?"
    )
    colaboradores_recibieron_capacitacion_alimentos = models.BooleanField()
    colaboradores_capacitados_salud_seguridad = models.BooleanField()
    colaboradores_recibieron_capacitacion_emergencias = models.BooleanField()
    colaboradores_recibieron_capacitacion_violencia = models.BooleanField(
        verbose_name=(
            "¿Los colaboradores recibieron capacitación sobre prevención de violencia de género "
            "incluyendo acoso sexual, explotación sexual y abuso infantil?"
        )
    )


class Espacio(models.Model):
    """
    Informacion relacionada al espacio fisico del Comedor/Merendero.
    Contiene la informacion de la cocina y la prestacion del Comedor/Merendero
    """

    tipo_espacio_fisico = models.ForeignKey(
        to=TipoEspacio,
        on_delete=models.PROTECT,
        verbose_name="2.1.1 ¿En qué tipo de espacio físico funciona el Comedor/Merendero?",
    )
    espacio_fisico_otro = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="2.1.2 Si eligió 'Otro', especificar",
    )

    cocina = models.OneToOneField(
        to=EspacioCocina,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    prestacion = models.OneToOneField(
        to=EspacioPrestacion,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Espacio fisico de comedor"
        verbose_name_plural = "Espacios fisicos de comedores"


class FrecuenciaRecepcionRecursos(models.Model):
    """
    Opciones de frecuencias de recepcion de recursos para un Comedor/Merendero
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
    Opciones de tipos de recursos recibidos por un Comedor/Merendero
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
    Informacion relacionada a las fuentes de recursos del Comedor/Merendero
    """

    recibe_donaciones_particulares = models.BooleanField()
    frecuencia_donaciones_particulares = models.ForeignKey(
        to=FrecuenciaRecepcionRecursos,
        on_delete=models.PROTECT,
        verbose_name="4.1.8 Si recibe, ¿Con qué frecuencia recibe donaciones particulares?",
        related_name="frecuencia_donaciones_particulares",
        blank=True,
        null=True,
    )
    recursos_donaciones_particulares = models.ForeignKey(
        to=TipoRecurso,
        on_delete=models.PROTECT,
        verbose_name="4.1.9 ¿Qué tipo de recursos recibe de donaciones particulares?",
        related_name="tipo_donaciones_particulares",
        blank=True,
        null=True,
    )

    recibe_estado_nacional = models.BooleanField()
    frecuencia_estado_nacional = models.ForeignKey(
        to=FrecuenciaRecepcionRecursos,
        on_delete=models.PROTECT,
        verbose_name="4.1.10 Si recibe, ¿Con qué frecuencia recibe del estado nacional?",
        related_name="frecuencia_estado_nacional",
        blank=True,
        null=True,
    )
    recursos_estado_nacional = models.ForeignKey(
        to=TipoRecurso,
        on_delete=models.PROTECT,
        verbose_name="4.1.11 ¿Qué tipo de recursos recibe del estado nacional?",
        related_name="tipo_estado_nacional",
        blank=True,
        null=True,
    )

    recibe_estado_provincial = models.BooleanField()
    frecuencia_estado_provincial = models.ForeignKey(
        to=FrecuenciaRecepcionRecursos,
        on_delete=models.PROTECT,
        verbose_name="4.1.12 Si recibe, ¿Con qué frecuencia recibe del estado provincial?",
        related_name="frecuencia_estado_provincial",
        blank=True,
        null=True,
    )
    recursos_estado_provincial = models.ForeignKey(
        to=TipoRecurso,
        on_delete=models.PROTECT,
        verbose_name="4.1.15 ¿Qué tipo de recursos recibe del estado provincial?",
        related_name="tipo_estado_provincial",
        blank=True,
        null=True,
    )

    recibe_estado_municipal = models.BooleanField()
    frecuencia_estado_municipal = models.ForeignKey(
        to=FrecuenciaRecepcionRecursos,
        on_delete=models.PROTECT,
        verbose_name="4.1.16Si recibe, ¿Con qué frecuencia recibe del estado municipal?",
        related_name="frecuencia_estado_municipal",
        blank=True,
        null=True,
    )
    recursos_estado_municipal = models.ForeignKey(
        to=TipoRecurso,
        on_delete=models.PROTECT,
        verbose_name="4.1.17 ¿Qué tipo de recursos recibe del estado municipal?",
        related_name="tipo_estado_municipal",
        blank=True,
        null=True,
    )

    recibe_otros = models.BooleanField()
    frecuencia_otros = models.ForeignKey(
        to=FrecuenciaRecepcionRecursos,
        on_delete=models.PROTECT,
        verbose_name="4.1.18 Si recibe, ¿Con qué frecuencia recibe de otras fuentes?",
        related_name="frecuencia_otros",
        blank=True,
        null=True,
    )
    recursos_otros = models.ForeignKey(
        to=TipoRecurso,
        on_delete=models.PROTECT,
        verbose_name="4.1.19 ¿Qué tipo de recursos recibe de otras fuentes?",
        related_name="tipo_otros",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Fuente de recursos"
        verbose_name_plural = "Fuentes de recursos"


class FuenteCompras(models.Model):
    """
    Informacion relacionada a la realizacion de compras para abastecer el Comedor/Merendero
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


class Prestacion(models.Model):
    """
    Modelo que representa una prestación brindada en un Comedor/Merendero.
    """

    # TODO: Esto tiene que se refactorizado, pero se como hacer los formularios :p
    lunes_desayuno_actual = models.PositiveIntegerField(null=True, blank=True)
    lunes_desayuno_espera = models.PositiveIntegerField(null=True, blank=True)
    lunes_almuerzo_actual = models.PositiveIntegerField(null=True, blank=True)
    lunes_almuerzo_espera = models.PositiveIntegerField(null=True, blank=True)
    lunes_merienda_actual = models.PositiveIntegerField(null=True, blank=True)
    lunes_merienda_espera = models.PositiveIntegerField(null=True, blank=True)
    lunes_cena_actual = models.PositiveIntegerField(null=True, blank=True)
    lunes_cena_espera = models.PositiveIntegerField(null=True, blank=True)

    martes_desayuno_actual = models.PositiveIntegerField(null=True, blank=True)
    martes_desayuno_espera = models.PositiveIntegerField(null=True, blank=True)
    martes_almuerzo_actual = models.PositiveIntegerField(null=True, blank=True)
    martes_almuerzo_espera = models.PositiveIntegerField(null=True, blank=True)
    martes_merienda_actual = models.PositiveIntegerField(null=True, blank=True)
    martes_merienda_espera = models.PositiveIntegerField(null=True, blank=True)
    martes_cena_actual = models.PositiveIntegerField(null=True, blank=True)
    martes_cena_espera = models.PositiveIntegerField(null=True, blank=True)

    miercoles_desayuno_actual = models.PositiveIntegerField(null=True, blank=True)
    miercoles_desayuno_espera = models.PositiveIntegerField(null=True, blank=True)
    miercoles_almuerzo_actual = models.PositiveIntegerField(null=True, blank=True)
    miercoles_almuerzo_espera = models.PositiveIntegerField(null=True, blank=True)
    miercoles_merienda_actual = models.PositiveIntegerField(null=True, blank=True)
    miercoles_merienda_espera = models.PositiveIntegerField(null=True, blank=True)
    miercoles_cena_actual = models.PositiveIntegerField(null=True, blank=True)
    miercoles_cena_espera = models.PositiveIntegerField(null=True, blank=True)

    jueves_desayuno_actual = models.PositiveIntegerField(null=True, blank=True)
    jueves_desayuno_espera = models.PositiveIntegerField(null=True, blank=True)
    jueves_almuerzo_actual = models.PositiveIntegerField(null=True, blank=True)
    jueves_almuerzo_espera = models.PositiveIntegerField(null=True, blank=True)
    jueves_merienda_actual = models.PositiveIntegerField(null=True, blank=True)
    jueves_merienda_espera = models.PositiveIntegerField(null=True, blank=True)
    jueves_cena_actual = models.PositiveIntegerField(null=True, blank=True)
    jueves_cena_espera = models.PositiveIntegerField(null=True, blank=True)

    viernes_desayuno_actual = models.PositiveIntegerField(null=True, blank=True)
    viernes_desayuno_espera = models.PositiveIntegerField(null=True, blank=True)
    viernes_almuerzo_actual = models.PositiveIntegerField(null=True, blank=True)
    viernes_almuerzo_espera = models.PositiveIntegerField(null=True, blank=True)
    viernes_merienda_actual = models.PositiveIntegerField(null=True, blank=True)
    viernes_merienda_espera = models.PositiveIntegerField(null=True, blank=True)
    viernes_cena_actual = models.PositiveIntegerField(null=True, blank=True)
    viernes_cena_espera = models.PositiveIntegerField(null=True, blank=True)

    sabado_desayuno_actual = models.PositiveIntegerField(null=True, blank=True)
    sabado_desayuno_espera = models.PositiveIntegerField(null=True, blank=True)
    sabado_almuerzo_actual = models.PositiveIntegerField(null=True, blank=True)
    sabado_almuerzo_espera = models.PositiveIntegerField(null=True, blank=True)
    sabado_merienda_actual = models.PositiveIntegerField(null=True, blank=True)
    sabado_merienda_espera = models.PositiveIntegerField(null=True, blank=True)
    sabado_cena_actual = models.PositiveIntegerField(null=True, blank=True)
    sabado_cena_espera = models.PositiveIntegerField(null=True, blank=True)

    domingo_desayuno_actual = models.PositiveIntegerField(null=True, blank=True)
    domingo_desayuno_espera = models.PositiveIntegerField(null=True, blank=True)
    domingo_almuerzo_actual = models.PositiveIntegerField(null=True, blank=True)
    domingo_almuerzo_espera = models.PositiveIntegerField(null=True, blank=True)
    domingo_merienda_actual = models.PositiveIntegerField(null=True, blank=True)
    domingo_merienda_espera = models.PositiveIntegerField(null=True, blank=True)
    domingo_cena_actual = models.PositiveIntegerField(null=True, blank=True)
    domingo_cena_espera = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Prestacion"
        verbose_name_plural = "Prestaciones"


class Referente(models.Model):
    """
    Modelo que representa a un referente, en algun futuro se migrara a Legajo.

    Atributos:
        nombre (CharField): Nombre del referente.
        apellido (CharField): Apellido del referente.
        mail (EmailField): Dirección de correo electrónico única del referente.
        celular (BigIntegerField): Número único del referente.
        documento (BigIntegerField): Documento único del referente.
    """

    nombre = models.CharField(max_length=255, verbose_name="Nombe del referente")
    apellido = models.CharField(max_length=255, verbose_name="Apellido del referente")
    mail = models.EmailField(unique=True, verbose_name="Mail del referente")
    celular = models.BigIntegerField(unique=True, verbose_name="Celular del referente")
    documento = models.BigIntegerField(
        unique=True, verbose_name="Documento del referente"
    )

    class Meta:
        verbose_name = "Referente"
        verbose_name_plural = "Referentes"


class Comedor(models.Model):
    """
    Modelo que representa un Comedor/Merendero.

    Atributos:
        nombre (CharField): Nombre del Comedor/Merendero.
        comienzo (IntegerField): Año de inicio de la actividad del Comedor/Merendero.
        calle (CharField): Calle donde se encuentra el Comedor/Merendero.
        numero (PositiveIntegerField): Número de la calle donde se encuentra el Comedor/Merendero.
        entre_calle_1 (CharField): Primera calle entre la cual se encuentra el Comedor/Merendero.
        entre_calle_2 (CharField): Segunda calle entre la cual se encuentra el Comedor/Merendero.
        provincia (ForeignKey): Provincia donde se encuentra el Comedor/Merendero.
        municipio (ForeignKey): Municipio donde se encuentra el Comedor/Merendero.
        localidad (ForeignKey): Localidad donde se encuentra el Comedor/Merendero.
        partido (CharField): Partido donde se encuentra el Comedor/Merendero/Merendero.
        barrio (CharField): Barrio donde se encuentra el Comedor/Merendero.
        codigo_postal (IntegerField): Código postal del Comedor/Merendero.
        referente (ForeignKey): Referente del Comedor/Merendero.
    """

    nombre = models.CharField(
        max_length=255,
    )
    comienzo = models.IntegerField(
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(timezone.now().year),
        ],
        verbose_name="Año en el que comenzó a funcionar",
    )
    calle = models.CharField(max_length=255)
    numero = models.PositiveIntegerField()
    entre_calle_1 = models.CharField(max_length=255, blank=True, null=True)
    entre_calle_2 = models.CharField(max_length=255, blank=True, null=True)
    provincia = models.ForeignKey(to=LegajoProvincias, on_delete=models.PROTECT)
    municipio = models.ForeignKey(to=LegajoMunicipio, on_delete=models.PROTECT)
    localidad = models.ForeignKey(to=LegajoLocalidad, on_delete=models.PROTECT)
    partido = models.CharField(max_length=255)
    barrio = models.CharField(max_length=255)
    codigo_postal = models.IntegerField(
        validators=[
            MinValueValidator(1000),
            MaxValueValidator(999999),
        ],  # Entre 4 a 6 digitos
    )
    referente = models.ForeignKey(
        to=Referente, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self) -> str:
        return str(self.nombre)

    class Meta:
        indexes = [
            models.Index(fields=["nombre"]),
        ]
        verbose_name = "comedor"
        verbose_name_plural = "comedores"
        ordering = ["nombre"]


class Relevamiento(models.Model):
    """
    Modelo que representa un relevamiento realizado en un Comedor/Merendero.

    Atributos:
        Comedor/Merendero/Merendero (ForeignKey): Relación con el Comedor/Merendero donde se realizó el relevamiento.
        fecha_visita (DateTimeField): Fecha y hora de la visita.
        funcionamiento (OneToOneField): Información relacionada al funcionamiento del Comedor/Merendero.
        espacio (OneToOneField): Información relacionada al espacio físico del Comedor/Merendero.
        colaboradores (OneToOneField): Información relacionada a las personas que realizan tareas en el Comedor/Merendero/Merendero/Merendero.
        recursos (OneToOneField): Información relacionada a las fuentes de recursos del Comedor/Merendero.
        compras (OneToOneField): Información relacionada a la realización de compras para abastecer el Comedor/Merendero.
    """

    comedor = models.ForeignKey(
        to=Comedor,
        on_delete=models.CASCADE,
    )
    relevador = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, null=True)
    fecha_visita = models.DateTimeField(default=timezone.now, blank=True)
    funcionamiento = models.OneToOneField(
        to=FuncionamientoPrestacion,
        on_delete=models.PROTECT,
    )
    espacio = models.OneToOneField(
        to=Espacio,
        on_delete=models.PROTECT,
    )
    colaboradores = models.OneToOneField(
        to=Colaboradores,
        on_delete=models.PROTECT,
    )
    recursos = models.OneToOneField(
        to=FuenteRecursos,
        on_delete=models.PROTECT,
    )
    compras = models.OneToOneField(
        to=FuenteCompras,
        on_delete=models.PROTECT,
    )
    prestacion = models.OneToOneField(
        to=Prestacion,
        on_delete=models.PROTECT,
    )

    class Meta:
        indexes = [
            models.Index(fields=["comedor"]),
        ]
        verbose_name = "Relevamiento"
        verbose_name_plural = "Relevamientos"


class Observacion(models.Model):
    """
    Modelo que representa una observación realizada en un Comedor/Merendero.
    """

    observador = models.ForeignKey(
        to=Usuarios, on_delete=models.SET_NULL, null=True, blank=True
    )
    comedor = models.ForeignKey(
        to=Comedor,
        on_delete=models.CASCADE,
        blank=True,
    )
    fecha = models.DateTimeField(default=timezone.now, blank=True)
    observacion = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=["comedor"]),
        ]
        verbose_name = "Observacion"
        verbose_name_plural = "Observaciones"
