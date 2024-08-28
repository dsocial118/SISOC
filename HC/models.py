from django.db import models


class Persona(models.Model):
    documentoNumero: models.IntegerField(null=True, blank=True)
    documentoTipo: models.CharField(max_length=250, unique=True)
    genero: models.CharField(max_length=250, unique=True)
    personaCodigo: models.IntegerField(null=True, blank=True)
    creado: models.DateField(auto_now_add=True)


class Indicadores(models.Model):
    value: models.BooleanField(default=True)
    ultimoTurno: models.DateTimeField(null=True, blank=True)
    turnoCodigo: models.IntegerField(null=True, blank=True)
    creado: models.DateField(auto_now_add=True)


class ProblemasMentales(models.Model):
    value: models.BooleanField(default=True)
    creado: models.DateField(auto_now_add=True)


class EnfermedadCatastrofica(models.Model):
    value: models.BooleanField(default=True)
    creado: models.DateField(auto_now_add=True)


class ControlMedico(models.Model):
    cantidad: models.IntegerField(null=True, blank=True)
    ultimoTurno: models.DateTimeField(null=True, blank=True)
    turnoCodigo: models.IntegerField(null=True, blank=True)
    creado: models.DateField(auto_now_add=True)


class CentroMedico(models.Model):
    nombre: models.CharField(max_length=250, unique=True)
    ultimoTurno: models.DateTimeField
    turnocCodigo: models.IntegerField(null=True, blank=True)
    creado: models.DateField(auto_now_add=True)


class Turno(models.Model):
    FechaTurno: models.DateTimeField(null=True, blank=True)
    Especialidad: models.CharField(max_length=250, unique=True)
    Asistencia: models.BooleanField(default=True)
    Reprogramado: models.BooleanField(default=True)
    FechaReprogramacion: models.DateTimeField(null=True, blank=True)
    turnoCodigo: models.IntegerField(null=True, blank=True)
    creado: models.DateField(auto_now_add=True)


class Embarazo(models.Model):
    value: models.BooleanField(default=True)
    EsMenor: models.BooleanField(default=True)
    Riesgo: models.BooleanField(default=True)
    CantidadControles: models.IntegerField(null=True, blank=True)
    ultimoTurno: models.DateTimeField(null=True, blank=True)
    turnoCodigo: models.IntegerField(null=True, blank=True)
    creado: models.DateField(auto_now_add=True)


class ContrLPediatrico(models.Model):
    value: models.BooleanField(default=True)
    cantidad: models.IntegerField(null=True, blank=True)
    ultimoTurno: models.DateTimeField(null=True, blank=True)
    turnoCodigo: models.IntegerField(null=True, blank=True)
    creado: models.DateField(auto_now_add=True)


class ControlDental(models.Model):
    value: models.BooleanField(default=True)
    cantidad: models.IntegerField(null=True, blank=True)
    ultimoTurno: models.DateTimeField(null=True, blank=True)
    turnoCodigo: models.IntegerField(null=True, blank=True)
    creado: models.DateField(auto_now_add=True)


class ControlOftalmologico(models.Model):
    value: models.BooleanField(default=True)
    cantidad: models.IntegerField(null=True, blank=True)
    ultimoTurno: models.DateTimeField(null=True, blank=True)
    turnoCodigo: models.IntegerField(null=True, blank=True)
    creado: models.DateField(auto_now_add=True)


class ControlGynecologico(models.Model):
    value: models.BooleanField(default=True)
    cantidad: models.IntegerField(null=True, blank=True)
    ultimoTurno: models.DateTimeField(null=True, blank=True)
    turnoCodigo: models.IntegerField(null=True, blank=True)
    creado: models.DateField(auto_now_add=True)
