from django.db import models
from comedores.models import Comedor


class InformacionRelevante(models.Model):
    comedor = models.OneToOneField(Comedor, on_delete=models.CASCADE)
    numero_expediente = models.CharField(max_length=255)
    numero_resolucion = models.CharField(max_length=255)
    vencimiento_mandato = models.DateField()
    if_relevamiento = models.CharField(max_length=255)

    def __str__(self):
        return f"Información Relevante - {self.comedor.nombre}"
