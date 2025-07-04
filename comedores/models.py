from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone

from configuraciones.models import Municipio, Provincia
from configuraciones.models import Localidad
from organizaciones.models import Organizacion
from ciudadanos.models import Ciudadano, EstadoIntervencion
from duplas.models import Dupla


class TipoDeComedor(models.Model):
    """
    Opciones de tipos para un Comedor/Merendero/Punto de entrega
    """

    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        ordering = ["id"]
        verbose_name = "Tipo de comedor"
        verbose_name_plural = "Tipos de comedor"


class Referente(models.Model):
    """
    Modelo que representa a un referente, en algun futuro se migrara a Ciudadano.

    Atributos:
        nombre (CharField): Nombre del referente.
        apellido (CharField): Apellido del referente.
        mail (EmailField): Dirección de correo electrónico única del referente.
        celular (BigIntegerField): Número único del referente.
        documento (BigIntegerField): Documento único del referente.
        funcion (CharField): Función del referente.
    """

    nombre = models.CharField(
        max_length=255, verbose_name="Nombre del referente", blank=True, null=True
    )
    apellido = models.CharField(
        max_length=255, verbose_name="Apellido del referente", blank=True, null=True
    )
    mail = models.EmailField(verbose_name="Mail del referente", blank=True, null=True)
    celular = models.BigIntegerField(
        verbose_name="Celular del referente", blank=True, null=True
    )
    documento = models.BigIntegerField(
        verbose_name="Documento del referente", blank=True, null=True
    )
    funcion = models.CharField(
        verbose_name="Funcion del referente", max_length=255, blank=True, null=True
    )

    class Meta:
        verbose_name = "Referente"
        verbose_name_plural = "Referentes"


class Programas(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        ordering = ["id"]
        verbose_name = "Programa"
        verbose_name_plural = "Programas"


class Comedor(models.Model):
    """
    Representa una Comedor/Merendero.

    Atributos:
        nombre (CharField): Nombre del Comedor/Merendero.
        comienzo (IntegerField): Año de inicio de la actividad del Comedor/Merendero.
        tipocomedor (ForeignKey): Tipo de Comedor/Merendero.
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
        dupla (ForeignKey): Dúpla del Comedor/Merendero.
    """

    nombre = models.CharField(
        max_length=255,
    )
    organizacion = models.ForeignKey(
        to=Organizacion, blank=True, null=True, on_delete=models.PROTECT
    )
    programa = models.ForeignKey(
        to=Programas, blank=True, null=True, on_delete=models.PROTECT
    )
    id_externo = models.IntegerField(
        verbose_name="Id Externo",
        blank=True,
        null=True,
    )
    codigo_de_proyecto = models.CharField(
        max_length=255,
        verbose_name="Código de Proyecto",
        blank=True,
        null=True,
    )
    comienzo = models.IntegerField(
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(timezone.now().year),
        ],
        verbose_name="Año en el que comenzó a funcionar",
        blank=True,
        null=True,
    )
    tipocomedor = models.ForeignKey(
        to=TipoDeComedor, on_delete=models.PROTECT, null=True, blank=True
    )
    dupla = models.ForeignKey(
        to=Dupla,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    # Se agrego el estado del comedor para poder filtrar los que no tienen ingreso
    # y los que tienen ingreso asignado a dupla tecnica
    estadosComedor = [
        ("Sin Ingreso", "Sin Ingreso"),
        ("Asignado a Dupla Técnica", "Asignado a Dupla Técnica"),
    ]
    estado = models.CharField(
        choices=estadosComedor,
        max_length=255,
        blank=True,
        null=True,
        default="Sin Ingreso",
    )

    direccion_validator = RegexValidator(
        regex=r"^[a-zA-Z0-9\s.,áéíóúÁÉÍÓÚñÑ-]*$",
        message="La dirección solo puede contener letras, números, espacios y los caracteres ., -",
    )

    calle = models.CharField(
        max_length=255, blank=True, null=True, validators=[direccion_validator]
    )
    numero = models.PositiveIntegerField(blank=True, null=True)
    piso = models.CharField(
        max_length=255, blank=True, null=True, validators=[direccion_validator]
    )
    departamento = models.CharField(
        max_length=255, blank=True, null=True, validators=[direccion_validator]
    )
    manzana = models.CharField(
        max_length=255, blank=True, null=True, validators=[direccion_validator]
    )
    lote = models.CharField(
        max_length=255, blank=True, null=True, validators=[direccion_validator]
    )
    entre_calle_1 = models.CharField(
        max_length=255, blank=True, null=True, validators=[direccion_validator]
    )
    entre_calle_2 = models.CharField(
        max_length=255, blank=True, null=True, validators=[direccion_validator]
    )
    latitud = models.FloatField(
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        blank=True,
        null=True,
    )
    longitud = models.FloatField(
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        blank=True,
        null=True,
    )
    provincia = models.ForeignKey(to=Provincia, on_delete=models.PROTECT, null=True)
    municipio = models.ForeignKey(
        to=Municipio, on_delete=models.SET_NULL, null=True, blank=True
    )
    localidad = models.ForeignKey(
        to=Localidad, on_delete=models.SET_NULL, null=True, blank=True
    )
    partido = models.CharField(max_length=255, null=True, blank=True)
    barrio = models.CharField(max_length=255, null=True, blank=True)
    codigo_postal = models.IntegerField(
        validators=[
            MinValueValidator(1000),
            MaxValueValidator(999999),
        ],  # Entre 4 a 6 digitos
        blank=True,
        null=True,
    )
    referente = models.ForeignKey(
        to=Referente, on_delete=models.SET_NULL, null=True, blank=True
    )
    foto_legajo = models.ImageField(upload_to="comedor/", blank=True, null=True)

    def __str__(self) -> str:
        return str(self.nombre)

    class Meta:
        indexes = [
            models.Index(fields=["nombre"]),
        ]
        verbose_name = "comedor"
        verbose_name_plural = "comedores"
        ordering = ["nombre"]


class Nomina(models.Model):
    comedor = models.ForeignKey("Comedor", on_delete=models.SET_NULL, null=True)
    ciudadano = models.ForeignKey(
        Ciudadano,
        on_delete=models.CASCADE,
        related_name="nominas",
        null=True,
        blank=True,
    )
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.ForeignKey(EstadoIntervencion, on_delete=models.SET_NULL, null=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Nomina"
        verbose_name_plural = "Nominas"
        indexes = [models.Index(fields=["comedor"])]


class ImagenComedor(models.Model):
    comedor = models.ForeignKey(
        Comedor, on_delete=models.CASCADE, related_name="imagenes"
    )
    imagen = models.ImageField(upload_to="comedor/")

    def __str__(self):
        return f"Imagen de {self.comedor.nombre}"


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


class ValorComida(models.Model):
    tipo = models.CharField(max_length=50)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField()


class CategoriaComedor(models.Model):
    nombre = models.CharField(max_length=255)
    puntuacion_min = models.IntegerField()
    puntuacion_max = models.IntegerField()

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Categoria de Comedor"
        verbose_name_plural = "Categorias de Comedor"
