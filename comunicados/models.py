from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class EstadoComunicado(models.TextChoices):
    BORRADOR = "borrador", "Borrador"
    PUBLICADO = "publicado", "Publicado"
    ARCHIVADO = "archivado", "Archivado"


class TipoComunicado(models.TextChoices):
    INTERNO = "interno", "Comunicación Interna"
    EXTERNO = "externo", "Comunicación Externa"


class SubtipoComunicado(models.TextChoices):
    INSTITUCIONAL = "institucional", "Comunicación Institucional"
    COMEDORES = "comedores", "Comunicación a Comedores"


class Comunicado(models.Model):
    titulo = models.CharField(max_length=255, verbose_name="Título")
    cuerpo = models.TextField(verbose_name="Cuerpo")
    estado = models.CharField(
        max_length=20,
        choices=EstadoComunicado.choices,
        default=EstadoComunicado.BORRADOR,
        verbose_name="Estado",
    )
    destacado = models.BooleanField(default=False, verbose_name="Destacado")
    tipo = models.CharField(
        max_length=20,
        choices=TipoComunicado.choices,
        default=TipoComunicado.INTERNO,
        verbose_name="Tipo de comunicado",
    )
    subtipo = models.CharField(
        max_length=20,
        choices=SubtipoComunicado.choices,
        default="",
        blank=True,
        verbose_name="Subtipo de comunicado",
    )
    para_todos_comedores = models.BooleanField(
        default=False,
        verbose_name="Enviar a todos los comedores",
    )
    comedores = models.ManyToManyField(
        "comedores.Comedor",
        blank=True,
        related_name="comunicados",
        verbose_name="Comedores destinatarios",
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de creación"
    )
    fecha_publicacion = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de publicación"
    )
    fecha_vencimiento = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de vencimiento"
    )
    usuario_creador = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="comunicados_creados",
        verbose_name="Usuario creador",
    )
    usuario_ultima_modificacion = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="comunicados_modificados",
        null=True,
        blank=True,
        verbose_name="Última modificación por",
    )
    fecha_ultima_modificacion = models.DateTimeField(
        auto_now=True, verbose_name="Fecha última modificación"
    )

    class Meta:
        verbose_name = "Comunicado"
        verbose_name_plural = "Comunicados"
        ordering = ["-destacado", "-fecha_publicacion", "-fecha_creacion"]

    def __str__(self):
        return self.titulo

    def publicar(self, usuario):
        """Publica el comunicado, estableciendo la fecha de publicación."""
        self.estado = EstadoComunicado.PUBLICADO
        self.fecha_publicacion = timezone.now()
        self.usuario_ultima_modificacion = usuario
        self.save()

    def archivar(self, usuario):
        """Archiva el comunicado."""
        self.estado = EstadoComunicado.ARCHIVADO
        self.usuario_ultima_modificacion = usuario
        self.save()

    @property
    def esta_vencido(self):
        """Verifica si el comunicado está vencido."""
        if self.fecha_vencimiento:
            return timezone.now() > self.fecha_vencimiento
        return False

    @property
    def es_visible(self):
        """Determina si el comunicado debe mostrarse en la vista principal."""
        return self.estado == EstadoComunicado.PUBLICADO and not self.esta_vencido


class ComunicadoAdjunto(models.Model):
    comunicado = models.ForeignKey(
        Comunicado,
        on_delete=models.CASCADE,
        related_name="adjuntos",
        verbose_name="Comunicado",
    )
    archivo = models.FileField(
        upload_to="comunicados/adjuntos/",
        verbose_name="Archivo",
    )
    nombre_original = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Nombre original",
    )
    fecha_subida = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de subida"
    )

    class Meta:
        verbose_name = "Adjunto"
        verbose_name_plural = "Adjuntos"

    def __str__(self):
        return self.nombre_original or self.archivo.name

    def save(self, *args, **kwargs):
        if not self.nombre_original and self.archivo:
            self.nombre_original = self.archivo.name.split("/")[-1]
        super().save(*args, **kwargs)
