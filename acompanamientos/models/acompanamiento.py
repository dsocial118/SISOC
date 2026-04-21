from django.db import models


class Acompanamiento(models.Model):
    admision = models.OneToOneField(
        "admisiones.Admision",
        on_delete=models.CASCADE,
        related_name="acompanamiento",
    )
    nro_convenio = models.CharField(max_length=100, blank=True, default="")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Acompañamiento - Conv. {self.nro_convenio}"


class InformacionRelevante(models.Model):
    acompanamiento = models.OneToOneField(
        Acompanamiento,
        on_delete=models.CASCADE,
        related_name="informacion_relevante",
    )
    numero_expediente = models.CharField(max_length=255)
    numero_resolucion = models.CharField(max_length=255)
    vencimiento_mandato = models.DateField()
    if_relevamiento = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Información Relevante - {self.acompanamiento}"


# TODO: Cambiar el nombre de esta clase para que no se pise conceptualmente con el de relevamiento
class Prestacion(models.Model):
    acompanamiento = models.ForeignKey(
        Acompanamiento,
        on_delete=models.CASCADE,
        related_name="prestaciones",
    )
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
        return f"Prestación - {self.acompanamiento} - {self.dia}"
