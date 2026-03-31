# pylint: disable=too-many-lines

from django.db import models
from django.contrib.auth.models import User
from ciudadanos.models import Ciudadano
from core.models import Dia, Localidad, Municipio, Provincia, Programa
from core.soft_delete import SoftDeleteModelMixin


class Centro(SoftDeleteModelMixin, models.Model):
    nombre = models.CharField(max_length=200)
    referente = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        limit_choices_to={"groups__name": "ReferenteCentroVAT"},
        related_name="vat_centros",
        null=True,
        blank=False,
    )
    codigo = models.CharField(max_length=20, unique=True)
    activo = models.BooleanField(default=True)
    provincia = models.ForeignKey(
        to=Provincia,
        on_delete=models.PROTECT,
        null=True,
        related_name="vat_centros",
    )
    municipio = models.ForeignKey(
        to=Municipio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vat_centros",
    )
    localidad = models.ForeignKey(
        to=Localidad,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vat_centros",
    )
    calle = models.CharField(max_length=255, blank=True, null=True)
    numero = models.PositiveIntegerField(blank=True, null=True)
    domicilio_actividad = models.CharField(
        max_length=255, verbose_name="Domicilio de actividades"
    )
    codigo_postal = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Código Postal",
    )
    lote = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Lote",
    )
    manzana = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Manzana",
    )
    entre_calles = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Entre Calles",
    )
    telefono = models.CharField(max_length=50, verbose_name="Teléfono")
    celular = models.CharField(max_length=50, verbose_name="Celular")
    correo = models.EmailField(max_length=100, verbose_name="Correo electrónico")
    sitio_web = models.URLField(
        max_length=200, blank=True, null=True, verbose_name="Sitio web"
    )
    nombre_referente = models.CharField(
        max_length=100, verbose_name="Nombre del responsable"
    )
    apellido_referente = models.CharField(
        max_length=100, verbose_name="Apellido del responsable"
    )
    telefono_referente = models.CharField(
        max_length=50, verbose_name="Teléfono del responsable"
    )
    correo_referente = models.EmailField(
        max_length=100, verbose_name="Correo del responsable"
    )
    tipo_gestion = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Tipo de Gestión"
    )
    clase_institucion = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Clase de Institución"
    )
    situacion = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Situación"
    )

    def __str__(self):
        return self.nombre

    class Meta:
        indexes = [
            models.Index(
                fields=["nombre"],
                name="vat_centro_nombre_idx",
            ),
        ]


class ModalidadInstitucional(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la modalidad")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Modalidad Institucional"
        verbose_name_plural = "Modalidades Institucionales"
        ordering = ["nombre"]


class Sector(SoftDeleteModelMixin, models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre del sector")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Sector"
        verbose_name_plural = "Sectores"
        ordering = ["nombre"]
        indexes = [
            models.Index(
                fields=["nombre"],
                name="vat_sector_nombre_idx",
            ),
        ]


class Subsector(SoftDeleteModelMixin, models.Model):
    sector = models.ForeignKey(
        Sector,
        on_delete=models.CASCADE,
        related_name="subsectores",
        verbose_name="Sector",
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre del subsector")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    def __str__(self):
        return f"{self.nombre} ({self.sector.nombre})"

    class Meta:
        verbose_name = "Subsector"
        verbose_name_plural = "Subsectores"
        ordering = ["sector", "nombre"]
        unique_together = ("sector", "nombre")
        indexes = [
            models.Index(
                fields=["nombre"],
                name="vat_subsector_nombre_idx",
            ),
        ]


class TituloReferencia(SoftDeleteModelMixin, models.Model):
    codigo_referencia = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Código de Referencia"
    )
    nombre = models.CharField(max_length=200, verbose_name="Nombre del título")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Activo")

    def __str__(self):
        return self.nombre

    plan_estudio = models.ForeignKey(
        "PlanVersionCurricular",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="titulos",
        verbose_name="Plan de Estudio",
    )

    class Meta:
        verbose_name = "Título de Referencia"
        verbose_name_plural = "Títulos de Referencia"
        ordering = ["nombre"]
        indexes = [
            models.Index(
                fields=["nombre"],
                name="vat_titref_nombre_idx",
            ),
        ]


class ModalidadCursada(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la modalidad")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Activo")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Modalidad de Cursado"
        verbose_name_plural = "Modalidades de Cursado"
        ordering = ["nombre"]


class PlanVersionCurricular(SoftDeleteModelMixin, models.Model):
    sector = models.ForeignKey(
        Sector,
        on_delete=models.PROTECT,
        related_name="planes_estudio",
        verbose_name="Sector",
    )
    subsector = models.ForeignKey(
        Subsector,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="planes_estudio",
        verbose_name="Subsector",
    )
    modalidad_cursada = models.ForeignKey(
        ModalidadCursada,
        on_delete=models.PROTECT,
        related_name="planes",
        verbose_name="Modalidad de Cursado",
    )
    normativa = models.CharField(
        max_length=200, blank=True, null=True, verbose_name="Normativa"
    )
    horas_reloj = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Horas Reloj"
    )
    nivel_requerido = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Nivel Requerido"
    )
    nivel_certifica = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Nivel que Certifica"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")

    def clean(self):
        from django.core.exceptions import ValidationError

        errors = {}

        if self.subsector_id and self.sector_id:
            if self.subsector.sector_id != self.sector_id:
                errors["subsector"] = (
                    "El subsector seleccionado no pertenece al sector indicado."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.sector.nombre} - {self.modalidad_cursada.nombre}"

    class Meta:
        verbose_name = "Plan de Estudio"
        verbose_name_plural = "Planes de Estudio"
        ordering = ["sector", "modalidad_cursada"]

    @property
    def titulo_referencia(self):
        """Backward compat: devuelve el primer Título asociado a este plan."""
        return self.titulos.order_by("id").first()

    @property
    def titulo_referencia_id(self):
        """Backward compat."""
        t = self.titulo_referencia
        return t.id if t else None


class InscripcionOferta(SoftDeleteModelMixin, models.Model):
    ESTADO_CHOICES = [
        ("inscrito", "Inscrito"),
        ("lista_espera", "Lista de Espera"),
        ("completado", "Completado"),
        ("abandonado", "Abandonado"),
        ("rechazado", "Rechazado"),
    ]

    oferta = models.ForeignKey(
        "Comision",
        on_delete=models.CASCADE,
        related_name="inscripciones_oferta",
        verbose_name="Comisión",
    )
    ciudadano = models.ForeignKey(
        Ciudadano,
        on_delete=models.PROTECT,
        related_name="vat_inscripciones_oferta",
        verbose_name="Ciudadano",
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="inscrito",
        verbose_name="Estado",
    )
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    inscrito_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="vat_inscripciones_oferta_realizadas",
        verbose_name="Inscrito por",
    )

    def __str__(self):
        return f"{self.ciudadano} - {self.oferta} [{self.estado}]"

    class Meta:
        verbose_name = "Inscripción a Comisión"
        verbose_name_plural = "Inscripciones a Comisiones"
        unique_together = ("oferta", "ciudadano")
        ordering = ["-fecha_inscripcion"]
        indexes = [
            models.Index(fields=["oferta", "estado"], name="vat_inscofe_ofe_est_idx"),
            models.Index(
                fields=["estado"],
                name="vat_inscofe_estado_idx",
            ),
        ]


# ============================================================================
# FASE 5: SISTEMA DE VOUCHERS
# ============================================================================


class VoucherParametria(models.Model):
    """
    Plantilla de voucher: define los parámetros base (programa, créditos,
    vencimiento) que luego se usan para asignar vouchers a ciudadanos.
    """

    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    programa = models.ForeignKey(
        Programa,
        on_delete=models.PROTECT,
        related_name="vat_voucher_parametrias",
        verbose_name="Programa",
    )
    cantidad_inicial = models.PositiveIntegerField(
        verbose_name="Créditos por ciudadano"
    )
    fecha_vencimiento = models.DateField(verbose_name="Fecha de vencimiento")
    RENOVACION_TIPO_CHOICES = [
        ("suma", "Sumar al saldo existente"),
        ("reinicia", "Reiniciar al valor configurado"),
    ]

    renovacion_mensual = models.BooleanField(
        default=False, verbose_name="Renovación mensual"
    )
    cantidad_renovacion = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Créditos en cada renovación",
        help_text="Si está vacío se usa la cantidad inicial.",
    )
    renovacion_tipo = models.CharField(
        max_length=10,
        choices=RENOVACION_TIPO_CHOICES,
        default="suma",
        verbose_name="Tipo de renovación",
    )
    inscripcion_unica_activa = models.BooleanField(
        default=False,
        verbose_name="Inscripción única activa",
        help_text=(
            "Si está activado, el ciudadano solo puede tener una inscripción "
            "activa a la vez en comisiones de este programa. Debe completar o "
            "abandonar la inscripción actual antes de inscribirse en otra."
        ),
    )
    activa = models.BooleanField(default=True, verbose_name="Activa")
    creado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="vat_voucher_parametrias_creadas",
        verbose_name="Creado por",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} ({self.programa})"

    class Meta:
        verbose_name = "Parametría de Voucher"
        verbose_name_plural = "Parametrías de Voucher"
        ordering = ["-fecha_creacion"]


class Voucher(SoftDeleteModelMixin, models.Model):
    """
    Representa una asignación de crédito de formación a un ciudadano.
    Un voucher permite acceso a un cierto número de horas/cupos de formación.
    """

    ESTADO_CHOICES = [
        ("activo", "Activo"),
        ("vencido", "Vencido"),
        ("agotado", "Agotado"),
        ("cancelado", "Cancelado"),
    ]

    parametria = models.ForeignKey(
        VoucherParametria,
        on_delete=models.PROTECT,
        related_name="vouchers",
        verbose_name="Parametría",
        null=True,
        blank=True,
    )
    ciudadano = models.ForeignKey(
        Ciudadano,
        on_delete=models.CASCADE,
        related_name="vat_vouchers",
        verbose_name="Ciudadano",
    )
    programa = models.ForeignKey(
        Programa,
        on_delete=models.PROTECT,
        related_name="vat_vouchers",
        verbose_name="Programa",
    )

    cantidad_inicial = models.PositiveIntegerField(verbose_name="Cantidad Inicial")
    cantidad_usada = models.PositiveIntegerField(
        default=0, verbose_name="Cantidad Usada"
    )
    cantidad_disponible = models.PositiveIntegerField(
        verbose_name="Cantidad Disponible"
    )

    fecha_asignacion = models.DateField(
        auto_now_add=True, verbose_name="Fecha de Asignación"
    )
    fecha_vencimiento = models.DateField(verbose_name="Fecha de Vencimiento")

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="activo",
        verbose_name="Estado",
    )

    asignado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="vat_vouchers_asignados",
        verbose_name="Asignado por",
        null=True,
        blank=True,
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Voucher {self.ciudadano} - {self.cantidad_disponible}/{self.cantidad_inicial}"

    class Meta:
        verbose_name = "Voucher"
        verbose_name_plural = "Vouchers"
        ordering = ["-fecha_asignacion"]
        indexes = [
            models.Index(
                fields=["ciudadano", "estado"],
                name="vat_vouch_ciud_est_idx",
            ),
            models.Index(fields=["estado"], name="vat_voucher_estado_idx"),
            models.Index(
                fields=["fecha_vencimiento"], name="vat_voucher_vencimiento_idx"
            ),
        ]


class VoucherRecarga(SoftDeleteModelMixin, models.Model):
    """
    Registro de cada recarga de crédito de un voucher.
    Mantiene el historial de recargas (automáticas, manuales, ajustes).
    """

    MOTIVO_CHOICES = [
        ("automatica", "Recarga Automática"),
        ("manual", "Recarga Manual"),
        ("ajuste", "Ajuste"),
        ("compensacion", "Compensación"),
    ]

    voucher = models.ForeignKey(
        Voucher,
        on_delete=models.CASCADE,
        related_name="recargas",
        verbose_name="Voucher",
    )
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad Recargada")
    fecha_recarga = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Recarga"
    )

    motivo = models.CharField(
        max_length=20,
        choices=MOTIVO_CHOICES,
        verbose_name="Motivo de Recarga",
    )

    autorizado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="vat_recargas_voucher",
        verbose_name="Autorizado por",
    )

    def __str__(self):
        return f"Recarga {self.voucher} - {self.cantidad} ({self.get_motivo_display()})"

    class Meta:
        verbose_name = "Recarga de Voucher"
        verbose_name_plural = "Recargas de Voucher"
        ordering = ["-fecha_recarga"]


class VoucherUso(SoftDeleteModelMixin, models.Model):
    """
    Registro de uso de voucher cuando un ciudadano se inscribe a una oferta.
    Descuenta créditos del voucher disponible.
    """

    voucher = models.ForeignKey(
        Voucher,
        on_delete=models.CASCADE,
        related_name="usos",
        verbose_name="Voucher",
    )
    inscripcion_oferta = models.ForeignKey(
        InscripcionOferta,
        on_delete=models.CASCADE,
        related_name="vat_voucher_usos",
        verbose_name="Inscripción a Oferta",
    )
    cantidad_usada = models.PositiveIntegerField(verbose_name="Cantidad Usada")
    fecha_uso = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Uso")

    def __str__(self):
        return f"Uso {self.voucher} - {self.cantidad_usada} en {self.inscripcion_oferta.oferta}"

    class Meta:
        verbose_name = "Uso de Voucher"
        verbose_name_plural = "Usos de Voucher"
        ordering = ["-fecha_uso"]
        indexes = [
            models.Index(
                fields=["voucher", "fecha_uso"], name="vat_vuso_vouch_fecha_idx"
            ),
        ]


class VoucherLog(models.Model):
    """
    Log de auditoría immutable para eventos de voucher.
    No usa soft delete - es histórico y debe ser preservado.
    """

    TIPO_EVENTO_CHOICES = [
        ("asignacion", "Asignación"),
        ("recarga", "Recarga"),
        ("uso", "Uso"),
        ("vencimiento", "Vencimiento"),
        ("cancelacion", "Cancelación"),
    ]

    voucher = models.ForeignKey(
        Voucher,
        on_delete=models.CASCADE,
        related_name="logs",
        verbose_name="Voucher",
    )

    tipo_evento = models.CharField(
        max_length=20,
        choices=TIPO_EVENTO_CHOICES,
        verbose_name="Tipo de Evento",
    )

    cantidad_afectada = models.IntegerField(verbose_name="Cantidad Afectada")
    fecha_evento = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha del Evento"
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="vat_logs_voucher",
        verbose_name="Usuario",
    )
    detalles = models.JSONField(
        default=dict, blank=True, verbose_name="Detalles Adicionales"
    )

    def __str__(self):
        return (
            f"{self.get_tipo_evento_display()} - {self.voucher} ({self.fecha_evento})"
        )

    class Meta:
        verbose_name = "Log de Voucher"
        verbose_name_plural = "Logs de Voucher"
        ordering = ["-fecha_evento"]
        indexes = [
            models.Index(
                fields=["voucher", "fecha_evento"],
                name="vat_vlog_vouch_fecha_idx",
            ),
            models.Index(fields=["tipo_evento"], name="vat_vlog_tipo_evt_idx"),
        ]


# ============================================================================
# FASE 2 (COMPLETA): INSTITUCIÓN - CONTACTOS E IDENTIFICADORES
# ============================================================================


class InstitucionContacto(models.Model):
    """
    Datos de contacto asociados a una institución (Centro).
    Permite múltiples contactos (email, teléfono, web, etc).
    """

    TIPO_CONTACTO_CHOICES = [
        ("email", "Email"),
        ("telefono", "Teléfono"),
        ("celular", "Celular"),
        ("sitio_web", "Sitio Web"),
        ("redes_sociales", "Redes Sociales"),
    ]

    centro = models.ForeignKey(
        Centro,
        on_delete=models.CASCADE,
        related_name="contactos_adicionales",
        verbose_name="Centro",
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CONTACTO_CHOICES,
        verbose_name="Tipo de Contacto",
    )
    valor = models.CharField(max_length=255, verbose_name="Valor")
    nombre_contacto = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Nombre del Contacto",
    )
    rol_area = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Rol / Área",
    )
    telefono_contacto = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Teléfono del Contacto",
    )
    email_contacto = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Correo del Contacto",
    )
    es_principal = models.BooleanField(default=False, verbose_name="Es Principal")
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )
    vigencia_desde = models.DateField(auto_now_add=True, verbose_name="Vigencia Desde")
    vigencia_hasta = models.DateField(
        blank=True, null=True, verbose_name="Vigencia Hasta"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.centro} - {self.get_tipo_display()}: {self.valor}"

    class Meta:
        verbose_name = "Contacto de Institución"
        verbose_name_plural = "Contactos de Institución"
        ordering = ["-es_principal", "tipo"]
        unique_together = ("centro", "tipo", "valor")


class AutoridadInstitucional(models.Model):
    """
    Representante legal/administrativo de la institución (Centro).
    """

    centro = models.ForeignKey(
        Centro,
        on_delete=models.CASCADE,
        related_name="autoridades",
        verbose_name="Centro",
    )
    nombre_completo = models.CharField(max_length=255, verbose_name="Nombre Completo")
    dni = models.CharField(max_length=20, verbose_name="DNI")
    cargo = models.CharField(max_length=100, verbose_name="Cargo")
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    es_actual = models.BooleanField(default=True, verbose_name="Es la Autoridad Actual")
    vigencia_desde = models.DateField(auto_now_add=True, verbose_name="Vigencia Desde")
    vigencia_hasta = models.DateField(
        blank=True, null=True, verbose_name="Vigencia Hasta"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.centro} - {self.nombre_completo} ({self.cargo})"

    class Meta:
        verbose_name = "Autoridad de Institución"
        verbose_name_plural = "Autoridades de Institución"
        ordering = ["-es_actual", "-vigencia_desde"]


class InstitucionIdentificadorHist(models.Model):
    """
    Registro histórico de identificadores de institución.
    (ej: CUIE, CUE, códigos provinciales, etc)
    """

    TIPO_IDENTIFICADOR_CHOICES = [
        ("cuie", "CUIE"),
        ("cue", "CUE"),
        ("codigo_provincial", "Código Provincial"),
        ("ruc", "RUC"),
        ("cuit", "CUIT"),
        ("otro", "Otro"),
    ]

    ROL_INSTITUCIONAL_CHOICES = [
        ("sede", "Sede"),
        ("anexo", "Anexo"),
        ("polo", "Polo"),
        ("centro_de_formacion", "Centro de Formación"),
    ]

    centro = models.ForeignKey(
        Centro,
        on_delete=models.CASCADE,
        related_name="identificadores_hist",
        verbose_name="Centro",
    )
    tipo_identificador = models.CharField(
        max_length=20,
        choices=TIPO_IDENTIFICADOR_CHOICES,
        verbose_name="Tipo de Identificador",
    )
    valor_identificador = models.CharField(
        max_length=100, verbose_name="Valor del Identificador"
    )
    rol_institucional = models.CharField(
        max_length=50,
        choices=ROL_INSTITUCIONAL_CHOICES,
        blank=True,
        null=True,
        verbose_name="Rol Institucional",
    )
    ubicacion = models.ForeignKey(
        "InstitucionUbicacion",
        on_delete=models.SET_NULL,
        related_name="identificadores_hist",
        blank=True,
        null=True,
        verbose_name="Ubicación asociada",
    )
    es_actual = models.BooleanField(default=True, verbose_name="Es Actual")
    vigencia_desde = models.DateField(auto_now_add=True, verbose_name="Vigencia Desde")
    vigencia_hasta = models.DateField(
        blank=True, null=True, verbose_name="Vigencia Hasta"
    )
    motivo = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Motivo del Cambio",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.ubicacion_id:
            return (
                f"{self.centro} - {self.get_tipo_identificador_display()}: "
                f"{self.valor_identificador} ({self.ubicacion})"
            )
        return f"{self.centro} - {self.get_tipo_identificador_display()}: {self.valor_identificador}"

    class Meta:
        verbose_name = "Identificador Histórico de Institución"
        verbose_name_plural = "Identificadores Históricos de Institución"
        ordering = ["-es_actual", "-vigencia_desde"]
        unique_together = ("centro", "tipo_identificador", "valor_identificador")


class InstitucionUbicacion(models.Model):
    """
    Vinculación entre Centro e ubicación con rol específico.
    Permite que un centro tenga múltiples ubicaciones (sede, anexo, etc).
    """

    ROL_UBICACION_CHOICES = [
        ("sede_principal", "Sede Principal"),
        ("anexo", "Anexo"),
        ("dependencia", "Dependencia"),
        ("punto_de_atencion", "Punto de Atención"),
    ]

    centro = models.ForeignKey(
        Centro,
        on_delete=models.CASCADE,
        related_name="ubicaciones",
        verbose_name="Centro",
    )
    localidad = models.ForeignKey(
        Localidad,
        on_delete=models.PROTECT,
        related_name="instituciones_ubicacion",
        verbose_name="Localidad",
    )
    rol_ubicacion = models.CharField(
        max_length=50,
        choices=ROL_UBICACION_CHOICES,
        verbose_name="Rol de Ubicación",
    )
    nombre_ubicacion = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        verbose_name="Nombre de Ubicación",
        help_text="Ejemplo: Sede Centro, Anexo Norte, Punto Barrio Sur.",
    )
    domicilio = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Domicilio"
    )
    es_principal = models.BooleanField(default=False, verbose_name="Es Principal")
    latitud = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitud = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True
    )
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )
    vigencia_desde = models.DateField(auto_now_add=True, verbose_name="Vigencia Desde")
    vigencia_hasta = models.DateField(
        blank=True, null=True, verbose_name="Vigencia Hasta"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        nombre = self.nombre_ubicacion or self.get_rol_ubicacion_display()
        return f"{self.centro} - {nombre} ({self.localidad})"

    class Meta:
        verbose_name = "Ubicación de Institución"
        verbose_name_plural = "Ubicaciones de Institución"
        ordering = ["-es_principal", "rol_ubicacion"]
        unique_together = ("centro", "localidad", "rol_ubicacion")


# ============================================================================
# CURSOS (NUEVA CAPA OPERATIVA POR CENTRO)
# ============================================================================


class Curso(SoftDeleteModelMixin, models.Model):
    """Curso operativo de un centro con ubicación y modalidad."""

    ESTADO_CURSO_CHOICES = [
        ("planificado", "Planificado"),
        ("activo", "Activo"),
        ("finalizado", "Finalizado"),
        ("cancelado", "Cancelado"),
    ]

    centro = models.ForeignKey(
        Centro,
        on_delete=models.CASCADE,
        related_name="cursos",
        verbose_name="Centro",
    )
    ubicacion = models.ForeignKey(
        InstitucionUbicacion,
        on_delete=models.PROTECT,
        related_name="cursos",
        verbose_name="Ubicación",
    )
    nombre = models.CharField(max_length=255, verbose_name="Nombre")
    modalidad = models.ForeignKey(
        ModalidadCursada,
        on_delete=models.PROTECT,
        related_name="cursos",
        verbose_name="Modalidad",
    )
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de Fin")
    cupo_total = models.PositiveIntegerField(verbose_name="Cupo Total")
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CURSO_CHOICES,
        default="planificado",
        verbose_name="Estado",
    )
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.fecha_inicio and self.fecha_fin and self.fecha_inicio > self.fecha_fin:
            raise ValidationError(
                {
                    "fecha_fin": "La fecha de fin debe ser mayor o igual a la fecha de inicio."
                }
            )

        if self.cupo_total is not None and self.cupo_total == 0:
            raise ValidationError({"cupo_total": "El cupo total debe ser mayor a 0."})

        if (
            self.ubicacion_id
            and self.centro_id
            and self.ubicacion.centro_id != self.centro_id
        ):
            raise ValidationError(
                {
                    "ubicacion": "La ubicación seleccionada no pertenece al centro del curso."
                }
            )

    def __str__(self):
        return f"{self.nombre} - {self.centro}"

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ["-fecha_inicio", "nombre"]
        indexes = [
            models.Index(
                fields=["centro", "estado"], name="vat_curso_centro_estado_idx"
            ),
            models.Index(fields=["estado"], name="vat_curso_estado_idx"),
        ]


class ComisionCurso(SoftDeleteModelMixin, models.Model):
    """Comisión asociada a un curso."""

    ESTADO_COMISION_CURSO_CHOICES = [
        ("planificada", "Planificada"),
        ("activa", "Activa"),
        ("cerrada", "Cerrada"),
        ("suspendida", "Suspendida"),
    ]

    curso = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name="comisiones",
        verbose_name="Curso",
    )
    codigo_comision = models.CharField(max_length=50, verbose_name="Código de Comisión")
    nombre = models.CharField(max_length=255, verbose_name="Nombre")
    cupo_total = models.PositiveIntegerField(verbose_name="Cupo Total")
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de Fin")
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_COMISION_CURSO_CHOICES,
        default="planificada",
        verbose_name="Estado",
    )
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.fecha_inicio and self.fecha_fin and self.fecha_inicio > self.fecha_fin:
            raise ValidationError(
                {
                    "fecha_fin": "La fecha de fin debe ser mayor o igual a la fecha de inicio."
                }
            )

        if self.cupo_total is not None and self.cupo_total == 0:
            raise ValidationError({"cupo_total": "El cupo total debe ser mayor a 0."})

        if self.curso_id:
            if (
                self.cupo_total
                and self.curso.cupo_total
                and self.cupo_total > self.curso.cupo_total
            ):
                raise ValidationError(
                    {
                        "cupo_total": (
                            "El cupo total de la comisión no puede superar el cupo total del curso."
                        )
                    }
                )
            if (
                self.fecha_inicio
                and self.curso.fecha_inicio
                and self.fecha_inicio < self.curso.fecha_inicio
            ):
                raise ValidationError(
                    {
                        "fecha_inicio": (
                            "La fecha de inicio de la comisión debe estar dentro del rango del curso."
                        )
                    }
                )
            if (
                self.fecha_fin
                and self.curso.fecha_fin
                and self.fecha_fin > self.curso.fecha_fin
            ):
                raise ValidationError(
                    {
                        "fecha_fin": (
                            "La fecha de fin de la comisión debe estar dentro del rango del curso."
                        )
                    }
                )

    def __str__(self):
        return f"{self.codigo_comision} - {self.nombre}"

    class Meta:
        verbose_name = "Comisión de Curso"
        verbose_name_plural = "Comisiones de Curso"
        ordering = ["codigo_comision"]
        unique_together = ("curso", "codigo_comision")
        indexes = [
            models.Index(
                fields=["curso", "estado"], name="vat_comcurso_curso_estado_idx"
            ),
        ]


# ============================================================================
# FASE 4 (COMPLETA): OFERTA INSTITUCIONAL - COMISIONES
# ============================================================================


class OfertaInstitucional(SoftDeleteModelMixin, models.Model):
    """
    Oferta educativa de una institución basada en un plan de estudio.
    Representa la intención de ofertar una carrera/programa en un período.
    """

    ESTADO_OFERTA_CHOICES = [
        ("planificada", "Planificada"),
        ("aprobada", "Aprobada"),
        ("publicada", "Publicada"),
        ("cerrada", "Cerrada"),
        ("cancelada", "Cancelada"),
    ]

    centro = models.ForeignKey(
        Centro,
        on_delete=models.CASCADE,
        related_name="ofertas_institucionales",
        verbose_name="Centro",
    )
    plan_curricular = models.ForeignKey(
        PlanVersionCurricular,
        on_delete=models.PROTECT,
        related_name="ofertas_institucionales",
        verbose_name="Plan de Estudio",
    )
    programa = models.ForeignKey(
        Programa,
        on_delete=models.PROTECT,
        related_name="ofertas_vat",
        verbose_name="Programa",
    )

    nombre_local = models.CharField(
        max_length=255, verbose_name="Nombre Local (si aplica)", blank=True
    )
    ciclo_lectivo = models.IntegerField(verbose_name="Ciclo Lectivo")
    plan_externo_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="ID Plan Externo",
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_OFERTA_CHOICES,
        default="planificada",
        verbose_name="Estado de Oferta",
    )

    costo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Costo",
        help_text="Costo del curso en pesos. 0 = gratuito.",
    )
    usa_voucher = models.BooleanField(
        default=False,
        verbose_name="Usa Voucher",
        help_text="Si está activo, al inscribirse un ciudadano se valida y descuenta un crédito de su voucher.",
    )
    voucher_parametrias = models.ManyToManyField(
        "VoucherParametria",
        related_name="ofertas_institucionales",
        blank=True,
        verbose_name="Vouchers habilitados",
        help_text="Parametrías de voucher permitidas para esta oferta.",
    )
    fecha_publicacion = models.DateField(
        blank=True, null=True, verbose_name="Fecha de Publicación"
    )

    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        nombre = self.nombre_local or self.plan_curricular.titulo_referencia.nombre
        return f"{self.centro} - {nombre} ({self.ciclo_lectivo})"

    class Meta:
        verbose_name = "Oferta Institucional"
        verbose_name_plural = "Ofertas Institucionales"
        ordering = ["-ciclo_lectivo"]
        unique_together = ("centro", "plan_curricular", "ciclo_lectivo")
        indexes = [
            models.Index(
                fields=["centro", "estado"],
                name="vat_ofeinst_ce_est_idx",
            ),
            models.Index(fields=["estado"], name="vat_ofeinst_estado_idx"),
        ]


class Comision(SoftDeleteModelMixin, models.Model):
    """
    Comisión o grupo de estudiantes para una oferta.
    Agrupa encuentros y estudiantes inscritos.
    """

    ESTADO_COMISION_CHOICES = [
        ("planificada", "Planificada"),
        ("activa", "Activa"),
        ("cerrada", "Cerrada"),
        ("suspendida", "Suspendida"),
    ]

    oferta = models.ForeignKey(
        OfertaInstitucional,
        on_delete=models.CASCADE,
        related_name="comisiones",
        verbose_name="Oferta Institucional",
    )
    ubicacion = models.ForeignKey(
        InstitucionUbicacion,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="comisiones",
        verbose_name="Ubicación",
    )

    codigo_comision = models.CharField(
        max_length=50, unique=True, verbose_name="Código de Comisión"
    )
    nombre = models.CharField(max_length=255, verbose_name="Nombre")
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de Fin")
    cupo = models.PositiveIntegerField(verbose_name="Cupo Total")
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_COMISION_CHOICES,
        default="planificada",
        verbose_name="Estado",
    )
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.cupo is not None and self.cupo == 0:
            raise ValidationError({"cupo": "El cupo debe ser mayor a 0."})

    def __str__(self):
        return f"{self.codigo_comision} - {self.nombre}"

    class Meta:
        verbose_name = "Comisión"
        verbose_name_plural = "Comisiones"
        ordering = ["codigo_comision"]
        indexes = [
            models.Index(
                fields=["oferta", "estado"],
                name="vat_comision_oferta_estado_idx",
            ),
        ]


class ComisionHorario(models.Model):
    """
    Horario específico de una comisión.
    Una comisión puede tener múltiples horarios (ej: clases y tutorías).
    """

    comision = models.ForeignKey(
        Comision,
        on_delete=models.CASCADE,
        related_name="horarios",
        verbose_name="Comisión",
    )
    dia_semana = models.ForeignKey(
        Dia,
        on_delete=models.PROTECT,
        related_name="horarios_comisiones",
        verbose_name="Día de la Semana",
    )
    hora_desde = models.TimeField(verbose_name="Hora Desde")
    hora_hasta = models.TimeField(verbose_name="Hora Hasta")
    aula_espacio = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Aula/Espacio",
    )
    vigente = models.BooleanField(default=True, verbose_name="Vigente")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"{self.comision} - {self.dia_semana} {self.hora_desde}-{self.hora_hasta}"
        )

    class Meta:
        verbose_name = "Horario de Comisión"
        verbose_name_plural = "Horarios de Comisión"
        ordering = ["comision", "dia_semana", "hora_desde"]
        unique_together = (
            "comision",
            "dia_semana",
            "hora_desde",
            "hora_hasta",
        )


class SesionComision(models.Model):
    """
    Instancia concreta de una sesión de una comisión.
    Se genera automáticamente a partir de los ComisionHorario y
    el rango fecha_inicio/fecha_fin de la Comision.
    Ejemplo: si hay un horario "Lunes 10-12" y la comisión dura un mes,
    se crean ~4 SesionComision (una por cada lunes del período).
    """

    ESTADO_CHOICES = [
        ("programada", "Programada"),
        ("realizada", "Realizada"),
        ("cancelada", "Cancelada"),
    ]

    comision = models.ForeignKey(
        Comision,
        on_delete=models.CASCADE,
        related_name="sesiones",
        verbose_name="Comisión",
    )
    horario = models.ForeignKey(
        ComisionHorario,
        on_delete=models.CASCADE,
        related_name="sesiones",
        verbose_name="Horario",
    )
    numero_sesion = models.PositiveIntegerField(verbose_name="Número de sesión")
    fecha = models.DateField(verbose_name="Fecha")
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="programada",
        verbose_name="Estado",
    )
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sesión #{self.numero_sesion} — {self.comision} ({self.fecha})"

    class Meta:
        verbose_name = "Sesión de Comisión"
        verbose_name_plural = "Sesiones de Comisión"
        ordering = ["fecha", "horario__hora_desde"]
        unique_together = ("comision", "horario", "fecha")
        indexes = [
            models.Index(
                fields=["comision", "estado"], name="vat_sesion_comision_estado_idx"
            ),
        ]


# ============================================================================
# FASE 5: INSCRIPCIÓN
# ============================================================================


class Inscripcion(SoftDeleteModelMixin, models.Model):
    """
    Inscripción de una Persona a una Comisión.
    Registra la relación ciudadano ↔ comisión con estado y validación.
    """

    ESTADO_INSCRIPCION_CHOICES = [
        ("pre_inscripta", "Pre-inscripta"),
        ("inscripta", "Inscripta"),
        ("validada_presencial", "Validada Presencial"),
        ("completada", "Completada"),
        ("abandonada", "Abandonada"),
        ("rechazada", "Rechazada"),
    ]

    ORIGEN_CANAL_CHOICES = [
        ("front_publico", "Front Público"),
        ("backoffice", "Backoffice"),
        ("api", "API"),
        ("importacion", "Importación"),
    ]

    ciudadano = models.ForeignKey(
        Ciudadano,
        on_delete=models.PROTECT,
        related_name="inscripciones_vat",
        verbose_name="Ciudadano",
    )
    comision = models.ForeignKey(
        Comision,
        on_delete=models.CASCADE,
        related_name="inscripciones",
        verbose_name="Comisión",
    )
    programa = models.ForeignKey(
        Programa,
        on_delete=models.PROTECT,
        related_name="inscripciones_vat",
        verbose_name="Programa",
    )

    estado = models.CharField(
        max_length=30,
        choices=ESTADO_INSCRIPCION_CHOICES,
        default="pre_inscripta",
        verbose_name="Estado",
    )
    origen_canal = models.CharField(
        max_length=30,
        choices=ORIGEN_CANAL_CHOICES,
        default="backoffice",
        verbose_name="Origen del Canal",
    )

    fecha_inscripcion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Inscripción"
    )
    fecha_validacion_presencial = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de Validación Presencial",
    )
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.ciudadano.nombre_completo} - {self.comision.codigo_comision} [{self.estado}]"

    class Meta:
        verbose_name = "Inscripción"
        verbose_name_plural = "Inscripciones"
        ordering = ["-fecha_inscripcion"]
        unique_together = ("ciudadano", "comision")
        indexes = [
            models.Index(
                fields=["comision", "estado"],
                name="vat_insc_com_est_idx",
            ),
            models.Index(
                fields=["ciudadano", "estado"],
                name="vat_insc_ciu_est_idx",
            ),
        ]


# ============================================================================
# FASE 6: ASISTENCIA
# ============================================================================


class AsistenciaSesion(models.Model):
    """
    Registro de asistencia de un inscripto a una sesión concreta de la comisión.
    Se crea una fila por cada (sesion, inscripcion); presente=True indica asistió.
    """

    sesion = models.ForeignKey(
        SesionComision,
        on_delete=models.CASCADE,
        related_name="asistencias",
        verbose_name="Sesión",
    )
    inscripcion = models.ForeignKey(
        "Inscripcion",
        on_delete=models.CASCADE,
        related_name="asistencias",
        verbose_name="Inscripción",
    )
    presente = models.BooleanField(default=False, verbose_name="Presente")
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )
    registrado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="asistencias_registradas",
        verbose_name="Registrado por",
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Registro"
    )

    def __str__(self):
        estado = "Presente" if self.presente else "Ausente"
        return (
            f"{self.inscripcion.ciudadano.nombre_completo} — {self.sesion} [{estado}]"
        )

    class Meta:
        verbose_name = "Asistencia a Sesión"
        verbose_name_plural = "Asistencias a Sesiones"
        unique_together = ("sesion", "inscripcion")
        indexes = [
            models.Index(fields=["sesion", "presente"], name="vat_asist_ses_pres_idx"),
        ]


# ============================================================================
# FASE 7: EVALUACIONES
# ============================================================================


class Evaluacion(models.Model):
    """
    Instancia de evaluación en una comisión.
    Define qué se evalúa, cuándo y características.
    """

    TIPO_EVALUACION_CHOICES = [
        ("parcial", "Parcial"),
        ("final", "Final"),
        ("integradora", "Integradora"),
        ("recuperatorio", "Recuperatorio"),
    ]

    comision = models.ForeignKey(
        Comision,
        on_delete=models.CASCADE,
        related_name="evaluaciones",
        verbose_name="Comisión",
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_EVALUACION_CHOICES,
        verbose_name="Tipo de Evaluación",
    )
    nombre = models.CharField(max_length=255, verbose_name="Nombre de la Evaluación")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    fecha = models.DateField(verbose_name="Fecha de la Evaluación")
    es_final = models.BooleanField(default=False, verbose_name="Es Evaluación Final")
    ponderacion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100,
        help_text="Ponderación en la calificación final (%)",
        verbose_name="Ponderación (%)",
    )
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.comision.codigo_comision} - {self.nombre} ({self.get_tipo_display()})"

    class Meta:
        verbose_name = "Evaluación"
        verbose_name_plural = "Evaluaciones"
        ordering = ["comision", "fecha"]
        indexes = [
            models.Index(
                fields=["comision", "tipo"],
                name="vat_eval_com_tipo_idx",
            ),
        ]


class ResultadoEvaluacion(SoftDeleteModelMixin, models.Model):
    """
    Resultado de evaluación de un inscripto.
    Registra calificación, aprobación y observaciones.
    """

    evaluacion = models.ForeignKey(
        Evaluacion,
        on_delete=models.CASCADE,
        related_name="resultados",
        verbose_name="Evaluación",
    )
    inscripcion = models.ForeignKey(
        Inscripcion,
        on_delete=models.CASCADE,
        related_name="resultados_evaluacion",
        verbose_name="Inscripción",
    )

    calificacion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Calificación",
    )
    aprobo = models.BooleanField(null=True, blank=True, verbose_name="¿Aprobó?")
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Registro"
    )
    registrado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="evaluaciones_registradas",
        verbose_name="Registrado por",
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.inscripcion.ciudadano.nombre_completo} - {self.evaluacion.nombre}: {self.calificacion}"

    class Meta:
        verbose_name = "Resultado de Evaluación"
        verbose_name_plural = "Resultados de Evaluación"
        ordering = ["-fecha_registro"]
        unique_together = ("evaluacion", "inscripcion")
        indexes = [
            models.Index(
                fields=["evaluacion", "aprobo"],
                name="vat_reseval_eval_apr_idx",
            ),
        ]
