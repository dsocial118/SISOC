from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .validators import LISTADO_FILE_VALIDATORS


class EstadoEncuesta(models.TextChoices):
    BORRADOR = "borrador", "Borrador"
    PUBLICADA = "publicada", "Publicada"
    CERRADA = "cerrada", "Cerrada"
    ARCHIVADA = "archivada", "Archivada"


class TipoPregunta(models.TextChoices):
    TEXTO_CORTO = "texto_corto", "Texto corto"
    TEXTO_LARGO = "texto_largo", "Texto largo"
    OPCION_UNICA = "opcion_unica", "Opción única"
    OPCION_MULTIPLE = "opcion_multiple", "Opción múltiple"
    ESCALA = "escala", "Escala"
    SI_NO = "si_no", "Sí/No"
    NUMERICO = "numerico", "Numérico"
    FECHA = "fecha", "Fecha"


class OperadorCondicion(models.TextChoices):
    IGUAL = "igual", "Igual a"
    DISTINTO = "distinto", "Distinto de"


class TipoSegmentacion(models.TextChoices):
    TODOS_LOS_USUARIOS = "todos_los_usuarios", "Todos los usuarios"
    LISTADO_DOCUMENTOS = "listado_documentos", "Listado de documentos"


class TipoDocumento(models.TextChoices):
    DNI = "dni", "DNI"
    CUIT = "cuit", "CUIT"
    CUIL = "cuil", "CUIL"


class EstadoRonda(models.TextChoices):
    ABIERTA = "abierta", "Abierta"
    CERRADA = "cerrada", "Cerrada"


def encuesta_listado_upload_to(instance, filename):
    """Ruta de guardado del archivo de listado, agrupada por encuesta."""
    return f"encuestas/segmentacion/{instance.encuesta_id or 'sin'}/{filename}"


class Encuesta(models.Model):
    titulo = models.CharField(max_length=200, verbose_name="Título")
    descripcion = models.TextField(blank=True, default="", verbose_name="Descripción")
    estado = models.CharField(
        max_length=20,
        choices=EstadoEncuesta.choices,
        default=EstadoEncuesta.BORRADOR,
        verbose_name="Estado",
    )
    es_anonima = models.BooleanField(default=False, verbose_name="¿Es anónima?")
    es_obligatoria = models.BooleanField(default=False, verbose_name="¿Es obligatoria?")
    intervalo_recordatorio_dias = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Intervalo de recordatorio (días)",
        help_text="Solo aplica si la encuesta no es obligatoria.",
    )
    es_recurrente = models.BooleanField(default=False, verbose_name="¿Es recurrente?")
    intervalo_recurrencia_dias = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Intervalo de recurrencia (días)"
    )
    duracion_ronda_dias = models.PositiveIntegerField(
        verbose_name="Duración de cada ronda (días)"
    )
    version = models.PositiveIntegerField(default=1, verbose_name="Versión")
    version_de = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="versiones",
        verbose_name="Versión de",
    )
    usuario_creador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="encuestas_creadas",
        verbose_name="Usuario creador",
    )
    usuario_ultima_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="encuestas_modificadas",
        null=True,
        blank=True,
        verbose_name="Última modificación por",
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de creación"
    )
    fecha_ultima_modificacion = models.DateTimeField(
        auto_now=True, verbose_name="Fecha de última modificación"
    )

    class Meta:
        verbose_name = "Encuesta"
        verbose_name_plural = "Encuestas"
        ordering = ["-fecha_creacion"]
        constraints = [
            models.UniqueConstraint(
                fields=["version_de", "version"],
                name="uniq_encuesta_version_de_version",
            )
        ]
        permissions = [
            ("ver_resultados", "Puede ver los resultados de las encuestas"),
        ]

    def __str__(self):
        return f"{self.titulo} (v{self.version})"

    def clean(self):
        super().clean()
        if not self.es_obligatoria and self.intervalo_recordatorio_dias is None:
            raise ValidationError(
                {
                    "intervalo_recordatorio_dias": (
                        "Las encuestas no obligatorias requieren un intervalo de "
                        "recordatorio."
                    )
                }
            )
        if self.es_recurrente and self.intervalo_recurrencia_dias is None:
            raise ValidationError(
                {
                    "intervalo_recurrencia_dias": (
                        "Las encuestas recurrentes requieren un intervalo de "
                        "recurrencia."
                    )
                }
            )


class Pregunta(models.Model):
    encuesta = models.ForeignKey(
        Encuesta,
        on_delete=models.CASCADE,
        related_name="preguntas",
        verbose_name="Encuesta",
    )
    texto = models.CharField(max_length=500, verbose_name="Texto")
    tipo = models.CharField(
        max_length=20,
        choices=TipoPregunta.choices,
        verbose_name="Tipo de respuesta esperada",
    )
    obligatoria = models.BooleanField(default=True, verbose_name="¿Obligatoria?")
    orden = models.PositiveIntegerField(default=0, verbose_name="Orden")
    pregunta_condicion = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="preguntas_dependientes",
        verbose_name="Mostrar según respuesta de",
    )
    operador_condicion = models.CharField(
        max_length=20,
        choices=OperadorCondicion.choices,
        blank=True,
        default="",
        verbose_name="Operador de la condición",
    )
    valor_condicion = models.CharField(
        max_length=200, blank=True, default="", verbose_name="Valor esperado"
    )

    class Meta:
        verbose_name = "Pregunta"
        verbose_name_plural = "Preguntas"
        ordering = ["encuesta", "orden"]

    def __str__(self):
        return self.texto

    def clean(self):
        super().clean()
        if (
            self.pregunta_condicion_id
            and self.encuesta_id
            and self.pregunta_condicion.encuesta_id != self.encuesta_id
        ):
            raise ValidationError(
                {
                    "pregunta_condicion": (
                        "La pregunta de referencia debe pertenecer a la misma "
                        "encuesta."
                    )
                }
            )
        if bool(self.pregunta_condicion_id) != bool(self.operador_condicion):
            raise ValidationError(
                "La condición de visibilidad requiere pregunta, operador y valor "
                "en conjunto."
            )


class OpcionPregunta(models.Model):
    pregunta = models.ForeignKey(
        Pregunta,
        on_delete=models.CASCADE,
        related_name="opciones",
        verbose_name="Pregunta",
    )
    texto = models.CharField(max_length=200, verbose_name="Texto")
    valor = models.CharField(max_length=200, verbose_name="Valor")
    orden = models.PositiveIntegerField(default=0, verbose_name="Orden")

    class Meta:
        verbose_name = "Opción de pregunta"
        verbose_name_plural = "Opciones de pregunta"
        ordering = ["pregunta", "orden"]

    def __str__(self):
        return self.texto


class SegmentacionEncuesta(models.Model):
    encuesta = models.OneToOneField(
        Encuesta,
        on_delete=models.CASCADE,
        related_name="segmentacion",
        verbose_name="Encuesta",
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoSegmentacion.choices,
        verbose_name="Tipo de segmentación",
    )
    archivo_listado = models.FileField(
        upload_to=encuesta_listado_upload_to,
        null=True,
        blank=True,
        validators=LISTADO_FILE_VALIDATORS,
        verbose_name="Archivo de listado",
    )

    class Meta:
        verbose_name = "Segmentación de encuesta"
        verbose_name_plural = "Segmentaciones de encuesta"

    def __str__(self):
        return f"Segmentación de {self.encuesta} ({self.get_tipo_display()})"


class SegmentacionDestinatario(models.Model):
    segmentacion = models.ForeignKey(
        SegmentacionEncuesta,
        on_delete=models.CASCADE,
        related_name="destinatarios",
        verbose_name="Segmentación",
    )
    tipo_documento = models.CharField(
        max_length=10, choices=TipoDocumento.choices, verbose_name="Tipo de documento"
    )
    numero_documento = models.CharField(
        max_length=20, verbose_name="Número de documento"
    )

    class Meta:
        verbose_name = "Destinatario de segmentación"
        verbose_name_plural = "Destinatarios de segmentación"
        constraints = [
            models.UniqueConstraint(
                fields=["segmentacion", "tipo_documento", "numero_documento"],
                name="uniq_segmentacion_destinatario",
            )
        ]

    def __str__(self):
        return f"{self.get_tipo_documento_display()} {self.numero_documento}"


class RondaEncuesta(models.Model):
    encuesta = models.ForeignKey(
        Encuesta,
        on_delete=models.PROTECT,
        related_name="rondas",
        verbose_name="Encuesta",
    )
    numero_ronda = models.PositiveIntegerField(verbose_name="Número de ronda")
    fecha_apertura = models.DateTimeField(verbose_name="Fecha de apertura")
    fecha_cierre_programada = models.DateTimeField(
        verbose_name="Fecha de cierre programada"
    )
    fecha_cierre_real = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de cierre real"
    )
    estado = models.CharField(
        max_length=10,
        choices=EstadoRonda.choices,
        default=EstadoRonda.ABIERTA,
        verbose_name="Estado",
    )
    cerrada_manualmente = models.BooleanField(
        default=False, verbose_name="¿Cerrada manualmente?"
    )

    class Meta:
        verbose_name = "Ronda de encuesta"
        verbose_name_plural = "Rondas de encuesta"
        ordering = ["-fecha_apertura"]
        constraints = [
            models.UniqueConstraint(
                fields=["encuesta", "numero_ronda"], name="uniq_ronda_encuesta_numero"
            )
        ]

    def __str__(self):
        return f"{self.encuesta} - Ronda {self.numero_ronda}"


class RespuestaRonda(models.Model):
    ronda = models.ForeignKey(
        RondaEncuesta,
        on_delete=models.PROTECT,
        related_name="respuestas",
        verbose_name="Ronda",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="respuestas_encuesta",
        verbose_name="Usuario",
    )
    fecha_respuesta = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de respuesta"
    )
    completa = models.BooleanField(default=False, verbose_name="¿Completa?")

    class Meta:
        verbose_name = "Respuesta de ronda"
        verbose_name_plural = "Respuestas de ronda"
        constraints = [
            models.UniqueConstraint(
                fields=["ronda", "usuario"], name="uniq_respuesta_ronda_usuario"
            )
        ]

    def __str__(self):
        return f"Respuesta de {self.usuario} a {self.ronda}"


class RespuestaPregunta(models.Model):
    respuesta_ronda = models.ForeignKey(
        RespuestaRonda,
        on_delete=models.CASCADE,
        related_name="respuestas_pregunta",
        verbose_name="Respuesta de ronda",
    )
    pregunta = models.ForeignKey(
        Pregunta,
        on_delete=models.PROTECT,
        related_name="respuestas",
        verbose_name="Pregunta",
    )
    valor_texto = models.TextField(
        blank=True, default="", verbose_name="Valor de texto"
    )
    valor_numero = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor numérico",
    )
    valor_fecha = models.DateField(null=True, blank=True, verbose_name="Valor de fecha")
    opciones_seleccionadas = models.ManyToManyField(
        OpcionPregunta,
        blank=True,
        related_name="respuestas",
        verbose_name="Opciones seleccionadas",
    )

    class Meta:
        verbose_name = "Respuesta de pregunta"
        verbose_name_plural = "Respuestas de pregunta"
        constraints = [
            models.UniqueConstraint(
                fields=["respuesta_ronda", "pregunta"], name="uniq_respuesta_pregunta"
            )
        ]

    def __str__(self):
        return f"Respuesta a '{self.pregunta}' ({self.respuesta_ronda_id})"


class RecordatorioUsuario(models.Model):
    ronda = models.ForeignKey(
        RondaEncuesta,
        on_delete=models.CASCADE,
        related_name="recordatorios",
        verbose_name="Ronda",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recordatorios_encuesta",
        verbose_name="Usuario",
    )
    fecha_proximo_aviso = models.DateTimeField(verbose_name="Fecha del próximo aviso")

    class Meta:
        verbose_name = "Recordatorio de usuario"
        verbose_name_plural = "Recordatorios de usuario"
        constraints = [
            models.UniqueConstraint(
                fields=["ronda", "usuario"], name="uniq_recordatorio_ronda_usuario"
            )
        ]

    def __str__(self):
        return f"Recordatorio de {self.usuario} para {self.ronda}"
