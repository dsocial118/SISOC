from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator
from core.models import Municipio, Provincia, Localidad
from core.soft_delete import SoftDeleteModelMixin


class TipoOrganizacion(models.Model):
    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        ordering = ["id"]
        verbose_name = "Tipo de Organización"
        verbose_name_plural = "Tipos de Organización"


class TipoEntidad(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Tipo de Entidad"
        verbose_name_plural = "Tipos de Entidad"


class SubtipoEntidad(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    tipo_entidad = models.ForeignKey(
        TipoEntidad,
        on_delete=models.CASCADE,
        related_name="subtipos",
        blank=True,
        null=True,
    )

    def __str__(self):
        return str(self.nombre)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Subtipo de Entidad"
        verbose_name_plural = "Subtipos de Entidad"


class RolFirmante(models.Model):
    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        ordering = ["id"]
        verbose_name = "Rol de Firmante"
        verbose_name_plural = "Roles de Firmante"


class Firmante(SoftDeleteModelMixin, models.Model):
    organizacion = models.ForeignKey(
        "Organizacion", on_delete=models.CASCADE, related_name="firmantes"
    )
    nombre = models.CharField(max_length=255)
    rol = models.ForeignKey(
        RolFirmante,
        on_delete=models.PROTECT,
        related_name="firmantes",
        blank=True,
        null=True,
    )
    cuit = models.BigIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(99999999999)],
    )

    def __str__(self):
        rol = self.rol.nombre if self.rol else "-"
        return f"{self.nombre} ({rol})"


class Aval(SoftDeleteModelMixin, models.Model):
    organizacion = models.ForeignKey(
        "Organizacion",
        on_delete=models.CASCADE,
        related_name="avales",
        blank=True,
        null=True,
    )
    nombre = models.CharField(max_length=255, blank=True, null=True)
    cuit = models.BigIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(99999999999)],
    )

    def __str__(self):
        cuit = self.cuit if self.cuit is not None else "-"
        return f"{self.nombre or 'Aval sin nombre'} ({cuit})"

    class Meta:
        verbose_name = "Aval"
        verbose_name_plural = "Avales"


class Organizacion(SoftDeleteModelMixin, models.Model):
    nombre = models.CharField(max_length=255)
    sigla = models.CharField(max_length=30, blank=True, null=True, verbose_name="Sigla")
    cuit = models.BigIntegerField(
        blank=True,
        null=True,
        db_index=True,
        validators=[MinValueValidator(0), MaxValueValidator(99999999999)],
    )
    telefono = models.BigIntegerField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    domicilio = models.CharField(max_length=255, blank=True, null=True)
    localidad = models.ForeignKey(
        to=Localidad, on_delete=models.SET_NULL, null=True, blank=True
    )
    partido = models.CharField(max_length=255, null=True, blank=True)
    provincia = models.ForeignKey(to=Provincia, on_delete=models.PROTECT, null=True)
    municipio = models.ForeignKey(
        to=Municipio, on_delete=models.SET_NULL, null=True, blank=True
    )
    tipo_entidad = models.ForeignKey(
        TipoEntidad,
        on_delete=models.CASCADE,
        related_name="organizaciones",
        blank=True,
        null=True,
    )
    subtipo_entidad = models.ForeignKey(
        SubtipoEntidad,
        on_delete=models.CASCADE,
        related_name="organizaciones",
        blank=True,
        null=True,
    )
    fecha_vencimiento = models.DateTimeField(
        default=timezone.now, verbose_name="Fecha de vencimiento"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        ordering = ["id"]
        verbose_name = "Organizacion"
        verbose_name_plural = "Organizaciones"
        indexes = [
            models.Index(fields=["telefono"], name="org_telefono_idx"),
        ]


class DocumentacionOrganizacion(models.Model):
    CATEGORIA_PERSONERIA = "personeria_juridica"
    CATEGORIA_ECLESIASTICA = "personeria_eclesiastica"
    CATEGORIA_BASE = "organizacion_base"

    CATEGORIAS = [
        (CATEGORIA_PERSONERIA, "Organizacion con personeria juridica"),
        (CATEGORIA_ECLESIASTICA, "Personeria juridica eclesiastica"),
        (CATEGORIA_BASE, "Organizacion de base"),
    ]

    nombre = models.CharField(max_length=255)
    categoria = models.CharField(max_length=40, choices=CATEGORIAS)
    obligatorio = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ["categoria", "orden", "id"]
        verbose_name = "Documentacion de organizacion"
        verbose_name_plural = "Documentaciones de organizacion"


class ArchivoOrganizacion(SoftDeleteModelMixin, models.Model):
    ESTADO_PENDIENTE = "pendiente"
    ESTADO_ADJUNTO = "Documento adjunto"
    ESTADO_A_VALIDAR = "A Validar Abogado"
    ESTADO_RECTIFICAR = "Rectificar"
    ESTADO_ACEPTADO = "Aceptado"

    ESTADOS = [
        (ESTADO_PENDIENTE, "Pendiente"),
        (ESTADO_ADJUNTO, "Documento adjunto"),
        (ESTADO_A_VALIDAR, "A Validar Abogado"),
        (ESTADO_RECTIFICAR, "Rectificar"),
        (ESTADO_ACEPTADO, "Aceptado"),
    ]

    organizacion = models.ForeignKey(
        Organizacion, on_delete=models.CASCADE, related_name="archivos_documentacion"
    )
    documentacion = models.ForeignKey(
        DocumentacionOrganizacion,
        on_delete=models.SET_NULL,
        related_name="archivos",
        null=True,
        blank=True,
    )
    nombre_personalizado = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Nombre personalizado",
        help_text="Nombre del documento adicional cuando no corresponde al catalogo.",
    )
    archivo = models.FileField(upload_to="organizaciones/documentacion/")
    estado = models.CharField(max_length=20, choices=ESTADOS, default=ESTADO_ADJUNTO)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    numero_gde = models.CharField(
        "Numero de GDE",
        max_length=50,
        blank=True,
        null=True,
    )
    observaciones = models.TextField(blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    modificado = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organizaciones_archivos_creados",
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organizaciones_archivos_modificados",
    )

    @property
    def esta_vencido(self):
        return bool(
            self.fecha_vencimiento and self.fecha_vencimiento < timezone.now().date()
        )

    @property
    def esta_por_vencer(self):
        if not self.fecha_vencimiento or self.esta_vencido:
            return False
        return (self.fecha_vencimiento - timezone.now().date()).days <= 30

    @property
    def es_personalizado(self):
        return self.documentacion_id is None

    @property
    def nombre_documento(self):
        if self.documentacion_id:
            return self.documentacion.nombre
        return self.nombre_personalizado or "Documento adicional"

    def __str__(self):
        return f"{self.organizacion_id} - {self.nombre_documento}"

    class Meta:
        ordering = ["-creado", "-id"]
        indexes = [
            models.Index(
                fields=["organizacion", "documentacion", "-creado"],
                name="org_doc_archivo_idx",
            ),
        ]
        verbose_name = "Archivo de organizacion"
        verbose_name_plural = "Archivos de organizacion"
