from django.db import models
from django.contrib.auth import get_user_model
from expedientespagos.models import ExpedientePago

User = get_user_model()


class ArchivosImportados(models.Model):
    archivo = models.FileField(upload_to="importados/")
    delimiter = models.CharField(max_length=1, default=",")
    fecha_subida = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    count_errores = models.IntegerField(default=0)
    count_exitos = models.IntegerField(default=0)
    importacion_completada = models.BooleanField(default=False)
    numero_expedinte_pago = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Archivo importado {self.archivo.name} por {self.usuario.username} el {self.fecha_subida}"


class ErroresImportacion(models.Model):
    archivo_importado = models.ForeignKey(
        ArchivosImportados, on_delete=models.DO_NOTHING, related_name="errores"
    )
    fila = models.IntegerField()
    mensaje = models.TextField(default="", blank=True)

    def __str__(self):
        return f"Error en fila {self.fila} del archivo {self.archivo_importado.archivo.name}: {self.mensaje}"


class ExitoImportacion(models.Model):
    archivo_importado = models.ForeignKey(
        ArchivosImportados, on_delete=models.DO_NOTHING, related_name="exitos"
    )
    fila = models.IntegerField()
    mensaje = models.TextField(default="", blank=True)

    def __str__(self):
        return f"Éxito en fila {self.fila} del archivo {self.archivo_importado.archivo.name}: {self.mensaje}"


class RegistroImportado(models.Model):
    exito_importacion = models.ForeignKey(
        ExitoImportacion, on_delete=models.DO_NOTHING, related_name="registros"
    )
    expediente_pago = models.ForeignKey(
        ExpedientePago, on_delete=models.DO_NOTHING, related_name="registros_importados"
    )

    def __str__(self):
        return f"Registro importado con ID de expediente {self.expediente_pago} asociado al éxito en fila {self.exito_importacion.fila}"
