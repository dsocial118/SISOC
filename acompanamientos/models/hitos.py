from django.db import models
from comedores.models.comedor import Comedor
from django.utils import timezone

class Hitos(models.Model):
    comedor = models.OneToOneField(Comedor, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(default=timezone.now, blank=True)
    retiro_tarjeta = models.BooleanField(default=False, verbose_name="Retiro de Tarjeta")
    habilitacion_tarjeta = models.BooleanField(default=False, verbose_name="Habilitación de Tarjeta")
    alta_usuario_plataforma = models.BooleanField(default=False, verbose_name="Alta de usuario en Plataforma")
    capacitacion_realizada = models.BooleanField(default=False, verbose_name="Capacitación realizada")
    notificacion_acreditacion_1 = models.BooleanField(default=False, verbose_name="Notificación de primera acreditación")
    notificacion_acreditacion_2 = models.BooleanField(default=False, verbose_name="Notificación de acreditación mes 2")
    notificacion_acreditacion_3 = models.BooleanField(default=False, verbose_name="Notificación de acreditación mes 3")
    notificacion_acreditacion_4 = models.BooleanField(default=False, verbose_name="Notificación de acreditación mes 4")
    notificacion_acreditacion_5 = models.BooleanField(default=False, verbose_name="Notificación de acreditación mes 5")
    notificacion_acreditacion_6 = models.BooleanField(default=False, verbose_name="Notificación de acreditación mes 6")
    nomina_entregada_inicial = models.BooleanField(default=False, verbose_name="Nómina entregada inicial")
    nomina_alta_baja_2 = models.BooleanField(default=False, verbose_name="Nómina Alta/baja mes 2")
    nomina_alta_baja_3 = models.BooleanField(default=False, verbose_name="Nómina Alta/baja mes 3")
    nomina_alta_baja_4 = models.BooleanField(default=False, verbose_name="Nómina Alta/baja mes 4")
    nomina_alta_baja_5 = models.BooleanField(default=False, verbose_name="Nómina Alta/baja mes 5")
    nomina_alta_baja_6 = models.BooleanField(default=False, verbose_name="Nómina Alta/baja mes 6")
    certificado_prestaciones_1 = models.BooleanField(default=False, verbose_name="Certificado mensual de prestaciones mes: 1")
    certificado_prestaciones_2 = models.BooleanField(default=False, verbose_name="Certificado mensual de prestaciones mes: 2")
    certificado_prestaciones_3 = models.BooleanField(default=False, verbose_name="Certificado mensual de prestaciones mes: 3")
    certificado_prestaciones_4 = models.BooleanField(default=False, verbose_name="Certificado mensual de prestaciones mes: 4")
    certificado_prestaciones_5 = models.BooleanField(default=False, verbose_name="Certificado mensual de prestaciones mes: 5")
    certificado_prestaciones_6 = models.BooleanField(default=False, verbose_name="Certificado mensual de prestaciones mes: 6")

    def __str__(self):
        return f"Hito - {self.comedor.nombre} - {self.fecha}"
    

class CompararHitosIntervenciones(models.Model):
    intervencion = models.CharField(max_length=255)
    subintervencion = models.CharField(max_length=255)
    hito = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.intervencion} - {self.subintervencion} - {self.hito}"