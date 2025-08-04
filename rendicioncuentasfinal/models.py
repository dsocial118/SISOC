from django.db import models
from django.utils import timezone

from comedores.models import Comedor


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
        return self.estado.nombre == "En análisis"
        # return self.tipo.personalizado and self.estado.nombre == "En análisis"

    class Meta:
        indexes = [
            models.Index(fields=["rendicion_final"]),
        ]
        unique_together = [["rendicion_final", "tipo"]]
        verbose_name = "Documento de Rendición"
        verbose_name_plural = "Documentos de Rendición"


# Create your models here.
