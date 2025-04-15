from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone

from configuraciones.models import Municipio, Provincia
from configuraciones.models import Localidad, Mes, Dia, Turno
from organizaciones.models import Organizacion


class CentroDesarrolloInfantil(models.Model):
    nombre = models.CharField(max_length=255)
    organizacion = models.ForeignKey(
        Organizacion,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    comienzo = models.IntegerField(
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(timezone.now().year),
        ],
        verbose_name="Año en el que comenzó a funcionar",
        blank=True,
        null=True,
    )
    numexpe = models.IntegerField(
        verbose_name="Numero de expediente",
        blank=True,
        null=True,
    )
    numrepo = models.IntegerField(
        verbose_name="Numero de Repi",
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
            ("otra", "Otra"),
        ],
        blank=True,
        null=True,
    )
    provincia = models.ForeignKey(
        to=Provincia,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
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
        ],
        blank=True,
        null=True,
    )
    direccion = models.TextField(
        blank=True,
        null=True,
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )
    email = models.EmailField(
        blank=True,
        null=True,
    )
    meses_funcionamiento = models.ManyToManyField(
        to=Mes,
        related_name="centros",
        blank=True,
    )
    dias_funcionamiento = models.ManyToManyField(
        to=Dia,
        related_name="centros",
        blank=True,
    )
    turnos_funcionamiento = models.ManyToManyField(
        to=Turno,
        related_name="centros",
        blank=True,
    )
    horario_inicio = models.TimeField(
        blank=True,
        null=True,
    )
    horario_fin = models.TimeField(
        blank=True,
        null=True,
    )
    cantidad_ninos = models.PositiveIntegerField(
        blank=True,
        null=True,
    )
    cantidad_trabajadores = models.PositiveIntegerField(
        blank=True,
        null=True,
    )
    cobro_arancel = models.CharField(
        max_length=20,
        choices=[
            ("inferior_15", "Arancel inferior al 15%"),
            ("superior_15", "Arancel superior al 15%"),
            ("no_cobra", "No se cobra arancel"),
        ],
        blank=True,
        null=True,
    )
    estabilidad_matricula = models.BooleanField(
        blank=True,
        null=True,
    )
    foto_legajo = models.ImageField(upload_to="cdi/", blank=True, null=True)
