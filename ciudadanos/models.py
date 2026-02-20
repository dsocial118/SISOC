from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.core.validators import MaxValueValidator as MaxValidator

from core.models import Localidad, Municipio, Nacionalidad, Programa, Provincia, Sexo
from core.soft_delete import SoftDeleteModelMixin

User = get_user_model()


class Ciudadano(SoftDeleteModelMixin, models.Model):
    """Datos básicos del ciudadano/a."""

    DOCUMENTO_DNI = "DNI"
    DOCUMENTO_CUIT = "CUIT"
    DOCUMENTO_PASAPORTE = "PASAPORTE"
    DOCUMENTO_LE = "LE"
    DOCUMENTO_CHOICES = [
        (DOCUMENTO_DNI, "DNI"),
        (DOCUMENTO_CUIT, "CUIT"),
        (DOCUMENTO_PASAPORTE, "Pasaporte"),
        (DOCUMENTO_LE, "Libreta de enrolamiento"),
    ]

    apellido = models.CharField(max_length=255)
    nombre = models.CharField(max_length=255)
    fecha_nacimiento = models.DateField()
    tipo_documento = models.CharField(
        max_length=20, choices=DOCUMENTO_CHOICES, default=DOCUMENTO_DNI
    )
    documento = models.PositiveBigIntegerField(
        validators=[MinValueValidator(1)], null=True
    )
    sexo = models.ForeignKey(Sexo, on_delete=models.SET_NULL, null=True, blank=True)
    nacionalidad = models.ForeignKey(
        Nacionalidad, on_delete=models.SET_NULL, null=True, blank=True
    )
    calle = models.CharField(max_length=255, null=True, blank=True)
    altura = models.CharField(max_length=10, null=True, blank=True)
    piso_departamento = models.CharField(max_length=50, null=True, blank=True)
    barrio = models.CharField(max_length=100, null=True, blank=True)
    provincia = models.ForeignKey(
        Provincia, on_delete=models.SET_NULL, null=True, blank=True
    )
    municipio = models.ForeignKey(
        Municipio, on_delete=models.SET_NULL, null=True, blank=True
    )
    localidad = models.ForeignKey(
        Localidad, on_delete=models.SET_NULL, null=True, blank=True
    )
    codigo_postal = models.CharField(max_length=12, null=True, blank=True)
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    telefono = models.CharField(max_length=30, null=True, blank=True)
    telefono_alternativo = models.CharField(max_length=30, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    ESTADO_CIVIL_CHOICES = [
        ("soltero", "Soltero/a"),
        ("casado", "Casado/a"),
        ("divorciado", "Divorciado/a"),
        ("viudo", "Viudo/a"),
        ("union_convivencial", "Unión convivencial"),
    ]
    estado_civil = models.CharField(
        max_length=20, choices=ESTADO_CIVIL_CHOICES, null=True, blank=True
    )
    cuil_cuit = models.CharField(max_length=13, null=True, blank=True)

    ORIGEN_DATO_CHOICES = [
        ("anses", "ANSES"),
        ("renaper", "RENAPER"),
        ("manual", "Carga Manual"),
        ("migracion", "Migración"),
    ]
    origen_dato = models.CharField(
        max_length=20, choices=ORIGEN_DATO_CHOICES, default="manual"
    )

    observaciones = models.TextField(null=True, blank=True)
    foto = models.ImageField(upload_to="ciudadanos", blank=True, null=True)

    familiares = models.ManyToManyField(
        "self", through="GrupoFamiliar", symmetrical=True, blank=True
    )

    creado_por = models.ForeignKey(
        User,
        related_name="ciudadano_creado_por",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    modificado_por = models.ForeignKey(
        User,
        related_name="ciudadano_modificado_por",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    creado = models.DateTimeField(default=timezone.now, editable=False)
    modificado = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["apellido", "nombre"]
        unique_together = ("tipo_documento", "documento")
        indexes = [
            models.Index(fields=["apellido", "nombre"]),
            models.Index(fields=["documento"]),
        ]

    def __str__(self) -> str:
        return f"{self.apellido}, {self.nombre}".strip(", ")

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}".strip()

    @classmethod
    def buscar_por_documento(cls, query, max_results=10, exclude_id=None):
        cleaned = (query or "").strip()
        if len(cleaned) < 4 or not cleaned.isdigit():
            return cls.objects.none()
        qs = cls.objects.filter(documento__startswith=cleaned)
        if exclude_id:
            qs = qs.exclude(pk=exclude_id)
        return qs.only("id", "nombre", "apellido", "documento").order_by("documento")[
            :max_results
        ]

    @property
    def edad(self) -> int:
        """Calcula la edad del ciudadano."""
        if not self.fecha_nacimiento:
            return None
        hoy = timezone.now().date()
        return (
            hoy.year
            - self.fecha_nacimiento.year
            - (
                (hoy.month, hoy.day)
                < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            )
        )

    @property
    def monto_total_mes(self):
        """Calcula el monto total de programas activos."""
        from django.db.models import Sum

        total = self.programas_transferencia.filter(
            activo=True, monto__isnull=False
        ).aggregate(Sum("monto"))["monto__sum"]
        return total or 0

    def get_absolute_url(self):
        return reverse("ciudadanos_ver", kwargs={"pk": self.pk})


class GrupoFamiliar(SoftDeleteModelMixin, models.Model):
    """Relación básica entre dos ciudadanos."""

    RELACION_PADRE = "PADRE/MADRE"
    RELACION_HIJO = "HIJO/A"
    RELACION_PAREJA = "PAREJA"
    RELACION_HERMANO = "HERMANO/A"
    RELACION_TUTOR = "TUTOR/A"
    RELACION_OTRO = "OTRO"

    VINCULO_CHOICES = [
        (RELACION_PADRE, "Padre/Madre"),
        (RELACION_HIJO, "Hijo/a"),
        (RELACION_PAREJA, "Pareja"),
        (RELACION_HERMANO, "Hermano/a"),
        (RELACION_TUTOR, "Tutor/a"),
        (RELACION_OTRO, "Otro"),
    ]

    ESTADO_BUENO = "bueno"
    ESTADO_REGULAR = "regular"
    ESTADO_CONFLICTIVO = "conflictivo"
    ESTADO_CHOICES = [
        (ESTADO_BUENO, "Bueno"),
        (ESTADO_REGULAR, "Regular"),
        (ESTADO_CONFLICTIVO, "Conflictivo"),
    ]

    ciudadano_1 = models.ForeignKey(
        Ciudadano, related_name="relaciones_salientes", on_delete=models.CASCADE
    )
    ciudadano_2 = models.ForeignKey(
        Ciudadano, related_name="relaciones_entrantes", on_delete=models.CASCADE
    )
    vinculo = models.CharField(
        max_length=20, choices=VINCULO_CHOICES, null=True, blank=True
    )
    estado_relacion = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, null=True, blank=True
    )
    conviven = models.BooleanField(default=False)
    cuidador_principal = models.BooleanField(default=False)
    observaciones = models.TextField(null=True, blank=True)

    creado = models.DateTimeField(default=timezone.now, editable=False)
    modificado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ciudadano_1", "ciudadano_2"]
        unique_together = ("ciudadano_1", "ciudadano_2")
        indexes = [
            models.Index(fields=["ciudadano_1"]),
            models.Index(fields=["ciudadano_2"]),
        ]

    def __str__(self) -> str:
        return f"{self.ciudadano_1} - {self.ciudadano_2} ({self.vinculo})"

    def get_absolute_url(self):
        return reverse("ciudadanos_ver", kwargs={"pk": self.ciudadano_1_id})


class Interaccion(models.Model):
    """Registro de interacciones con el ciudadano."""

    ciudadano = models.ForeignKey(
        Ciudadano, related_name="interacciones", on_delete=models.CASCADE
    )
    tipo = models.CharField(
        max_length=255,
        help_text="Ej: Rendición de cuentas, Contacto por teléfono, Relevamiento",
    )
    fecha = models.DateField()
    responsable = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    ESTADO_COMPLETO = "completo"
    ESTADO_EN_PLAN = "en_plan"
    ESTADO_PENDIENTE = "pendiente"

    ESTADO_CHOICES = [
        (ESTADO_COMPLETO, "Completo"),
        (ESTADO_EN_PLAN, "En Plan"),
        (ESTADO_PENDIENTE, "Pendiente"),
    ]

    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE
    )
    notas = models.TextField(null=True, blank=True)

    creado = models.DateTimeField(default=timezone.now, editable=False)
    modificado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Interacción"
        verbose_name_plural = "Interacciones"

    def __str__(self):
        return f"{self.ciudadano} - {self.tipo} ({self.fecha})"


class CiudadanoPrograma(models.Model):
    programas = models.ForeignKey(
        Programa, related_name="programa_ciudadano", on_delete=models.CASCADE
    )
    ciudadano = models.ForeignKey(
        Ciudadano, related_name="ciudadano_programa", on_delete=models.CASCADE
    )
    fecha_creado = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(
        User,
        related_name="prog_creado_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-fecha_creado"]
        verbose_name = "CiudadanoProgramas"
        verbose_name_plural = "CiudadanosProgramas"
        unique_together = (("ciudadano", "programas"),)

    def __str__(self) -> str:
        return f"{self.ciudadano} - {self.programas}"


class HistorialCiudadanoProgramas(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    accion = models.CharField(
        max_length=10, choices=[("agregado", "Agregado"), ("eliminado", "Eliminado")]
    )
    programa = models.ForeignKey(
        Programa, related_name="hist_prog_ciudadano", on_delete=models.CASCADE
    )
    ciudadano = models.ForeignKey(
        Ciudadano, related_name="hist_ciudadano_programa", on_delete=models.CASCADE
    )
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Historial CiudadanoPrograma"
        verbose_name_plural = "Historial CiudadanosProgramas"

    def __str__(self):
        return f"{self.fecha} - {self.accion} - {self.programa} - {self.ciudadano}"


class HistorialTransferencia(models.Model):
    """Historial mensual de transferencias por ciudadano."""

    ciudadano = models.ForeignKey(
        Ciudadano, related_name="historial_transferencias", on_delete=models.CASCADE
    )
    mes = models.IntegerField(validators=[MinValueValidator(1), MaxValidator(12)])
    anio = models.IntegerField(validators=[MinValueValidator(2000)])

    monto_auh = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monto_prestacion_alimentar = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    monto_centro_familia = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    monto_comedor = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    creado = models.DateTimeField(default=timezone.now, editable=False)
    modificado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-anio", "-mes"]
        verbose_name = "Historial de Transferencia"
        verbose_name_plural = "Historial de Transferencias"
        unique_together = ("ciudadano", "mes", "anio")

    def __str__(self):
        return f"{self.ciudadano} - {self.mes}/{self.anio}"

    @property
    def total_mes(self):
        return (
            self.monto_auh
            + self.monto_prestacion_alimentar
            + self.monto_centro_familia
            + self.monto_comedor
        )


class ProgramaTransferencia(models.Model):
    """Programas de transferencia directa e indirecta."""

    TIPO_AUH = "auh"
    TIPO_PRESTACION_ALIMENTAR = "prestacion_alimentar"
    TIPO_CENTRO_FAMILIA = "centro_familia"
    TIPO_COMEDOR = "comedor"
    TIPO_ADUANA = "aduana"

    TIPO_CHOICES = [
        (TIPO_AUH, "AUH"),
        (TIPO_PRESTACION_ALIMENTAR, "Prestación Alimentar"),
        (TIPO_CENTRO_FAMILIA, "Centro de Familia"),
        (TIPO_COMEDOR, "Asiste a comedor"),
        (TIPO_ADUANA, "Aduana"),
    ]

    CATEGORIA_DIRECTA = "directa"
    CATEGORIA_INDIRECTA = "indirecta"

    CATEGORIA_CHOICES = [
        (CATEGORIA_DIRECTA, "Transferencia Directa"),
        (CATEGORIA_INDIRECTA, "Transferencia Indirecta"),
    ]

    ciudadano = models.ForeignKey(
        Ciudadano, related_name="programas_transferencia", on_delete=models.CASCADE
    )
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    monto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cantidad_texto = models.CharField(
        max_length=100, null=True, blank=True, help_text="Ej: '2 colchones'"
    )
    activo = models.BooleanField(default=True)

    creado = models.DateTimeField(default=timezone.now, editable=False)
    modificado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["categoria", "tipo"]
        verbose_name = "Programa de Transferencia"
        verbose_name_plural = "Programas de Transferencia"

    def __str__(self):
        return f"{self.ciudadano} - {self.get_tipo_display()}"
