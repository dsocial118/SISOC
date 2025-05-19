from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from configuraciones.models import Municipio, Provincia
from configuraciones.models import Localidad
from configuraciones.models import Sexo
from organizaciones.models import Organizacion
from ciudadanos.models import EstadoIntervencion
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
        nombre (CharField): Nombre del comedor.
        organizacion (ForeignKey): Referencia a la organización asociada (opcional).
        programa (ForeignKey): Referencia al programa asociado (opcional).
        id_externo (IntegerField): Identificador externo del comedor (opcional).
        codigo_de_proyecto (CharField): Código de proyecto asociado al comedor (opcional).
        comienzo (IntegerField): Año en que comenzó a funcionar el comedor (opcional, entre 1900 y el año actual).
        tipocomedor (ForeignKey): Tipo de comedor (opcional).
        dupla (ForeignKey): Dupla técnica asociada (opcional).
        estado (CharField): Estado actual del comedor. Opciones: "Sin Ingreso" o "Asignado a Dupla Técnica".
        calle (CharField): Nombre de la calle (opcional).
        numero (PositiveIntegerField): Número de la calle (opcional).
        piso (CharField): Piso (opcional).
        departamento (CharField): Departamento (opcional).
        manzana (CharField): Manzana (opcional).
        lote (CharField): Lote (opcional).
        entre_calle_1 (CharField): Primera calle transversal (opcional).
        entre_calle_2 (CharField): Segunda calle transversal (opcional).
        latitud (FloatField): Coordenada de latitud (opcional, entre -90 y 90).
        longitud (FloatField): Coordenada de longitud (opcional, entre -180 y 180).
        provincia (ForeignKey): Provincia donde se encuentra el comedor (opcional).
        municipio (ForeignKey): Municipio (opcional).
        localidad (ForeignKey): Localidad (opcional).
        partido (CharField): Partido o distrito (opcional).
        barrio (CharField): Barrio (opcional).
        codigo_postal (IntegerField): Código postal (opcional, de 4 a 6 dígitos).
        referente (ForeignKey): Persona referente del comedor (opcional).
        foto_legajo (ImageField): Campo para subir una foto o documento (opcional).
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

    calle = models.CharField(max_length=255, blank=True, null=True)
    numero = models.PositiveIntegerField(blank=True, null=True)
    piso = models.CharField(max_length=255, blank=True, null=True)
    departamento = models.CharField(max_length=255, blank=True, null=True)
    manzana = models.CharField(max_length=255, blank=True, null=True)
    lote = models.CharField(max_length=255, blank=True, null=True)
    entre_calle_1 = models.CharField(max_length=255, blank=True, null=True)
    entre_calle_2 = models.CharField(max_length=255, blank=True, null=True)
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
    """
    Guardado de las intervenciones realizadas a un ciudadano.
    """

    comedor = models.ForeignKey(Comedor, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.ForeignKey(
        EstadoIntervencion, on_delete=models.SET_NULL, default=1, null=True
    )
    observaciones = models.TextField(blank=True, null=True)
    nombre = models.TextField(blank=True, null=True)
    apellido = models.TextField(blank=True, null=True)
    dni = models.IntegerField(blank=True, null=True)
    sexo = models.ForeignKey(Sexo, on_delete=models.SET_NULL, default=1, null=True)

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
