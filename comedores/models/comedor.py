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


class RendicionCuentasFinal(models.Model):
    """
    Modelo que representa una rendición de cuentas final de un Comedor/Merendero.
    Será donde se conecten todos los documentos adjuntos.
    Atributos:
        comedor (ForeignKey): Referencia al modelo Comedor, indicando a qué comedor pertenece la rendición.
        fisicamente_presentada (BooleanField): Indica si la rendición física fue presentada y aceptada en PAC.
    Métodos:
        add_documento_personalizado(nombre):
            Crea y asocia un documento personalizado a la rendición final, generando el tipo de documento si no existe.
    """

    comedor = models.ForeignKey(
        to=Comedor, on_delete=models.CASCADE, blank=True, related_name="rendiciones"
    )
    fisicamente_presentada = models.BooleanField(
        default=False,
        verbose_name="Rendición física presentada y aceptada en PAC",
    )

    def add_documento_personalizado(self, nombre):
        tipo_custom, _created = TipoDocumentoRendicionFinal.objects.get_or_create(
            nombre=nombre, personalizado=True
        )

        return DocumentoRendicionFinal.objects.create(
            rendicion_final=self, tipo=tipo_custom, fecha_modificacion=timezone.now()
        )

    class Meta:
        verbose_name = "Rendición de Cuentas Final"
        verbose_name_plural = "Rendiciones de Cuentas Final"


class EstadoDocumentoRendicionFinal(models.Model):
    """
    Modelo que representa el estado de un documento de rendición final.

    Atributos:
        nombre (CharField): Nombre único que identifica el estado del documento.
    """

    nombre = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = "Estado de Documento"
        verbose_name_plural = "Estados de Documento"


class TipoDocumentoRendicionFinal(models.Model):
    """
    Modelo que representa un tipo de documento utilizado en la rendición final.

    Atributos:
        nombre (CharField): Nombre único que identifica el tipo de documento.
        validador (CharField): Nombre de la persona o área responsable de validar el documento.
            Puede ser 'Dupla', 'Contabilidad', etc. Este campo es opcional y por defecto es 'Dupla'.
        personalizado (BooleanField): Indica si el tipo de documento es creado por un usuario.
    """

    nombre = models.CharField(max_length=255, unique=True)
    validador = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default="Dupla",
        help_text="Quien debe validar el documento. Ej: Dupla, Contabilidad, etc.",
    )
    personalizado = models.BooleanField(
        default=False,
        help_text="Indica si el tipo de documento es creado por un usuario.",
    )

    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documento"


class DocumentoRendicionFinal(models.Model):
    """
    Modelo que representa un documento en la Rendición de Cuentas Final.
    Atributos:
        rendicion_final (ForeignKey): Referencia a la instancia de RendicionCuentasFinal a la que pertenece el documento.
        documento (FileField): Archivo adjunto correspondiente al documento de rendición.
        tipo (ForeignKey): Tipo de documento, relacionado con TipoDocumentoRendicionFinal.
        estado (ForeignKey): Estado actual del documento, relacionado con EstadoDocumentoRendicionFinal.
        observaciones (CharField): Observaciones adicionales sobre el documento (opcional).
        fecha_modificacion (DateTimeField): Fecha y hora de la última modificación del documento.
    """

    rendicion_final = models.ForeignKey(
        to=RendicionCuentasFinal,
        on_delete=models.CASCADE,
        related_name="documentos",
    )
    documento = models.FileField(
        upload_to="rendicion_cuentas_final/", null=True, blank=True
    )
    tipo = models.ForeignKey(
        TipoDocumentoRendicionFinal, on_delete=models.PROTECT, null=True
    )
    estado = models.ForeignKey(
        to=EstadoDocumentoRendicionFinal,
        on_delete=models.PROTECT,
        default=1,
    )
    observaciones = models.CharField(max_length=255, blank=True, null=True)
    fecha_modificacion = models.DateTimeField(null=True, blank=True)

    @property
    def editable(self):
        return self.estado.nombre in {"No presentado", "Subsanar"}

    @property
    def validable(self):
        return self.tipo.validador == "Dupla" and self.estado.nombre == "En análisis"

    @property
    def eliminable(self):
        return self.tipo.personalizado and self.estado.nombre == "En análisis"

    class Meta:
        indexes = [
            models.Index(fields=["rendicion_final"]),
        ]
        unique_together = [["rendicion_final", "tipo"]]
        verbose_name = "Documento de Rendición"
        verbose_name_plural = "Documentos de Rendición"
