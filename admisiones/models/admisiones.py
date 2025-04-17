from django.db import models
from users.models import User
from comedores.models.comedor import Comedor


class EstadoAdmision(models.Model):
    nombre = models.CharField(max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=["nombre"]),
        ]
        verbose_name = "estadosadmision"
        verbose_name_plural = "estadosadmisiones"


class TipoConvenio(models.Model):
    nombre = models.CharField(max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=["nombre"]),
        ]
        verbose_name = "tipoconvenio"
        verbose_name_plural = "tiposconvenios"


class Admision(models.Model):
    comedor = models.ForeignKey(Comedor, on_delete=models.SET_NULL, null=True)
    estado = models.ForeignKey(EstadoAdmision, on_delete=models.SET_NULL, null=True)
    tipo_convenio = models.ForeignKey(
        TipoConvenio, on_delete=models.SET_NULL, null=True
    )
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    modificado = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["comedor"]),
        ]
        verbose_name = "admisiontecnico"
        verbose_name_plural = "admisionestecnicos"
        ordering = ["-creado"]


class TipoDocumentacion(models.Model):
    """
    Opciones de tipos de documentación asociadas a una admisión.
    """

    nombre = models.CharField(max_length=255, unique=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de Documentación"
        verbose_name_plural = "Tipos de Documentación"
        ordering = ["nombre"]


class Documentacion(models.Model):
    nombre = models.CharField(max_length=255)
    tipo = models.ForeignKey(TipoDocumentacion, on_delete=models.SET_NULL, null=True)
    convenios = models.ManyToManyField("TipoConvenio", blank=True)

    def __str__(self):
        return str(self.nombre) if self.nombre else "Sin nombre"


class ArchivoAdmision(models.Model):
    admision = models.ForeignKey(Admision, on_delete=models.CASCADE)
    documentacion = models.ForeignKey(Documentacion, on_delete=models.CASCADE)
    archivo = models.FileField(
        upload_to="comedor/admisiones_archivos/", null=True, blank=True
    )
    estado = models.CharField(
        max_length=20,
        choices=[("pendiente", "Pendiente"), ("validar", "A Validar")],
        default="pendiente",
    )

    def __str__(self):
        return f"{self.admision.id} - {self.documentacion.nombre}"


class DuplaContacto(models.Model):
    comedor = models.ForeignKey(Comedor, on_delete=models.SET_NULL, null=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha = models.DateField()
    tipo = models.CharField(
        max_length=20,
        choices=[("whatsapp", "Whatsapp"), ("email", "Email"), ("llamada", "Llamada")],
        blank=False,
        null=False,
    )
    observaciones = models.TextField()
