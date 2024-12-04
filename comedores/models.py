from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from configuraciones.models import Municipio, Provincia
from configuraciones.models import Localidad


class EstadosIntervencion(models.Model):
    """
    Guardado de los estados de las intervenciones realizadas a un legajo.
    """

    nombre = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nombre}"

    class Meta:
        verbose_name = "EstadosIntervencion"
        verbose_name_plural = "EstadosIntervenciones"

class TipoIntervencion(models.Model):
    """
    Guardado de los tipos de intervenciones realizadas a un legajo.
    """

    nombre = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nombre}"

    class Meta:
        verbose_name = "TipoIntervencion"
        verbose_name_plural = "TiposIntervencion"

class SubIntervencion(models.Model):
    """
    Guardado de las SubIntervencion realizadas a un legajo.
    """

    nombre = models.CharField(max_length=255)
    fk_subintervencion = models.ForeignKey(
        TipoIntervencion, on_delete=models.SET_NULL, default=1, null=True
    )

    def __str__(self):
        return f"{self.nombre}"

    class Meta:
        verbose_name = "SubIntervencion"
        verbose_name_plural = "SubIntervenciones"

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

    espacio_elaboracion_alimentos = models.BooleanField(default=False)
    almacenamiento_alimentos_secos = models.BooleanField(default=False)
    heladera = models.BooleanField(default=False)
    freezer = models.BooleanField(default=False)
    recipiente_residuos_organicos = models.BooleanField(default=False)
    recipiente_residuos_reciclables = models.BooleanField(default=False)
    otros_residuos = models.BooleanField(default=False)
    recipiente_otros_residuos = models.BooleanField(default=False)
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
    abastecimiento_agua_otro = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="En caso de otro, especificar",
    )
    instalacion_electrica = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Espacio de cocina y almacenamiento de alimentos"
        verbose_name_plural = "Espacios de cocina y almacenamiento de alimentos"


class TipoGestionQuejas(models.Model):
    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de gestion de quejas"
        verbose_name_plural = "Tipos de gestion de quejas"


class EspacioPrestacion(models.Model):
    """
    Informacion relacionada al espacio donde se brinda la prestacion del Comedor/Merendero
    """

    espacio_equipado = models.BooleanField(default=False)
    tiene_ventilacion = models.BooleanField(default=False)
    tiene_salida_emergencia = models.BooleanField(default=False)
    salida_emergencia_senializada = models.BooleanField(default=False)
    tiene_equipacion_incendio = models.BooleanField(default=False)
    tiene_botiquin = models.BooleanField(default=False)
    tiene_buena_iluminacion = models.BooleanField(default=False)
    tiene_sanitarios = models.BooleanField(default=False)
    desague_hinodoro = models.ForeignKey(
        to=TipoDesague,
        on_delete=models.PROTECT,
        verbose_name="2.3.9 Si la respuesta anterior es SI, el desagüe del inodoro es",
        blank=True,
        null=True,
    )
    gestion_quejas = models.ForeignKey(
        to=TipoGestionQuejas,
        on_delete=models.PROTECT,
        verbose_name=(
            "2.3.10 ¿El Comedor/Merendero cuenta con alguna forma de "
            "registro de los reclamos sobre la prestacion alimentaria"
        ),
    )
    gestion_quejas_otro = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="En caso de otro, especificar",
    )
    informacion_quejas = models.BooleanField(default=False)
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
        default=False,
        verbose_name="3.1.2 ¿El Comedor/Merendero cuentan con personas que realizan tareas capacitadas para la manipulación de alimentos?",
    )
    colaboradores_recibieron_capacitacion_alimentos = models.BooleanField(default=False)
    colaboradores_capacitados_salud_seguridad = models.BooleanField(default=False)
    colaboradores_recibieron_capacitacion_emergencias = models.BooleanField(
        default=False
    )
    colaboradores_recibieron_capacitacion_violencia = models.BooleanField(
        default=False,
        verbose_name=(
            "¿Los colaboradores recibieron capacitación sobre prevención de violencia de género "
            "incluyendo acoso sexual, explotación sexual y abuso infantil?"
        ),
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

    recibe_donaciones_particulares = models.BooleanField(default=False)
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

    recibe_estado_nacional = models.BooleanField(default=False)
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

    recibe_estado_provincial = models.BooleanField(default=False)
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

    recibe_estado_municipal = models.BooleanField(default=False)
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

    recibe_otros = models.BooleanField(default=False)
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

    def clean(self) -> None:
        if self.recibe_donaciones_particulares and (
            not self.frecuencia_donaciones_particulares
            or not self.recursos_donaciones_particulares
        ):
            raise ValueError(
                "Si recibe donaciones particulares, debe completar la frecuencia y el tipo de recurso"
            )

        if self.recibe_estado_nacional and (
            not self.frecuencia_estado_nacional or not self.recursos_estado_nacional
        ):
            raise ValueError(
                "Si recibe del estado nacional, debe completar la frecuencia y el tipo de recurso"
            )

        if self.recibe_estado_provincial and (
            not self.frecuencia_estado_provincial or not self.recursos_estado_provincial
        ):
            raise ValueError(
                "Si recibe del estado provincial, debe completar la frecuencia y el tipo de recurso"
            )

        if self.recibe_estado_municipal and (
            not self.frecuencia_estado_municipal or not self.recursos_estado_municipal
        ):
            raise ValueError(
                "Si recibe del estado municipal, debe completar la frecuencia y el tipo de recurso"
            )

        if self.recibe_otros and (not self.frecuencia_otros or not self.recursos_otros):
            raise ValueError(
                "Si recibe otros recursos, debe completar la frecuencia y el tipo de recurso"
            )

        return super().clean()

    class Meta:
        verbose_name = "Fuente de recursos"
        verbose_name_plural = "Fuentes de recursos"


class FuenteCompras(models.Model):
    """
    Informacion relacionada a la realizacion de compras para abastecer el Comedor/Merendero
    """

    almacen_cercano = models.BooleanField(default=False)
    verduleria = models.BooleanField(default=False)
    granja = models.BooleanField(default=False)
    carniceria = models.BooleanField(default=False)
    pescaderia = models.BooleanField(default=False)
    supermercado = models.BooleanField(default=False)
    mercado_central = models.BooleanField(default=False)
    ferias_comunales = models.BooleanField(default=False)
    mayoristas = models.BooleanField(default=False)
    otro = models.BooleanField(default=False)

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
    mail = models.EmailField(verbose_name="Mail del referente")
    celular = models.BigIntegerField(verbose_name="Celular del referente")
    documento = models.BigIntegerField(verbose_name="Documento del referente")

    class Meta:
        verbose_name = "Referente"
        verbose_name_plural = "Referentes"


class Comedor(models.Model):
    """
    Modelo que representa un Comedor/Merendero.

    Atributos:
        gestionar_uid (CharField): UID unica que referencia al Comedor/Merendero en GESTIONAR.
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

    gestionar_uid = models.CharField(max_length=255, unique=True, blank=True)

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
    provincia = models.ForeignKey(to=Provincia, on_delete=models.PROTECT, null=True)
    municipio = models.ForeignKey(to=Municipio, on_delete=models.PROTECT, null=True)
    localidad = models.ForeignKey(to=Localidad, on_delete=models.PROTECT, null=True)
    partido = models.CharField(max_length=255, null=True)
    barrio = models.CharField(max_length=255, null=True)
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

class Intervencion(models.Model):
    """
    Guardado de las intervenciones realizadas a un legajo.
    """

    fk_legajo = models.ForeignKey(Comedor, on_delete=models.SET_NULL, null=True)
    fk_subintervencion = models.ForeignKey(
        SubIntervencion, on_delete=models.SET_NULL, null=True
    )
    fk_tipo_intervencion = models.ForeignKey(
        TipoIntervencion, on_delete=models.SET_NULL, null=True
    )
    fecha = models.DateTimeField(auto_now_add=True)
    fk_estado = models.ForeignKey(
        EstadosIntervencion, on_delete=models.SET_NULL, default=1, null=True
    )

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Intervencion"
        verbose_name_plural = "Intervenciones"
        indexes = [models.Index(fields=["fk_legajo"])]


class Relevamiento(models.Model):
    """
    Modelo que representa un relevamiento realizado en un Comedor/Merendero.

    Atributos
        gestionar_uid (CharField): UID unica que referencia al Relevamiento en GESTIONAR.
        Comedor/Merendero/Merendero (ForeignKey): Relación con el Comedor/Merendero donde se realizó el relevamiento.
        fecha_visita (DateTimeField): Fecha y hora de la visita.
        funcionamiento (OneToOneField): Información relacionada al funcionamiento del Comedor/Merendero.
        espacio (OneToOneField): Información relacionada al espacio físico del Comedor/Merendero.
        colaboradores (OneToOneField): Información relacionada a las personas que realizan tareas en el Comedor/Merendero/Merendero/Merendero.
        recursos (OneToOneField): Información relacionada a las fuentes de recursos del Comedor/Merendero.
        compras (OneToOneField): Información relacionada a la realización de compras para abastecer el Comedor/Merendero.
    """

    gestionar_uid = models.CharField(max_length=255, unique=True, blank=True)

    comedor = models.ForeignKey(
        to=Comedor,
        on_delete=models.CASCADE,
    )
    relevador = models.CharField(max_length=255, blank=True)
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
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["comedor"]),
        ]
        unique_together = [["comedor", "fecha_visita"]]
        verbose_name = "Relevamiento"
        verbose_name_plural = "Relevamientos"


class Observacion(models.Model):
    """
    Modelo que representa una observación realizada en un Comedor/Merendero.
    """

    observador = models.CharField(max_length=255, blank=True)
    comedor = models.ForeignKey(
        to=Comedor,
        on_delete=models.CASCADE,
        blank=True,
    )
    fecha_visita = models.DateTimeField(default=timezone.now, blank=True)
    observacion = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=["comedor"]),
        ]
        unique_together = [["comedor", "fecha_visita"]]
        verbose_name = "Observacion"
        verbose_name_plural = "Observaciones"
