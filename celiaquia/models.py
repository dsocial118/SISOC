from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django import forms



class CargaMasivaForm(forms.Form):
    archivo = forms.FileField(label="Archivo Excel (.xlsx)", required=True)

class EstadoExpediente(models.Model):
    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Estado del Expediente"
        verbose_name_plural = "Estados del Expediente"


class Expediente(models.Model):
    usuario_creador = models.ForeignKey(User, on_delete=models.PROTECT, related_name='expedientes_creados')
    provincia = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.ForeignKey(EstadoExpediente, on_delete=models.PROTECT)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Expediente {self.id} - {self.provincia}"

    class Meta:
        verbose_name = "Expediente"
        verbose_name_plural = "Expedientes"


class PersonaFormulario(models.Model):
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name='personas')
    nombre = models.CharField(max_length=255)
    apellido = models.CharField(max_length=255)
    dni = models.CharField(max_length=20)
    sexo = models.CharField(max_length=10)
    fecha_nacimiento = models.DateField()
    datos_complementarios = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class AsignacionTecnico(models.Model):
    expediente = models.OneToOneField(Expediente, on_delete=models.CASCADE)
    tecnico = models.ForeignKey(User, on_delete=models.PROTECT, related_name='expedientes_asignados')
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Asignado a {self.tecnico.username}"


class ArchivoCruce(models.Model):
    organismo_opciones = [
        ('syntis', 'Syntis'),
        ('salud', 'Salud'),
        ('renaper', 'Renaper'),
    ]
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name='archivos_cruce')
    archivo = models.FileField(upload_to='cruces/')
    organismo = models.CharField(max_length=50, choices=organismo_opciones)
    tipo = models.CharField(max_length=10, choices=[('aprobado', 'Aprobado'), ('rechazado', 'Rechazado')])
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.organismo} - {self.tipo}"

class CargaMasivaForm(forms.Form):
    archivo = forms.FileField(label="Archivo Excel (.xlsx)", required=True)

class ResultadoCruce(models.Model):
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name='resultados')
    dni = models.CharField(max_length=20)
    estado = models.CharField(max_length=10, choices=[('aceptado', 'Aceptado'), ('rechazado', 'Rechazado')])
    motivo_rechazo = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.dni} - {self.estado}"


class InformePago(models.Model):
    expediente = models.OneToOneField(Expediente, on_delete=models.CASCADE)
    tecnico = models.ForeignKey(User, on_delete=models.PROTECT)
    fecha_pago = models.DateField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Pago de Expediente {self.expediente.id}"

    class Meta:
        verbose_name = "Informe de Pago"
        verbose_name_plural = "Informes de Pago"
