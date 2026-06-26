from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from core.models import Programa

from .validators import INSUMO_FILE_VALIDATORS


def insumo_upload_to(instance, filename):
    """Ruta de guardado del archivo del insumo, agrupada por programa."""
    return f"insumos/programa_{instance.programa_id or 'sin'}/{filename}"


class InsumoCategoria(models.Model):
    """Categoría para organizar los insumos de un programa de comedores."""

    programa = models.ForeignKey(
        Programa,
        on_delete=models.PROTECT,
        related_name="insumo_categorias",
        verbose_name="Programa",
    )
    nombre = models.CharField(max_length=150, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, default="", verbose_name="Descripción")
    orden = models.PositiveIntegerField(default=0, verbose_name="Orden")
    activo = models.BooleanField(default=True, verbose_name="Activa")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categoría de insumo"
        verbose_name_plural = "Categorías de insumos"
        ordering = ["orden", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["programa", "nombre"],
                name="uniq_insumocategoria_programa_nombre",
            )
        ]

    def __str__(self):
        return self.nombre


class Insumo(models.Model):
    """Documento descargable asociado a un programa de comedores."""

    programa = models.ForeignKey(
        Programa,
        on_delete=models.PROTECT,
        related_name="insumos",
        verbose_name="Programa",
    )
    categoria = models.ForeignKey(
        InsumoCategoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="insumos",
        verbose_name="Categoría",
    )
    titulo = models.CharField(max_length=200, verbose_name="Título")
    descripcion = models.TextField(blank=True, default="", verbose_name="Descripción")
    archivo = models.FileField(
        upload_to=insumo_upload_to,
        max_length=255,
        validators=INSUMO_FILE_VALIDATORS,
        verbose_name="Archivo",
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="insumos_creados",
        verbose_name="Usuario de creación",
    )
    usuario_actualizacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="insumos_actualizados",
        verbose_name="Usuario de actualización",
    )

    class Meta:
        verbose_name = "Insumo"
        verbose_name_plural = "Insumos"
        ordering = ["-fecha_creacion", "titulo"]

    def __str__(self):
        return self.titulo

    def clean(self):
        super().clean()
        if (
            self.categoria_id
            and self.programa_id
            and self.categoria.programa_id != self.programa_id
        ):
            raise ValidationError(
                {"categoria": ("La categoría seleccionada pertenece a otro programa.")}
            )

    @property
    def nombre_archivo(self):
        if not self.archivo:
            return ""
        return self.archivo.name.rsplit("/", 1)[-1]

    @property
    def categoria_display(self):
        return self.categoria.nombre if self.categoria_id else "Sin categoría"

    @property
    def creado_por_display(self):
        user = self.usuario_creacion
        if not user:
            return "-"
        return user.get_full_name() or user.get_username()
