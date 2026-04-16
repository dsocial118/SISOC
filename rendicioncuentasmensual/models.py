from django.conf import settings
from django.db import models

from comedores.models import Comedor
from core.soft_delete import SoftDeleteModelMixin


class DocumentacionAdjunta(SoftDeleteModelMixin, models.Model):
    CATEGORIA_FORMULARIO_II = "formulario_ii"
    CATEGORIA_FORMULARIO_III = "formulario_iii"
    CATEGORIA_FORMULARIO_IV = "formulario_iv"
    CATEGORIA_FORMULARIO_V = "formulario_v"
    CATEGORIA_FORMULARIO_VI = "formulario_vi"
    CATEGORIA_EXTRACTO_BANCARIO = "extracto_bancario"
    CATEGORIA_COMPROBANTES = "comprobantes"
    CATEGORIA_PLANILLA_SEGUROS = "planilla_seguros"
    CATEGORIA_OTROS = "otros"

    ESTADO_PRESENTADO = "presentado"
    ESTADO_SUBSANAR = "subsanar"
    ESTADO_VALIDADO = "validado"

    CATEGORIA_CHOICES = [
        (CATEGORIA_FORMULARIO_II, "Formulario II"),
        (CATEGORIA_FORMULARIO_III, "Formulario III"),
        (CATEGORIA_FORMULARIO_IV, "Formulario IV"),
        (CATEGORIA_FORMULARIO_V, "Formulario V"),
        (CATEGORIA_FORMULARIO_VI, "Formulario VI"),
        (CATEGORIA_EXTRACTO_BANCARIO, "Extracto Bancario"),
        (CATEGORIA_COMPROBANTES, "Comprobante/s"),
        (CATEGORIA_PLANILLA_SEGUROS, "Planilla de Seguros"),
        (CATEGORIA_OTROS, "Documentación Extra"),
    ]

    ESTADO_CHOICES = [
        (ESTADO_PRESENTADO, "Presentado"),
        (ESTADO_SUBSANAR, "A Subsanar"),
        (ESTADO_VALIDADO, "Validado"),
    ]

    CATEGORIAS_CONFIG = (
        {
            "codigo": CATEGORIA_FORMULARIO_II,
            "label": "Formulario II",
            "required": True,
            "multiple": False,
            "order": 1,
        },
        {
            "codigo": CATEGORIA_FORMULARIO_III,
            "label": "Formulario III",
            "required": True,
            "multiple": False,
            "order": 2,
        },
        {
            "codigo": CATEGORIA_FORMULARIO_IV,
            "label": "Formulario IV",
            "required": False,
            "multiple": False,
            "order": 3,
        },
        {
            "codigo": CATEGORIA_FORMULARIO_V,
            "label": "Formulario V",
            "required": True,
            "multiple": False,
            "order": 4,
        },
        {
            "codigo": CATEGORIA_FORMULARIO_VI,
            "label": "Formulario VI",
            "required": False,
            "multiple": False,
            "order": 5,
        },
        {
            "codigo": CATEGORIA_EXTRACTO_BANCARIO,
            "label": "Extracto Bancario",
            "required": True,
            "multiple": False,
            "order": 6,
        },
        {
            "codigo": CATEGORIA_COMPROBANTES,
            "label": "Comprobante/s",
            "required": True,
            "multiple": True,
            "order": 7,
        },
        {
            "codigo": CATEGORIA_PLANILLA_SEGUROS,
            "label": "Planilla de Seguros",
            "required": False,
            "multiple": False,
            "order": 8,
        },
        {
            "codigo": CATEGORIA_OTROS,
            "label": "Documentación Extra",
            "required": False,
            "multiple": True,
            "order": 9,
        },
    )

    nombre = models.CharField(max_length=255, verbose_name="Nombre del Documento")
    categoria = models.CharField(
        max_length=40,
        choices=CATEGORIA_CHOICES,
        default=CATEGORIA_COMPROBANTES,
        verbose_name="Categoría",
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default=ESTADO_PRESENTADO,
        verbose_name="Estado del documento",
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones",
    )
    archivo = models.FileField(
        upload_to="rendicioncuentasmensualdocumentos_adjuntos/",
        verbose_name="Archivo",
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación",
    )
    ultima_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Modificación",
    )
    rendicion_cuenta_mensual = models.ForeignKey(
        "RendicionCuentaMensual",
        on_delete=models.CASCADE,
        related_name="archivos_adjuntos",
        verbose_name="Rendición de Cuenta Mensual",
        null=True,
        blank=True,
    )
    documento_subsanado = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="subsanaciones",
        verbose_name="Documento subsanado",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Documento Adjunto"
        verbose_name_plural = "Documentos Adjuntos"

    def get_estado_visual(self):
        override = getattr(self, "estado_visual_override", None)
        if override:
            return override
        return self.estado

    def get_estado_visual_display(self):
        override = getattr(self, "estado_visual_display_override", None)
        if override:
            return override
        return self.get_estado_display()

    @classmethod
    def categorias_mobile(cls):
        return list(cls.CATEGORIAS_CONFIG)

    @classmethod
    def categorias_obligatorias(cls):
        return {item["codigo"] for item in cls.CATEGORIAS_CONFIG if item["required"]}

    @classmethod
    def categorias_multiples(cls):
        return {item["codigo"] for item in cls.CATEGORIAS_CONFIG if item["multiple"]}

    @classmethod
    def get_categoria_config(cls, categoria):
        return next(
            (item for item in cls.CATEGORIAS_CONFIG if item["codigo"] == categoria),
            None,
        )


class RendicionCuentaMensual(SoftDeleteModelMixin, models.Model):
    ESTADO_ELABORACION = "elaboracion"
    ESTADO_REVISION = "revision"
    ESTADO_SUBSANAR = "subsanar"
    ESTADO_FINALIZADA = "finalizada"

    ESTADO_CHOICES = [
        (ESTADO_ELABORACION, "Presentación en elaboración"),
        (ESTADO_REVISION, "Presentación en revisión"),
        (ESTADO_SUBSANAR, "Presentación a subsanar"),
        (ESTADO_FINALIZADA, "Presentación finalizada"),
    ]

    MESES = [
        (1, "Enero"),
        (2, "Febrero"),
        (3, "Marzo"),
        (4, "Abril"),
        (5, "Mayo"),
        (6, "Junio"),
        (7, "Julio"),
        (8, "Agosto"),
        (9, "Septiembre"),
        (10, "Octubre"),
        (11, "Noviembre"),
        (12, "Diciembre"),
    ]

    comedor = models.ForeignKey(
        Comedor,
        on_delete=models.SET_NULL,
        related_name="rendiciones_cuentas_mensuales",
        null=True,
        blank=True,
    )
    mes = models.IntegerField(verbose_name="Mes", choices=MESES)
    anio = models.IntegerField(verbose_name="Año")
    convenio = models.CharField(
        max_length=100,
        verbose_name="Convenio",
        blank=True,
        null=True,
    )
    numero_rendicion = models.PositiveIntegerField(
        verbose_name="Número de Rendición",
        blank=True,
        null=True,
    )
    periodo_inicio = models.DateField(
        verbose_name="Período inicio",
        blank=True,
        null=True,
    )
    periodo_fin = models.DateField(
        verbose_name="Período fin",
        blank=True,
        null=True,
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default=ESTADO_ELABORACION,
        verbose_name="Estado de Rendición",
    )
    documento_adjunto = models.BooleanField(
        default=False,
        verbose_name="Documento Adjunto",
    )
    observaciones = models.TextField(
        verbose_name="Observaciones",
        blank=True,
        null=True,
    )
    usuario_creador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="rendiciones_cuentas_mensuales_creadas",
        blank=True,
        null=True,
        verbose_name="Usuario creador",
    )
    usuario_ultima_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="rendiciones_cuentas_mensuales_modificadas",
        blank=True,
        null=True,
        verbose_name="Usuario última modificación",
    )
    ultima_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Modificación",
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación",
    )

    class Meta:
        permissions = [
            ("manage_mobile_rendicion", "Puede gestionar rendiciones mobile"),
        ]
        verbose_name = "Rendición de Cuenta Mensual"
        verbose_name_plural = "Rendiciones de Cuenta Mensuales"

    @property
    def arvhios_adjuntos(self):  # compat legacy (typo histórico)
        return getattr(self, "archivos_adjuntos")
