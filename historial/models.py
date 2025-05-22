from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


class Historial(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    accion = models.CharField(max_length=255)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)
    objeto = GenericForeignKey("content_type", "object_id")

    diferencias = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"[{self.fecha}] - Usuario: {self.usuario} - Accion: {self.accion} - Modelo: {self.content_type} - Instancia: {self.object_id}"

    class Meta:
        verbose_name = "Historial"
        verbose_name_plural = "Historiales"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["fecha"]),
            models.Index(fields=["usuario"]),
            models.Index(fields=["accion"]),
            models.Index(fields=["content_type"]),
            models.Index(fields=["object_id"]),
        ]
