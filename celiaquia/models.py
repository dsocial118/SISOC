from django.db import models
from django.contrib.auth import get_user_model
from ciudadanos.models import Ciudadano

from django.contrib.auth.models import User


# Estados dinámicos del Expediente
class EstadoExpediente(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Estado del Expediente"
        verbose_name_plural = "Estados del Expediente"

    def __str__(self):
        return self.nombre

    def display_name(self):
        # quita guiones bajos y capitaliza
        return self.nombre.replace("_", " ").capitalize()


# Estados dinámicos del Legajo dentro de un expediente
class EstadoLegajo(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Estado del Legajo"
        verbose_name_plural = "Estados del Legajo"

    def __str__(self):
        return self.nombre


# Catálogo dinámico de organismos de cruce
class Organismo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Organismo de Cruce"
        verbose_name_plural = "Organismos de Cruce"

    def __str__(self):
        return self.nombre


# Catálogo dinámico de tipos de cruce (aprobado/rechazado)
class TipoCruce(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Tipo de Cruce"
        verbose_name_plural = "Tipos de Cruce"

    def __str__(self):
        return self.nombre


# Expediente principal
class Expediente(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
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

    class Meta:
        verbose_name = "Expediente"
        verbose_name_plural = "Expedientes"

    def __str__(self):
        return f"{self.codigo} - {self.usuario_provincia.username}"


# Relación entre Expediente y Ciudadano (Legajo)
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
    creado_en = models.DateTimeField(auto_now_add=True)
    modificado_en = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("expediente", "ciudadano")
        verbose_name = "Expediente Ciudadano"
        verbose_name_plural = "Expedientes Ciudadano"

    def __str__(self):
        return f"{self.ciudadano.documento} - {self.ciudadano.nombre} {self.ciudadano.apellido}"


# Asignación de técnico a Expediente
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


# Archivos de cruce cargados para el Expediente
class ArchivoCruce(models.Model):
    expediente = models.ForeignKey(
        Expediente, on_delete=models.CASCADE, related_name="archivos_cruce"
    )
    organismo = models.ForeignKey(
        Organismo, on_delete=models.PROTECT, related_name="archivos_cruce"
    )
    tipo = models.ForeignKey(
        TipoCruce, on_delete=models.PROTECT, related_name="archivos_cruce"
    )
    archivo = models.FileField(upload_to="expedientes/cruces/")
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Archivo de Cruce"
        verbose_name_plural = "Archivos de Cruce"

    def __str__(self):
        return f"{self.organismo.nombre} - {self.tipo.nombre}"


# Resultado de cruce para cada ciudadano dentro del Expediente
class ResultadoCruce(models.Model):
    expediente = models.ForeignKey(
        Expediente, on_delete=models.CASCADE, related_name="resultados_cruce"
    )
    expediente_ciudadano = models.ForeignKey(
        ExpedienteCiudadano, on_delete=models.CASCADE, related_name="resultados_cruce"
    )
    organismo = models.ForeignKey(
        Organismo, on_delete=models.PROTECT, related_name="resultados_cruce"
    )
    estado = models.ForeignKey(
        TipoCruce, on_delete=models.PROTECT, related_name="resultados_cruce"
    )
    motivo_rechazo = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Resultado de Cruce"
        verbose_name_plural = "Resultados de Cruce"

    def __str__(self):
        return f"{self.expediente_ciudadano.ciudadano.documento} - {self.organismo.nombre} - {self.estado.nombre}"


# Informe y cierre de pago
class InformePago(models.Model):
    expediente = models.OneToOneField(
        Expediente, on_delete=models.CASCADE, related_name="informe_pago"
    )
    tecnico = models.ForeignKey(User, on_delete=models.PROTECT)
    fecha_pago = models.DateField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Informe de Pago"
        verbose_name_plural = "Informes de Pago"

    def __str__(self):
        return f"Pago {self.expediente.codigo} - {self.monto}"
