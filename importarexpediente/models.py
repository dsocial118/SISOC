from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ImportJob(models.Model):
    """
    Registro de una carga de archivo (CSV/Excel).
    Guarda metadata y totales del CRUD ejecutado.
    """

    archivo_nombre = models.CharField(max_length=255)
    archivo_size = models.PositiveIntegerField(blank=True, null=True)
    iniciado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    estado = models.CharField(
        max_length=20,
        choices=[
            ("pendiente", "Pendiente"),
            ("procesando", "Procesando"),
            ("finalizado", "Finalizado"),
            ("fallido", "Fallido"),
        ],
        default="pendiente",
    )

    # Totales
    total_registros = models.PositiveIntegerField(default=0)
    creados = models.PositiveIntegerField(default=0)
    actualizados = models.PositiveIntegerField(default=0)
    omitidos = models.PositiveIntegerField(default=0)
    errores = models.PositiveIntegerField(default=0)

    # Config de import
    delimitador = models.CharField(max_length=5, default=",")
    tiene_header = models.BooleanField(default=True)
    notas = models.TextField(blank=True, null=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Import #{self.pk} - {self.archivo_nombre} ({self.estado})"


class ImportRowLog(models.Model):
    """
    Detalle por fila procesada.
    Permite auditar el CRUD por cada registro del archivo.
    """

    job = models.ForeignKey(ImportJob, on_delete=models.CASCADE, related_name="rows")
    linea_numero = models.PositiveIntegerField()
    raw_data = models.JSONField(blank=True, null=True)

    accion = models.CharField(
        max_length=20,
        choices=[
            ("crear", "Crear"),
            ("actualizar", "Actualizar"),
            ("omitir", "Omitir"),
            ("error", "Error"),
        ],
    )

    modelo = models.CharField(max_length=100, default="expedientespagos.ExpedientePago")
    objeto_pk = models.CharField(max_length=50, blank=True, null=True)

    mensaje = models.TextField(blank=True, null=True)  # motivo de omisión o error
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["job", "linea_numero"]),
            models.Index(fields=["accion"]),
        ]

    def __str__(self):
        return f"Job {self.job_id} - Línea {self.linea_numero} - {self.accion}"