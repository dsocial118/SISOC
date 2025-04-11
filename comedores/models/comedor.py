from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from configuraciones.models import Municipio, Provincia
from configuraciones.models import Localidad
from configuraciones.models import Sexo
from organizaciones.models import Organizacion
from users.models import User


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
    Modelo que representa a un referente, en algun futuro se migrara a Legajo.

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
    Modelo que representa un Comedor/Merendero.

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
        to=Municipio, on_delete=models.PROTECT, null=True, blank=True
    )
    localidad = models.ForeignKey(
        to=Localidad, on_delete=models.PROTECT, null=True, blank=True
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


class Intervencion(models.Model):
    """
    Guardado de las intervenciones realizadas a un legajo.
    """

    fk_comedor = models.ForeignKey(Comedor, on_delete=models.SET_NULL, null=True)
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
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Intervencion"
        verbose_name_plural = "Intervenciones"
        indexes = [models.Index(fields=["fk_comedor"])]


class Nomina(models.Model):
    """
    Guardado de las intervenciones realizadas a un legajo.
    """

    fk_comedor = models.ForeignKey(Comedor, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    fk_estado = models.ForeignKey(
        EstadosIntervencion, on_delete=models.SET_NULL, default=1, null=True
    )
    observaciones = models.TextField(blank=True, null=True)
    nombre = models.TextField(blank=True, null=True)
    apellido = models.TextField(blank=True, null=True)
    dni = models.IntegerField(blank=True, null=True)
    fk_sexo = models.ForeignKey(Sexo, on_delete=models.SET_NULL, default=1, null=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Nomina"
        verbose_name_plural = "Nominas"
        indexes = [models.Index(fields=["fk_comedor"])]


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
