from django.conf import settings
from django.db import models


class Acompanamiento(models.Model):
    ESTADO_ACTIVO = "activo"
    ESTADO_CERRADO = "cerrado"
    ESTADO_FINALIZADO = "finalizado"

    # El cierre de la admisión gana sobre la finalización: si un acompañamiento
    # finalizado luego recibe un forzar cierre, el cierre es el hecho posterior.
    ESTADOS = [
        (ESTADO_ACTIVO, "Activo"),
        (ESTADO_CERRADO, "Cerrado"),
        (ESTADO_FINALIZADO, "Finalizado"),
    ]

    admision = models.OneToOneField(
        "admisiones.Admision",
        on_delete=models.CASCADE,
        related_name="acompanamiento",
    )
    nro_convenio = models.CharField(max_length=100, blank=True, default="")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_finalizado = models.DateTimeField(
        "Fecha de finalización del acompañamiento",
        null=True,
        blank=True,
    )
    finalizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acompanamientos_finalizados",
        verbose_name="Finalizado por",
    )

    def __str__(self):
        return f"Acompañamiento - Conv. {self.nro_convenio}"

    @property
    def finalizado(self):
        """True si se marcó la finalización del plazo de ejecución del convenio."""
        return self.fecha_finalizado is not None

    @property
    def cerrado(self):
        """True si la admisión fue inactivada (forzar cierre, descarte, etc.)."""
        return not self.admision.activa

    @property
    def puede_finalizarse(self):
        """La finalización solo aplica sobre un acompañamiento vigente.

        No debe ofrecerse si la admisión ya fue inactivada (forzar cierre) ni si
        el acompañamiento ya fue finalizado.
        """
        return self.admision.activa and not self.finalizado

    @property
    def es_gestionable(self):
        """False cuando el acompañamiento ya no admite operaciones en SISOC."""
        return self.admision.activa and not self.finalizado

    @property
    def estado(self):
        """Estado del acompañamiento para etiquetas y filtros del listado."""
        if self.cerrado:
            return self.ESTADO_CERRADO
        if self.finalizado:
            return self.ESTADO_FINALIZADO
        return self.ESTADO_ACTIVO

    @property
    def estado_display(self):
        return dict(self.ESTADOS).get(self.estado, self.estado)


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
