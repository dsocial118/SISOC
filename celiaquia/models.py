from django.db import models
from django.contrib.auth import get_user_model
from ciudadanos.models import Ciudadano

User = get_user_model()



class EstadoExpediente(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Estado del Expediente"
        verbose_name_plural = "Estados del Expediente"

    def __str__(self):
        return self.nombre

    def display_name(self):

        return self.nombre.replace("_", " ").capitalize()



class EstadoLegajo(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Estado del Legajo"
        verbose_name_plural = "Estados del Legajo"

    def __str__(self):
        return self.nombre



class Organismo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Organismo de Cruce"
        verbose_name_plural = "Organismos de Cruce"

    def __str__(self):
        return self.nombre



class TipoCruce(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Tipo de Cruce"
        verbose_name_plural = "Tipos de Cruce"

    def __str__(self):
        return self.nombre



class Expediente(models.Model):
    usuario_provincia = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="expedientes_creados"
    )
    usuario_modificador = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="expedientes_modificados",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    estado = models.ForeignKey(
        EstadoExpediente, on_delete=models.PROTECT, related_name="expedientes"
    )
    observaciones = models.TextField(blank=True, null=True)


    excel_masivo = models.FileField(
        upload_to="expedientes/masivos/", null=True, blank=True
    )

    cruce_excel = models.FileField(
        upload_to="expedientes/cruces/", null=True, blank=True
    )
    documento = models.FileField(
        upload_to="expedientes/prd/", null=True, blank=True
    )

    class Meta:
        verbose_name = "Expediente"
        verbose_name_plural = "Expedientes"

    def __str__(self):
        return f"{self.codigo} - {self.usuario_provincia.username}"



class ExpedienteCiudadano(models.Model):
    expediente = models.ForeignKey(
        Expediente, on_delete=models.CASCADE, related_name="expediente_ciudadanos"
    )
    ciudadano = models.ForeignKey(
        Ciudadano, on_delete=models.PROTECT, related_name="expedientes"
    )
    estado = models.ForeignKey(
        EstadoLegajo, on_delete=models.PROTECT, related_name="expediente_ciudadanos"
    )
    archivo = models.FileField(upload_to="legajos/archivos/", null=True, blank=True)


    cruce_ok = models.BooleanField(null=True, blank=True)

    observacion_cruce = models.CharField(max_length=255, null=True, blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    modificado_en = models.DateTimeField(auto_now=True)

    REV_TEC_CHOICES = [
        ("PENDIENTE", "Pendiente"),
        ("APROBADO", "Aprobado por técnico"),
        ("RECHAZADO", "Rechazado por técnico"),
    ]
    revision_tecnico = models.CharField(
        max_length=10, choices=REV_TEC_CHOICES, default="PENDIENTE"
    )
    SINTYS_CHOICES = [
        ("SIN_CRUCE", "Sin cruce"),
        ("MATCH", "Matcheado"),
        ("NO_MATCH", "No matcheado"),
    ]
    resultado_sintys = models.CharField(
        max_length=10, choices=SINTYS_CHOICES, default="SIN_CRUCE"
    )

    class Meta:
        unique_together = ("expediente", "ciudadano")
        verbose_name = "Expediente Ciudadano"
        verbose_name_plural = "Expedientes Ciudadano"

    def __str__(self):
        return f"{self.ciudadano.documento} - {self.ciudadano.nombre} {self.ciudadano.apellido}"



class AsignacionTecnico(models.Model):
    expediente = models.OneToOneField(
        Expediente, on_delete=models.CASCADE, related_name="asignacion_tecnico"
    )
    tecnico = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="expedientes_asignados"
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Asignación de Técnico"
        verbose_name_plural = "Asignaciones de Técnico"

    def __str__(self):
        return f"{self.expediente.codigo} -> {self.tecnico.username}"
