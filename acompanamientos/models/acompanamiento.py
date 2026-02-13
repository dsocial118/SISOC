from django.db import models
from comedores.models import Comedor


class InformacionRelevante(models.Model):
    comedor = models.OneToOneField(Comedor, on_delete=models.CASCADE)
    numero_expediente = models.CharField(max_length=255)
    numero_resolucion = models.CharField(max_length=255)
    vencimiento_mandato = models.DateField()
    if_relevamiento = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Información Relevante - {self.comedor.nombre}"


# TODO: Cambiar el nombre de esta clase para que no se pise conceptualmente con el de relevamiento
class Prestacion(models.Model):
    comedor = models.ForeignKey(Comedor, on_delete=models.CASCADE)
    dia = models.CharField(
        max_length=20,
        choices=[
            ("lunes", "Lunes"),
            ("martes", "Martes"),
            ("miercoles", "Miércoles"),
            ("jueves", "Jueves"),
            ("viernes", "Viernes"),
            ("sabado", "Sábado"),
            ("domingo", "Domingo"),
        ],
    )
    desayuno = models.BooleanField(default=False)
    almuerzo = models.BooleanField(default=False)
    merienda = models.BooleanField(default=False)
    cena = models.BooleanField(default=False)

    def __str__(self):
        return f"Prestación - {self.comedor.nombre} - {self.dia}"
