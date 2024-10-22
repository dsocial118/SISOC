from datetime import date  # pylint: disable=too-many-lines

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from multiselectfield import MultiSelectField
from usuarios.models import User, Usuarios

class LegajosProvincias(models.Model):
    """Modelo para las provincias de los legajos."""
    nombre = models.CharField(max_length=50)
    abreviatura = models.CharField(max_length=10)
    poblacion = models.PositiveIntegerField()
    porcentaje_pobreza = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    poblacion_economicamente_activa = models.PositiveIntegerField()
    porcentaje_empleo = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    porcentaje_educacion_incompleta_obligatoria = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    porcentaje_primaria_incompleta = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    porcentaje_secundaria_incompleta = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    cantidad_de_beneficiarios_paz = models.PositiveIntegerField()
    porcentaje_paz = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    cantidad_de_expendientes = models.PositiveIntegerField()
    agroindustria_alimentos = models.BooleanField()
    agroindustria_ganaderia = models.BooleanField()
    agroindustria_agricultura_familiar = models.BooleanField()
    agroindustria_pesca = models.BooleanField()
    agroindustria_forestal = models.BooleanField()
    agroindustria_manufactura = models.BooleanField()

    oficios_carpinteria = models.BooleanField()
    oficios_electicista = models.BooleanField()
    oficios_mecanica = models.BooleanField()
    oficios_herreria = models.BooleanField()
    oficios_jardineria = models.BooleanField()
    oficios_gastronomico = models.BooleanField()
    oficios_logistica = models.BooleanField()
    oficios_textil = models.BooleanField()
    oficios_soldador = models.BooleanField()
    oficios_plomeria = models.BooleanField()
    oficios_albanileria = models.BooleanField()
    oficios_panaderia = models.BooleanField()
    oficios_auxiliar_salud = models.BooleanField()

    economia_circular_ener_renovable = models.BooleanField()
    economia_circular_reciclaje = models.BooleanField()

    tecnologia_software_soporte_tecnico = models.BooleanField()
    tecnologia_software_infraestructura_informatica = models.BooleanField()
    tecnologia_software_desarollo_software = models.BooleanField()
    tecnologia_software_instalaciones_tecnicas = models.BooleanField()
    tecnologia_software_infraestructura_digital = models.BooleanField()

    servicios_lamapara = models.BooleanField()
    servicios_transporte = models.BooleanField()
    servicios_cuidados = models.BooleanField()
    servicios_salud = models.BooleanField()
    servicios_educacion = models.BooleanField()

    energia = models.BooleanField()
    mineria = models.BooleanField()
    industria_petroquimica = models.BooleanField()

    class Meta:
        verbose_name = "Provincia"
        verbose_name_plural = "Provincias"

    def __str__(self):
        return f"{self.nombre}"
    
class Presupuesto (models.Model):
    """Modelo para los presupuestos de los legajos."""
    provincia = models.ForeignKey(LegajosProvincias, on_delete=models.CASCADE)
    anio = models.PositiveIntegerField()
    presupuesto_total = models.PositiveIntegerField()
    presupuesto_linea_socio_productivo = models.PositiveIntegerField()
    presupuesto_linea_formativo = models.PositiveIntegerField()
    class Meta:
        verbose_name = "Presupuesto"
        verbose_name_plural = "Presupuestos"

    def __str__(self):
        return f"{self.provincia} - {self.anio}"

class Proyectos (models.Model):
    """Modelo para los proyectos de los legajos."""
    provincia = models.ForeignKey(LegajosProvincias, on_delete=models.CASCADE)
    proyecto = models.CharField(max_length=50)
    presupuesto = models.ForeignKey(Presupuesto, on_delete=models.CASCADE)
    class Meta:
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"

    def __str__(self):
        return f"{self.provincia} - {self.proyecto}"
    
class DocumentacionArchivos (models.Model):
    """Modelo para los archivos de documentación de los legajos."""
    provincia = models.ForeignKey(LegajosProvincias, on_delete=models.CASCADE)
    proyecto = models.ForeignKey(Proyectos, on_delete=models.CASCADE)
    fecha_creacion = models.DateField()
    fecha_modificacion = models.DateField()
    archivo = models.FileField(upload_to="documentacion/")
    class Meta:
        verbose_name = "Archivo"
        verbose_name_plural = "Archivos"

    def __str__(self):
        return f"{self.provincia} - {self.archivo}"

class HistorialPresupuesto (models.Model):
    """Modelo para el historial de los presupuestos de los legajos."""
    provincia = models.ForeignKey(LegajosProvincias, on_delete=models.CASCADE)
    anio = models.PositiveIntegerField()
    presupuesto_total = models.PositiveIntegerField()
    presupuesto_linea_socio_productivo = models.PositiveIntegerField()
    presupuesto_linea_formativo = models.PositiveIntegerField()
    class Meta:
        verbose_name = "Historial de Presupuesto"
        verbose_name_plural = "Historial de Presupuestos"

    def __str__(self):
        return f"{self.provincia} - {self.anio}"
