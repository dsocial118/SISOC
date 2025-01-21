from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.forms import ValidationError
from django.utils import timezone

from configuraciones.models import Municipio, Provincia
from configuraciones.models import Localidad, Mes, Dia, Turno
from legajos.models import Sexo
from comedores.models import Referente



class Organizacion(models.Model):
    nombre = models.CharField(max_length=255)
    cuit = models.CharField(max_length=13, unique=True)
    # 
    provincia = models.ForeignKey(to=Provincia, on_delete=models.PROTECT, null=True)
    municipio = models.ForeignKey(
        to=Municipio, on_delete=models.PROTECT, null=True, blank=True
    )
    localidad = models.ForeignKey(
        to=Localidad, on_delete=models.PROTECT, null=True, blank=True
    )
    partido = models.CharField(max_length=255, null=True, blank=True)
    barrio = models.CharField(max_length=255, null=True, blank=True)
    codigo_postal = models.IntegerField(
        validators=[
            MinValueValidator(1000),
            MaxValueValidator(999999),
        ],  # Entre 4 a 6 digitos
        blank=True,
        null=True,
    )
    # 
    direccion = models.TextField()
    telefono = models.CharField(max_length=20)
    email = models.EmailField()
    referente = models.ForeignKey(
        to=Referente, on_delete=models.SET_NULL, null=True, blank=True
    )

class CentroDesarrolloInfantil(models.Model):
    nombre = models.CharField(max_length=255)
    organizacion = models.ForeignKey(Organizacion, on_delete=models.CASCADE)
    comienzo = models.IntegerField(
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(timezone.now().year),
        ],
        verbose_name="Año en el que comenzó a funcionar",
        blank=True,
        null=True,
    )
    modalidad_gestion = models.CharField(
        max_length=50,
        choices=[
            ("nacional", "Gobierno Nacional"),
            ("provincial", "Gobierno Provincial"),
            ("municipal", "Gobierno Municipal"),
            ("ong", "ONG"),
            ("cogestion", "Co-gestión"),
            ("otra", "Otra")
        ]
    )
    provincia = models.ForeignKey(to=Provincia, on_delete=models.PROTECT, null=True)
    municipio = models.ForeignKey(
        to=Municipio, on_delete=models.PROTECT, null=True, blank=True
    )
    localidad = models.ForeignKey(
        to=Localidad, on_delete=models.PROTECT, null=True, blank=True
    )
    partido = models.CharField(max_length=255, null=True, blank=True)
    barrio = models.CharField(max_length=255, null=True, blank=True)
    codigo_postal = models.IntegerField(
        validators=[
            MinValueValidator(1000),
            MaxValueValidator(999999),
        ],  # Entre 4 a 6 digitos
        blank=True,
        null=True,
    )
    direccion = models.TextField()
    telefono = models.CharField(max_length=20)
    email = models.EmailField()
    meses_funcionamiento = models.ManyToManyField(to=Mes, related_name="centros")
    dias_funcionamiento = models.ManyToManyField(to=Dia, related_name="centros")
    turnos_funcionamiento = models.ManyToManyField(to=Turno, related_name="centros")
    horario_inicio = models.TimeField()
    horario_fin = models.TimeField()
    cantidad_ninos = models.PositiveIntegerField()
    cantidad_trabajadores = models.PositiveIntegerField()
    cobro_arancel = models.CharField(
        max_length=20,
        choices=[
            ("inferior_15", "Arancel inferior al 15%"),
            ("superior_15", "Arancel superior al 15%"),
            ("no_cobra", "No se cobra arancel")
        ]
    )
    estabilidad_matricula = models.BooleanField()

