import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from core.models import Municipio, Provincia


class PasEstado(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Estado PAS"
        verbose_name_plural = "Estados PAS"

    def __str__(self):
        return self.nombre


class PasAviso(models.Model):
    codigo = models.PositiveIntegerField(unique=True)
    descripcion = models.CharField(max_length=255)
    observacion = models.CharField(max_length=255, blank=True)
    estados = models.ManyToManyField(PasEstado, related_name="avisos")

    class Meta:
        ordering = ["codigo"]
        verbose_name = "Aviso PAS"
        verbose_name_plural = "Avisos PAS"

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"


class PasPersona(models.Model):
    id_persona = models.PositiveIntegerField(unique=True, verbose_name="IdPersona")
    apellidos = models.CharField(max_length=150)
    nombres = models.CharField(max_length=150)
    dni = models.PositiveIntegerField(unique=True)
    cuit = models.CharField(max_length=20, blank=True)
    provincia = models.ForeignKey(Provincia, on_delete=models.PROTECT)
    municipio = models.ForeignKey(Municipio, on_delete=models.PROTECT)
    domicilio = models.CharField(max_length=255, blank=True)
    correo_electronico = models.EmailField(blank=True)
    telefono_celular = models.CharField(max_length=30, blank=True)
    estado = models.ForeignKey(PasEstado, on_delete=models.PROTECT)
    avisos = models.ManyToManyField(PasAviso, related_name="personas")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["apellidos", "nombres", "id_persona"]
        permissions = [
            ("export_ddjj_tokens", "Puede exportar enlaces de DDJJ PAS"),
        ]
        verbose_name = "Persona PAS"
        verbose_name_plural = "Personas PAS"

    def __str__(self):
        return f"{self.apellidos}, {self.nombres} - {self.dni}"

    @property
    def declaracion_jurada_vigente(self):
        return getattr(self, "declaraciones_juradas").first()

    @property
    def invitacion_ddjj_vigente(self):
        return (
            self.invitaciones_ddjj.filter(utilizada__isnull=True, revocada__isnull=True)
            .filter(Q(vence__isnull=True) | Q(vence__gt=timezone.now()))
            .first()
        )


class PasInvitacionDDJJ(models.Model):
    persona = models.ForeignKey(
        PasPersona,
        on_delete=models.CASCADE,
        related_name="invitaciones_ddjj",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    creada = models.DateTimeField(auto_now_add=True)
    vence = models.DateTimeField(null=True, blank=True)
    utilizada = models.DateTimeField(null=True, blank=True)
    revocada = models.DateTimeField(null=True, blank=True)
    creada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invitaciones_ddjj_pas",
    )

    class Meta:
        ordering = ["-creada", "-id"]
        verbose_name = "Invitación a DDJJ PAS"
        verbose_name_plural = "Invitaciones a DDJJ PAS"

    @property
    def disponible(self):
        return (
            not self.utilizada
            and not self.revocada
            and (not self.vence or self.vence > timezone.now())
        )

    def get_formulario_path(self):
        return reverse("pas_ddjj_formulario", kwargs={"token": self.token})

    def get_formulario_url(self, public_origin=None):
        origin = (public_origin or settings.DOMINIO).strip().rstrip("/")
        if not origin:
            raise ValueError(
                "No se configuró DOMINIO para construir la URL pública de la DDJJ."
            )
        return f"{origin}{self.get_formulario_path()}"


def archivo_ddjj_pas_upload_to(instance, filename):
    return (
        f"pas/ddjj/{instance.persona.dni}/{instance.presentada:%Y}/"
        f"ddjj_pas_{instance.persona.dni}_v{instance.version}.pdf"
    )


class PasDeclaracionJurada(models.Model):
    persona = models.ForeignKey(
        PasPersona,
        on_delete=models.PROTECT,
        related_name="declaraciones_juradas",
    )
    invitacion = models.OneToOneField(
        PasInvitacionDDJJ,
        on_delete=models.PROTECT,
        related_name="declaracion",
    )
    version = models.PositiveIntegerField()
    presentada = models.DateTimeField(auto_now_add=True)
    provincia = models.ForeignKey(
        Provincia,
        on_delete=models.PROTECT,
        related_name="declaraciones_juradas_pas",
    )
    municipio = models.ForeignKey(
        Municipio,
        on_delete=models.PROTECT,
        related_name="declaraciones_juradas_pas",
    )
    domicilio = models.CharField(max_length=255)
    correo_electronico = models.EmailField()
    telefono_celular = models.CharField(max_length=30)
    datos_mi_argentina_confirmados = models.BooleanField()
    embarazada = models.BooleanField()
    controles_embarazo_cumplidos = models.BooleanField(null=True, blank=True)
    hijos_menores_a_cargo = models.BooleanField()
    vacunacion_cumplida = models.BooleanField(null=True, blank=True)
    regularidad_escolar_acreditada = models.BooleanField(null=True, blank=True)
    gastos_bajo_limite_smvm = models.BooleanField()
    no_accedio_mercado_cambios = models.BooleanField()
    acepto_declaracion = models.BooleanField()
    respuestas = models.JSONField(default=dict)
    texto_legal = models.TextField()
    archivo_pdf = models.FileField(upload_to=archivo_ddjj_pas_upload_to)
    finalizada = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-version", "-presentada", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["persona", "version"],
                name="pas_ddjj_persona_version_uniq",
            )
        ]
        verbose_name = "Declaración jurada PAS"
        verbose_name_plural = "Declaraciones juradas PAS"

    def save(self, *args, **kwargs):
        if self.pk:
            original = type(self).objects.filter(pk=self.pk).only("finalizada").first()
            if original and original.finalizada:
                raise ValidationError("Una declaración jurada finalizada es inmutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Las declaraciones juradas no pueden eliminarse.")

    def __str__(self):
        return f"DDJJ {self.persona.dni} - versión {self.version}"


class PasExportacionTokens(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="exportaciones_tokens_ddjj_pas",
    )
    fecha = models.DateTimeField(auto_now_add=True)
    cantidad = models.PositiveIntegerField()

    class Meta:
        ordering = ["-fecha", "-id"]
        verbose_name = "Exportación de enlaces DDJJ PAS"
        verbose_name_plural = "Exportaciones de enlaces DDJJ PAS"

    def __str__(self):
        return f"Exportación DDJJ del {self.fecha:%d/%m/%Y %H:%M}"


class PasHistorialEstado(models.Model):
    persona = models.ForeignKey(
        PasPersona,
        on_delete=models.CASCADE,
        related_name="historial_estados",
    )
    estado_anterior = models.ForeignKey(
        PasEstado,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="historiales_como_anterior",
    )
    estado_nuevo = models.ForeignKey(
        PasEstado,
        on_delete=models.PROTECT,
        related_name="historiales_como_nuevo",
    )
    avisos_anteriores = models.ManyToManyField(
        PasAviso,
        blank=True,
        related_name="historiales_como_anterior",
    )
    avisos_nuevos = models.ManyToManyField(
        PasAviso,
        related_name="historiales_como_nuevo",
    )
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-fecha_cambio", "-id"]
        verbose_name = "Historial de estado PAS"
        verbose_name_plural = "Historiales de estado PAS"

    def __str__(self):
        return f"{self.persona_id} - {self.estado_nuevo} - {self.fecha_cambio:%d/%m/%Y}"


class PasInforme(models.Model):
    creado = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="informes_pas",
    )
    filtros = models.JSONField(default=dict, blank=True)
    modo = models.CharField(max_length=20, default="registros")
    resultado = models.JSONField(default=list, blank=True)
    total_personas = models.PositiveIntegerField(default=0)
    total_cambios = models.PositiveIntegerField(default=0)
    personas = models.ManyToManyField(PasPersona, blank=True, related_name="informes")
    cambios = models.ManyToManyField(
        PasHistorialEstado, blank=True, related_name="informes"
    )

    class Meta:
        ordering = ["-creado", "-id"]
        verbose_name = "Informe PAS"
        verbose_name_plural = "Informes PAS"

    def __str__(self):
        return self.numero

    @property
    def numero(self):
        if not self.pk:
            return "PAS-INF"
        return f"PAS-INF-{self.pk:06d}"
