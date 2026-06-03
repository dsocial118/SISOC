from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from core.models import Localidad, Municipio, Provincia
from core.soft_delete import SoftDeleteModelMixin


class EstadoItinerario(models.TextChoices):
    BORRADOR = "borrador", "Borrador"
    PRESENTADO = "presentado", "Presentado"
    EN_REVISION = "en_revision", "En revision Nacion"
    OBSERVADO = "observado", "Observado"
    EN_SUBSANACION = "en_subsanacion", "En subsanacion"
    SUBSANADO = "subsanado", "Subsanado"
    APROBADO = "aprobado", "Aprobado"
    RECHAZADO = "rechazado", "Rechazado"
    EN_EJECUCION = "en_ejecucion", "En ejecucion"
    EN_POST_OPERATIVO = "en_post_operativo", "En post-operativo"
    CERRADO = "cerrado", "Cerrado"
    CANCELADO = "cancelado", "Cancelado"


class EstadoJornada(models.TextChoices):
    PLANIFICADA = "planificada", "Planificada"
    CHECKLIST_PENDIENTE = "checklist_pendiente", "Pendiente checklist"
    PENDIENTE_HABILITACION = "pendiente_habilitacion", "Pendiente habilitacion"
    HABILITADA = "habilitada", "Habilitada"
    EN_PROGRESO = "en_progreso", "En progreso"
    PENDIENTE_CIERRE = "pendiente_cierre", "Pendiente de cierre"
    PENDIENTE_CIERRE_OBSERVADA = (
        "pendiente_cierre_observada",
        "Pendiente cierre observada",
    )
    FINALIZADA = "finalizada", "Finalizada"
    CERRADA = "cerrada", "Cerrada"
    EN_POST_OPERATIVO = "en_post_operativo", "En post-operativo"
    CERRADA_FINAL = "cerrada_final", "Cerrada final"
    OBSERVADA = "observada", "Observada"


class ResultadoAtencion(models.TextChoices):
    ENTREGADO_DIA = "entregado_dia", "Entregado en el dia"
    ENVIADO_LABORATORIO = "enviado_laboratorio", "Enviado a laboratorio"
    NO_REQUIERE = "no_requiere", "No requiere anteojos"
    DERIVADO = "derivado", "Derivado"


class EstadoRegistroNominal(models.TextChoices):
    CARGADO = "cargado", "Cargado"
    VALIDADO = "validado", "Validado"
    OBSERVADO = "observado", "Observado"
    CORREGIDO = "corregido", "Corregido"
    CERRADO = "cerrado", "Cerrado"


class EstadoLaboratorio(models.TextChoices):
    PENDIENTE_ENVIO = "pendiente_envio", "Pendiente de envio"
    ENVIADO = "enviado", "Enviado a laboratorio"
    EN_PRODUCCION = "en_produccion", "En produccion"
    ENVIADO_NACION = "enviado_nacion", "Enviado a Nacion"
    ENVIADO_PROVINCIA = "enviado_provincia", "Enviado a provincia"
    RECIBIDO = "recibido", "Recibido"
    ENTREGADO = "entregado", "Entregado"
    CERRADO = "cerrado", "Cerrado"
    INCIDENCIA = "incidencia", "Incidencia"


class EstadoEvaluacionVPSL(models.TextChoices):
    PENDIENTE = "pendiente", "Pendiente"
    APROBADO = "aprobado", "Aprobado"
    RECHAZADO = "rechazado", "Rechazado"
    SUBSANAR = "subsanar", "Subsanar"


class SedeVPSL(SoftDeleteModelMixin, models.Model):
    jurisdiccion = models.CharField(max_length=255)
    sector = models.CharField(max_length=64)
    ambito = models.CharField(max_length=64)
    departamento = models.CharField(max_length=255)
    codigo_departamento = models.CharField(max_length=32)
    localidad = models.CharField(max_length=255)
    codigo_localidad = models.CharField(max_length=32)
    cueanexo = models.CharField(max_length=32, unique=True)
    nombre = models.CharField(max_length=255)
    domicilio = models.CharField(max_length=255)
    codigo_postal = models.CharField(max_length=16, blank=True)
    telefono = models.CharField(max_length=80, blank=True)
    mail = models.TextField(blank=True)
    checklist_aprobado = models.BooleanField(default=False)
    latitud = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
    )
    longitud = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["jurisdiccion", "localidad", "nombre"]
        verbose_name = "Sede VPSL"
        verbose_name_plural = "Sedes VPSL"
        indexes = [
            models.Index(fields=["nombre"]),
            models.Index(fields=["cueanexo"]),
        ]

    def __str__(self):
        return f"{self.nombre} - {self.domicilio}"

    @property
    def mapa_query(self):
        if self.latitud is not None and self.longitud is not None:
            return f"{self.latitud},{self.longitud}"
        return f"{self.nombre}, {self.domicilio}, {self.localidad}, {self.jurisdiccion}"


class ItinerarioVPSL(SoftDeleteModelMixin, models.Model):
    provincia = models.ForeignKey(Provincia, on_delete=models.PROTECT)
    codigo = models.CharField(max_length=32, unique=True, blank=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    localidades_tentativas = models.TextField(blank=True)
    sedes_tentativas = models.TextField(blank=True)
    matricula_estimada = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
    )
    referente_nombre = models.CharField(max_length=255)
    referente_apellido = models.CharField(max_length=255, blank=True)
    referente_telefono = models.CharField(max_length=50, blank=True)
    referente_email = models.EmailField(blank=True)
    carta_referencia = models.CharField(max_length=255, blank=True)
    carta_referencia_estado = models.CharField(
        max_length=16,
        choices=EstadoEvaluacionVPSL.choices,
        default=EstadoEvaluacionVPSL.PENDIENTE,
    )
    carta_archivo = models.FileField(
        upload_to="ver_para_ser_libre/cartas/",
        blank=True,
        null=True,
    )
    carta_archivo_estado = models.CharField(
        max_length=16,
        choices=EstadoEvaluacionVPSL.choices,
        default=EstadoEvaluacionVPSL.PENDIENTE,
    )
    estado = models.CharField(
        max_length=32,
        choices=EstadoItinerario.choices,
        default=EstadoItinerario.BORRADOR,
        db_index=True,
    )
    observaciones = models.TextField(blank=True)
    subsanacion_observaciones = models.TextField(blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="itinerarios_vpsl_creados",
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="itinerarios_vpsl_modificados",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sedes = models.ManyToManyField(
        SedeVPSL,
        blank=True,
        related_name="itinerarios",
    )

    class Meta:
        ordering = ["-fecha_inicio", "provincia__nombre"]
        verbose_name = "Itinerario VPSL"
        verbose_name_plural = "Itinerarios VPSL"
        indexes = [
            models.Index(fields=["estado", "fecha_inicio"]),
            models.Index(fields=["provincia", "estado"]),
        ]

    def __str__(self):
        return f"{self.codigo or 'VPSL'} - {self.provincia}"

    def clean(self):
        super().clean()
        errors = {}
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            errors["fecha_fin"] = "La fecha de fin no puede ser anterior al inicio."
        if not self.carta_archivo:
            errors["carta_archivo"] = "Debe adjuntar carta archivo."
        if self.estado != EstadoItinerario.EN_SUBSANACION:
            required_text_fields = {
                "referente_nombre": self.referente_nombre,
                "referente_telefono": self.referente_telefono,
                "referente_email": self.referente_email,
            }
            for field_name, value in required_text_fields.items():
                if not str(value or "").strip():
                    errors[field_name] = "Este campo es obligatorio."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.codigo:
            codigo = f"VPSL-{self.pk:06d}"
            type(self).objects.filter(pk=self.pk).update(codigo=codigo)
            self.codigo = codigo


class EvaluacionSedeItinerarioVPSL(models.Model):
    itinerario = models.ForeignKey(
        ItinerarioVPSL,
        on_delete=models.CASCADE,
        related_name="evaluaciones_sedes",
    )
    sede = models.ForeignKey(
        SedeVPSL,
        on_delete=models.CASCADE,
        related_name="evaluaciones_itinerario",
    )
    estado = models.CharField(
        max_length=16,
        choices=EstadoEvaluacionVPSL.choices,
        default=EstadoEvaluacionVPSL.PENDIENTE,
    )
    observacion = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sede__jurisdiccion", "sede__localidad", "sede__nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["itinerario", "sede"],
                name="uniq_vpsl_evaluacion_itinerario_sede",
            )
        ]

    def __str__(self):
        return f"{self.itinerario} - {self.sede} - {self.get_estado_display()}"


class JornadaVPSL(SoftDeleteModelMixin, models.Model):
    VEHICULO_CHOICES = (
        ("vehiculo_1", "Vehiculo 1"),
        ("vehiculo_2", "Vehiculo 2"),
        ("vehiculo_3", "Vehiculo 3"),
        ("vehiculo_4", "Vehiculo 4"),
    )

    itinerario = models.ForeignKey(
        ItinerarioVPSL,
        on_delete=models.CASCADE,
        related_name="jornadas",
    )
    sede_vpsl = models.ForeignKey(
        SedeVPSL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="jornadas",
    )
    fecha = models.DateField()
    municipio = models.ForeignKey(
        Municipio, on_delete=models.SET_NULL, null=True, blank=True
    )
    localidad = models.ForeignKey(
        Localidad, on_delete=models.SET_NULL, null=True, blank=True
    )
    sede = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255, blank=True)
    vehiculo = models.CharField(
        max_length=32,
        choices=VEHICULO_CHOICES,
        blank=True,
    )
    horario_inicio = models.TimeField(blank=True, null=True)
    horario_fin = models.TimeField(blank=True, null=True)
    referente_nombre = models.CharField(max_length=255, blank=True)
    referente_apellido = models.CharField(max_length=255, blank=True)
    referente_dni = models.CharField(max_length=16, blank=True)
    referente_sexo = models.CharField(max_length=1, blank=True)
    referente_validado_renaper = models.BooleanField(default=False)
    referente_datos_renaper = models.JSONField(blank=True, null=True)
    referente_telefono = models.CharField(max_length=50, blank=True)
    referente_email = models.EmailField(blank=True)
    equipo_asignado = models.CharField(max_length=255, blank=True)
    estado = models.CharField(
        max_length=32,
        choices=EstadoJornada.choices,
        default=EstadoJornada.PLANIFICADA,
        db_index=True,
    )
    observaciones = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["fecha", "sede"]
        verbose_name = "Jornada VPSL"
        verbose_name_plural = "Jornadas VPSL"
        constraints = [
            models.UniqueConstraint(
                fields=["itinerario", "fecha", "sede"],
                name="uniq_vpsl_jornada_fecha_sede",
            )
        ]

    def __str__(self):
        return f"{self.fecha:%d/%m/%Y} - {self.sede}"

    def clean(self):
        super().clean()
        errors = {}
        if self.itinerario_id and self.fecha:
            inicio = self.itinerario.fecha_inicio
            fin = self.itinerario.fecha_fin
            if inicio and fin and not inicio <= self.fecha <= fin:
                errors["fecha"] = (
                    "La jornada debe estar dentro del rango del itinerario."
                )
        if (
            self.horario_inicio
            and self.horario_fin
            and self.horario_inicio >= self.horario_fin
        ):
            errors["horario_fin"] = "El horario de fin debe ser posterior al inicio."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.sede_vpsl_id:
            self.sede = self.sede_vpsl.nombre
            self.direccion = self.sede_vpsl.domicilio
        super().save(*args, **kwargs)

    @property
    def tiene_casos_laboratorio_pendientes(self):
        return self.registros.filter(
            caso_laboratorio__estado__in=[
                EstadoLaboratorio.PENDIENTE_ENVIO,
                EstadoLaboratorio.ENVIADO,
                EstadoLaboratorio.EN_PRODUCCION,
                EstadoLaboratorio.ENVIADO_NACION,
                EstadoLaboratorio.ENVIADO_PROVINCIA,
                EstadoLaboratorio.RECIBIDO,
                EstadoLaboratorio.INCIDENCIA,
            ]
        ).exists()


class ChecklistJornadaVPSL(models.Model):
    class Item(models.TextChoices):
        ELECTRICIDAD = "electricidad", "Electricidad"
        INFRAESTRUCTURA = "infraestructura", "Infraestructura"
        VIANDAS = "viandas", "Viandas / almuerzo"
        SEGURIDAD = "seguridad", "Seguridad / resguardo"
        MOVIL = "movil", "Movil"
        EQUIPO = "equipo", "Equipo operativo"
        OTRO = "otro", "Otro"

    jornada = models.ForeignKey(
        JornadaVPSL,
        on_delete=models.CASCADE,
        related_name="checklist",
        null=True,
        blank=True,
    )
    sede = models.ForeignKey(
        SedeVPSL,
        on_delete=models.CASCADE,
        related_name="checklist",
        null=True,
        blank=True,
    )
    item = models.CharField(max_length=32, choices=Item.choices)
    descripcion = models.CharField(max_length=255, blank=True)
    critico = models.BooleanField(default=True)
    cumple = models.BooleanField(blank=True, null=True)
    observacion = models.TextField(blank=True)
    evidencia = models.FileField(
        upload_to="ver_para_ser_libre/checklist/",
        blank=True,
        null=True,
    )
    responsable = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "Checklist de jornada VPSL"
        verbose_name_plural = "Checklist de jornada VPSL"
        constraints = [
            models.UniqueConstraint(
                fields=["jornada", "item"],
                name="uniq_vpsl_checklist_jornada_item",
            )
        ]

    def __str__(self):
        owner = self.sede or self.jornada
        return f"{owner} - {self.get_item_display()}"


class HistorialChecklistSedeVPSL(models.Model):
    checklist = models.ForeignKey(
        ChecklistJornadaVPSL,
        on_delete=models.CASCADE,
        related_name="historial",
    )
    cumple_anterior = models.BooleanField(blank=True, null=True)
    cumple_nuevo = models.BooleanField(blank=True, null=True)
    observacion_anterior = models.TextField(blank=True)
    observacion_nueva = models.TextField(blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Historial checklist sede VPSL"
        verbose_name_plural = "Historial checklist sede VPSL"


class RegistroNominalVPSL(SoftDeleteModelMixin, models.Model):
    jornada = models.ForeignKey(
        JornadaVPSL,
        on_delete=models.CASCADE,
        related_name="registros",
    )
    dni = models.CharField(max_length=16, blank=True, db_index=True)
    sexo = models.CharField(max_length=1, blank=True)
    identificador_alternativo = models.CharField(max_length=64, blank=True)
    nombre = models.CharField(max_length=255)
    apellido = models.CharField(max_length=255)
    edad = models.PositiveSmallIntegerField(blank=True, null=True)
    genero = models.CharField(max_length=64, blank=True)
    telefono = models.CharField(max_length=50, blank=True)
    escuela_sede = models.CharField(max_length=255, blank=True)
    numero_acta = models.CharField(max_length=64)
    numero_sobre = models.CharField(max_length=64, blank=True)
    fecha_atencion = models.DateField(default=timezone.localdate)
    prescripcion = models.TextField(blank=True)
    resultado = models.CharField(max_length=32, choices=ResultadoAtencion.choices)
    cantidad_lentes = models.PositiveSmallIntegerField(default=0)
    estado = models.CharField(
        max_length=32,
        choices=EstadoRegistroNominal.choices,
        default=EstadoRegistroNominal.CARGADO,
        db_index=True,
    )
    validado_renaper = models.BooleanField(default=False)
    no_verificar_renaper = models.BooleanField(default=False)
    datos_renaper = models.JSONField(blank=True, null=True)
    adjunto = models.FileField(
        upload_to="ver_para_ser_libre/registros/",
        blank=True,
        null=True,
    )
    primera_vez_anteojos = models.BooleanField(default=False)
    observaciones = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["apellido", "nombre"]
        verbose_name = "Registro nominal VPSL"
        verbose_name_plural = "Registros nominales VPSL"
        constraints = [
            models.UniqueConstraint(
                fields=["jornada", "numero_acta"],
                name="uniq_vpsl_registro_jornada_acta",
            )
        ]

    def __str__(self):
        return f"{self.apellido}, {self.nombre} - acta {self.numero_acta}"

    def clean(self):
        super().clean()
        if not self.dni and not self.identificador_alternativo:
            raise ValidationError(
                {
                    "dni": "Debe informar DNI o un identificador alternativo.",
                    "identificador_alternativo": "Debe informar DNI o identificador alternativo.",
                }
            )
        if self.resultado == ResultadoAtencion.NO_REQUIERE and self.cantidad_lentes:
            raise ValidationError(
                {"cantidad_lentes": "No corresponde informar lentes si no requiere."}
            )
        if self.cantidad_lentes and self.cantidad_lentes > 2:
            raise ValidationError(
                {"cantidad_lentes": "La cantidad maxima de lentes es 2."}
            )


class CasoLaboratorioVPSL(SoftDeleteModelMixin, models.Model):
    registro = models.OneToOneField(
        RegistroNominalVPSL,
        on_delete=models.CASCADE,
        related_name="caso_laboratorio",
    )
    estado = models.CharField(
        max_length=32,
        choices=EstadoLaboratorio.choices,
        default=EstadoLaboratorio.PENDIENTE_ENVIO,
        db_index=True,
    )
    fecha_envio = models.DateField(blank=True, null=True)
    fecha_recepcion = models.DateField(blank=True, null=True)
    fecha_entrega = models.DateField(blank=True, null=True)
    responsable_entrega = models.CharField(max_length=255, blank=True)
    destinatario = models.CharField(max_length=255, blank=True)
    remito = models.FileField(
        upload_to="ver_para_ser_libre/laboratorio/",
        blank=True,
        null=True,
    )
    incidencia = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["estado", "registro__jornada__fecha"]
        verbose_name = "Caso de laboratorio VPSL"
        verbose_name_plural = "Casos de laboratorio VPSL"

    def __str__(self):
        return f"{self.registro} - {self.get_estado_display()}"

    def clean(self):
        super().clean()
        if self.estado == EstadoLaboratorio.ENTREGADO and (
            not self.fecha_entrega or not self.responsable_entrega
        ):
            raise ValidationError(
                "Un caso entregado requiere fecha y responsable de entrega."
            )


class HistorialLaboratorioVPSL(models.Model):
    caso = models.ForeignKey(
        CasoLaboratorioVPSL,
        on_delete=models.CASCADE,
        related_name="historial",
    )
    estado_anterior = models.CharField(max_length=32, blank=True)
    estado_nuevo = models.CharField(max_length=32)
    fecha = models.DateField()
    responsable = models.CharField(max_length=255)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Historial laboratorio VPSL"
        verbose_name_plural = "Historial laboratorio VPSL"


class CierreDiarioVPSL(SoftDeleteModelMixin, models.Model):
    jornada = models.OneToOneField(
        JornadaVPSL,
        on_delete=models.CASCADE,
        related_name="cierre",
    )
    total_controles = models.PositiveIntegerField(default=0)
    anteojos_entregados = models.PositiveIntegerField(default=0)
    casos_laboratorio = models.PositiveIntegerField(default=0)
    no_requiere_anteojos = models.PositiveIntegerField(default=0)
    derivados = models.PositiveIntegerField(default=0)
    total_anteojos = models.PositiveIntegerField(default=0)
    cantidad_atenciones_registradas = models.PositiveIntegerField(default=0)
    cantidad_lentes_entregados_dia = models.PositiveIntegerField(default=0)
    cantidad_casos_laboratorio_reportados = models.PositiveIntegerField(default=0)
    responsable_cierre = models.CharField(max_length=255)
    fecha_cierre = models.DateTimeField(default=timezone.now)
    consistente = models.BooleanField(default=False)
    acta_adjunta = models.FileField(
        upload_to="ver_para_ser_libre/cierres/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["jpg", "jpeg", "png", "webp", "xls", "xlsx"]
            )
        ],
    )
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = "Cierre diario VPSL"
        verbose_name_plural = "Cierres diarios VPSL"

    def __str__(self):
        return f"Cierre {self.jornada}"


class HistorialCierreDiarioVPSL(models.Model):
    cierre = models.ForeignKey(
        CierreDiarioVPSL,
        on_delete=models.CASCADE,
        related_name="historial_subsanaciones",
    )
    cantidad_atenciones_registradas = models.PositiveIntegerField()
    cantidad_lentes_entregados_dia = models.PositiveIntegerField()
    cantidad_casos_laboratorio_reportados = models.PositiveIntegerField()
    responsable = models.CharField(max_length=255)
    acta_adjunta = models.FileField(
        upload_to="ver_para_ser_libre/cierres/historial/",
        blank=True,
        null=True,
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Historial de cierre diario VPSL"
        verbose_name_plural = "Historiales de cierre diario VPSL"


class HistorialEstadoVPSL(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    estado_anterior = models.CharField(max_length=64, blank=True)
    estado_nuevo = models.CharField(max_length=64)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    observacion = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Historial de estado VPSL"
        verbose_name_plural = "Historiales de estado VPSL"

    def __str__(self):
        return f"{self.content_object}: {self.estado_anterior} -> {self.estado_nuevo}"
