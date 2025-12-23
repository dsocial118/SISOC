from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ArchivosImportados(models.Model):
    archivo = models.FileField(upload_to='importados/')
    fecha_subida = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    error = models.TextField(blank=True, null=True)
    id_archivo = models.IntegerField(blank=True, null=True)
    def __str__(self):
        return f"Archivo importado {self.archivo.name} por {self.usuario.username} el {self.fecha_subida}"