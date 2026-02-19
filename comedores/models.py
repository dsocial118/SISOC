from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from core.models import Municipio, Provincia
from core.models import Localidad
from core.fields import UnicodeEmailField
from organizaciones.models import Organizacion
from ciudadanos.models import Ciudadano
from duplas.models import Dupla


class TipoDeComedor(models.Model):
    """
    Opciones de tipos para un Comedor/Merendero/Punto de entrega
    """

    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        ordering = ["id"]
        verbose_name = "Tipo de comedor"
        verbose_name_plural = "Tipos de comedor"


class Referente(models.Model):
    """
    Modelo que representa a un referente, en algun futuro se migrara a Ciudadano.

    Atributos:
        nombre (CharField): Nombre del referente.
        apellido (CharField): Apellido del referente.
        mail (EmailField): Dirección de correo electrónico única del referente.
        celular (BigIntegerField): Número único del referente.
        documento (BigIntegerField): Documento único del referente.
        funcion (CharField): Función del referente.
    """

    nombre = models.CharField(
        max_length=255, verbose_name="Nombre del referente", blank=True, null=True
    )
    apellido = models.CharField(
        max_length=255, verbose_name="Apellido del referente", blank=True, null=True
    )
    mail = UnicodeEmailField(verbose_name="Mail del referente", blank=True, null=True)
    celular = models.BigIntegerField(
        verbose_name="Celular del referente", blank=True, null=True
    )
    documento = models.BigIntegerField(
        verbose_name="Documento del referente", blank=True, null=True
    )
    funcion = models.CharField(
        verbose_name="Funcion del referente", max_length=255, blank=True, null=True
    )

    def clean(self):
        errors = {}
        # validar celular: maximo 15 dígitos numéricos
        if self.celular is not None:
            s = str(self.celular)
            if not s.isdigit() or len(s) > 15:
                errors["celular"] = ValidationError(
                    "El celular debe contener maximo 15 dígitos numéricos (sin espacios ni signos)."
                )

        # validar documento: 7 u 8 dígitos numéricos
        if self.documento is not None:
            s = str(self.documento)
            if not s.isdigit() or len(s) not in (7, 8):
                errors["documento"] = ValidationError(
                    "El documento debe contener 7 u 8 dígitos numéricos."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # asegurar que clean() se ejecute antes de salvar (validación consistente)
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"

    class Meta:
        verbose_name = "Referente"
        verbose_name_plural = "Referentes"


class Programas(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        ordering = ["id"]
        verbose_name = "Programa"
        verbose_name_plural = "Programas"


class EstadoActividad(models.Model):
    estado = models.CharField(max_length=255)

    def __str__(self):
        return str(self.estado)

    class Meta:
        ordering = ["id"]
        verbose_name = "Estado de Actividad"
        verbose_name_plural = "Estados de Actividad"


class EstadoProceso(models.Model):
    estado = models.CharField(max_length=255)
    estado_actividad = models.ForeignKey(
        to=EstadoActividad,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    def __str__(self):
        return str(self.estado)

    class Meta:
        ordering = ["id"]
        verbose_name = "Estado de Proceso"
        verbose_name_plural = "Estados de Proceso"


class EstadoDetalle(models.Model):
    estado = models.CharField(max_length=255)
    estado_proceso = models.ForeignKey(
        to=EstadoProceso,
        on_delete=models.PROTECT,
    )

    def __str__(self):
        return str(self.estado)

    class Meta:
        ordering = ["id"]
        verbose_name = "Estado de Detalle"
        verbose_name_plural = "Estados de Detalle"


class EstadoGeneral(models.Model):
    estado_actividad = models.ForeignKey(
        to=EstadoActividad,
        on_delete=models.PROTECT,
    )
    estado_proceso = models.ForeignKey(
        to=EstadoProceso,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    estado_detalle = models.ForeignKey(
        to=EstadoDetalle,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    def __str__(self):
        return (
            f"{self.estado_actividad} - {self.estado_proceso} - {self.estado_detalle}"
        )


class EstadoHistorial(models.Model):
    comedor = models.ForeignKey(
        to="Comedor",
        on_delete=models.CASCADE,
        related_name="historial_estados",
    )
    estado_general = models.ForeignKey(
        to=EstadoGeneral,
        on_delete=models.PROTECT,
    )
    usuario = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    fecha_cambio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.estado_general.__str__()

    class Meta:
        ordering = ["-fecha_cambio"]
        verbose_name = "Historial de Estado de Comedor"
        verbose_name_plural = "Historiales de Estado de Comedor"


class Comedor(models.Model):
    """
    Representa una Comedor/Merendero.

    Atributos:
        nombre (CharField): Nombre del Comedor/Merendero.
        comienzo (IntegerField): Año de inicio de la actividad del Comedor/Merendero.
        tipocomedor (ForeignKey): Tipo de Comedor/Merendero.
        calle (CharField): Calle donde se encuentra el Comedor/Merendero.
        numero (PositiveIntegerField): Número de la calle donde se encuentra el Comedor/Merendero.
        entre_calle_1 (CharField): Primera calle entre la cual se encuentra el Comedor/Merendero.
        entre_calle_2 (CharField): Segunda calle entre la cual se encuentra el Comedor/Merendero.
        provincia (ForeignKey): Provincia donde se encuentra el Comedor/Merendero.
        municipio (ForeignKey): Municipio donde se encuentra el Comedor/Merendero.
        localidad (ForeignKey): Localidad donde se encuentra el Comedor/Merendero.
        partido (CharField): Partido donde se encuentra el Comedor/Merendero/Merendero.
        barrio (CharField): Barrio donde se encuentra el Comedor/Merendero.
        codigo_postal (IntegerField): Código postal del Comedor/Merendero.
        referente (ForeignKey): Referente del Comedor/Merendero.
        dupla (ForeignKey): Dúpla del Comedor/Merendero.
    """

    nombre = models.CharField(
        max_length=255,
    )
    organizacion = models.ForeignKey(
        to=Organizacion, blank=True, null=True, on_delete=models.PROTECT
    )
    programa = models.ForeignKey(
        to=Programas, blank=True, null=True, on_delete=models.PROTECT
    )
    id_externo = models.IntegerField(
        verbose_name="Id Externo",
        blank=True,
        null=True,
    )
    codigo_de_proyecto = models.CharField(
        max_length=255,
        verbose_name="Código de Proyecto",
        blank=True,
        null=True,
    )
    comienzo = models.IntegerField(
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(2026),
        ],
        verbose_name="Año en el que comenzó a funcionar",
        blank=True,
        null=True,
    )
    tipocomedor = models.ForeignKey(
        to=TipoDeComedor, on_delete=models.PROTECT, null=True, blank=True
    )
    dupla = models.ForeignKey(
        to=Dupla,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    # Se agrego el estado del comedor para poder filtrar los que no tienen ingreso
    # y los que tienen ingreso asignado a dupla tecnica
    estadosComedor = [
        ("Sin Ingreso", "Sin Ingreso"),
        ("Asignado a Dupla Técnica", "Asignado a Dupla Técnica"),
    ]
    estado = models.CharField(
        choices=estadosComedor,
        max_length=255,
        blank=True,
        null=True,
        default="Sin Ingreso",
    )

    ESTADO_GENERAL_DEFAULT = "Sin definir"
    ultimo_estado = models.ForeignKey(
        to=EstadoHistorial,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="comedores_con_ultimo_estado",
    )

    direccion_validator = RegexValidator(
        regex=r"^[a-zA-Z0-9\s.,áéíóúÁÉÍÓÚñÑ-]*$",
        message="La dirección solo puede contener letras, números, espacios y los caracteres ., -",
    )

    calle = models.CharField(
        max_length=255, blank=True, null=True, validators=[direccion_validator]
    )
    numero = models.PositiveIntegerField(blank=True, null=True)
    piso = models.CharField(
        max_length=255, blank=True, null=True, validators=[direccion_validator]
    )
    departamento = models.CharField(
        max_length=255, blank=True, null=True, validators=[direccion_validator]
    )
    manzana = models.CharField(
        max_length=255, blank=True, null=True, validators=[direccion_validator]
    )
    lote = models.CharField(
        max_length=255, blank=True, null=True, validators=[direccion_validator]
    )
    entre_calle_1 = models.CharField(
        max_length=255, blank=True, null=True, validators=[direccion_validator]
    )
    entre_calle_2 = models.CharField(
        max_length=255, blank=True, null=True, validators=[direccion_validator]
    )
    latitud = models.FloatField(
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        blank=True,
        null=True,
    )
    longitud = models.FloatField(
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        blank=True,
        null=True,
    )
    provincia = models.ForeignKey(to=Provincia, on_delete=models.PROTECT, null=True)
    municipio = models.ForeignKey(
        to=Municipio, on_delete=models.SET_NULL, null=True, blank=True
    )
    localidad = models.ForeignKey(
        to=Localidad, on_delete=models.SET_NULL, null=True, blank=True
    )
    partido = models.CharField(max_length=255, null=True, blank=True)
    barrio = models.CharField(max_length=255, null=True, blank=True)
    codigo_postal = models.IntegerField(
        validators=[
            MinValueValidator(1000),
            MaxValueValidator(999999),
        ],  # Entre 4 a 6 digitos
        blank=True,
        null=True,
    )
    referente = models.ForeignKey(
        to=Referente, on_delete=models.SET_NULL, null=True, blank=True
    )
    foto_legajo = models.ImageField(upload_to="comedor/", blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    ESTADOS_VALIDACION = [
        ("Pendiente", "Pendiente"),
        ("Validado", "Validado"),
        ("No Validado", "No Validado"),
    ]

    estado_validacion = models.CharField(
        max_length=20,
        choices=ESTADOS_VALIDACION,
        blank=True,
        default="Pendiente",
        verbose_name="Estado de validación",
    )

    fecha_validado = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de validación",
    )

    def __str__(self) -> str:
        return str(self.nombre)

    def get_estado_general_display(self) -> str:
        """
        Devuelve el nombre del estado general (actividad) basado en el último historial registrado.
        """
        if (
            self.ultimo_estado
            and self.ultimo_estado.estado_general_id
            and self.ultimo_estado.estado_general.estado_actividad
        ):
            return self.ultimo_estado.estado_general.estado_actividad.estado
        return self.ESTADO_GENERAL_DEFAULT

    def delete(self, using=None, keep_parents=False):
        """
        Elimina el comedor junto con su historial de estados evitando errores de llaves protegidas.
        """
        db_alias = using or self._state.db or "default"
        with transaction.atomic(using=db_alias):
            # pylint: disable=access-member-before-definition
            ultimo_estado_id = getattr(self, "ultimo_estado_id", None)
            if ultimo_estado_id:
                type(self).objects.using(db_alias).filter(pk=self.pk).update(
                    ultimo_estado=None
                )
                self.ultimo_estado_id = None
            EstadoHistorial.objects.using(db_alias).filter(comedor_id=self.pk).delete()
            return super().delete(using=db_alias, keep_parents=keep_parents)

    class Meta:
        indexes = [
            models.Index(fields=["nombre"]),
        ]
        verbose_name = "comedor"
        verbose_name_plural = "comedores"
        ordering = ["nombre"]


class AuditComedorPrograma(models.Model):
    comedor = models.ForeignKey(
        Comedor, on_delete=models.CASCADE, related_name="programa_changes"
    )
    from_programa = models.ForeignKey(
        Programas,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="programa_changes_from",
    )
    to_programa = models.ForeignKey(
        Programas,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="programa_changes_to",
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="comedor_programa_changes",
    )

    class Meta:
        ordering = ["-changed_at", "-id"]
        verbose_name = "Cambio de programa del comedor"
        verbose_name_plural = "Cambios de programa del comedor"
        indexes = [
            models.Index(fields=["comedor", "changed_at"]),
            models.Index(fields=["changed_by"]),
        ]

    def __str__(self):
        from_programa = (
            self.from_programa.nombre if self.from_programa else "Sin programa"
        )
        to_programa = self.to_programa.nombre if self.to_programa else "Sin programa"
        return f"{self.comedor.nombre}: {from_programa} -> {to_programa}"


class Nomina(models.Model):
    ESTADO_PENDIENTE = "pendiente"
    ESTADO_ACTIVO = "activo"
    ESTADO_BAJA = "baja"

    ESTADO_CHOICES = [
        (ESTADO_ACTIVO, "Activo"),
        (ESTADO_PENDIENTE, "Pendiente"),
        (ESTADO_BAJA, "Baja"),
    ]

    comedor = models.ForeignKey("Comedor", on_delete=models.SET_NULL, null=True)
    ciudadano = models.ForeignKey(
        Ciudadano,
        on_delete=models.CASCADE,
        related_name="nominas",
        null=True,
        blank=True,
    )
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default=ESTADO_PENDIENTE,
    )
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Nomina"
        verbose_name_plural = "Nominas"
        indexes = [models.Index(fields=["comedor"])]

    def __str__(self):
        comedor = self.comedor.nombre if self.comedor else "Comedor sin nombre"
        ciudadano = str(self.ciudadano) if self.ciudadano else "Ciudadano no asignado"
        return f"{ciudadano} en {comedor} ({self.get_estado_display()})"


class ImagenComedor(models.Model):
    comedor = models.ForeignKey(
        Comedor, on_delete=models.CASCADE, related_name="imagenes"
    )
    imagen = models.ImageField(upload_to="comedor/")

    def __str__(self):
        return f"Imagen de {self.comedor.nombre}"


class Observacion(models.Model):
    """
    Modelo que representa una observación realizada en un Comedor/Merendero.
    """

    observador = models.CharField(max_length=255, blank=True)
    comedor = models.ForeignKey(
        to=Comedor,
        on_delete=models.CASCADE,
        blank=True,
    )
    fecha_visita = models.DateTimeField(default=timezone.now, blank=True)
    observacion = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=["comedor"]),
        ]
        verbose_name = "Observacion"
        verbose_name_plural = "Observaciones"

    def __str__(self):
        comedor = self.comedor.nombre if self.comedor else "Comedor sin nombre"
        fecha = self.fecha_visita.date() if self.fecha_visita else "sin fecha"
        return f"Observación {fecha} - {comedor}"


class ValorComida(models.Model):
    tipo = models.CharField(max_length=50)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField()

    def __str__(self):
        return f"{self.tipo}: ${self.valor} ({self.fecha})"


class CategoriaComedor(models.Model):
    nombre = models.CharField(max_length=255)
    puntuacion_min = models.IntegerField()
    puntuacion_max = models.IntegerField()

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Categoria de Comedor"
        verbose_name_plural = "Categorias de Comedor"


class TerritorialCache(models.Model):
    """
    Modelo para cachear información de territoriales de GESTIONAR por provincia.
    """

    gestionar_uid = models.CharField(max_length=100)
    nombre = models.CharField(max_length=200)
    provincia = models.ForeignKey(to=Provincia, on_delete=models.CASCADE)
    activo = models.BooleanField(default=True)

    # Metadatos de cache
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_ultimo_sync = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "comedores_territorial_cache"
        ordering = ["provincia__nombre", "nombre"]
        verbose_name = "Cache Territorial"
        verbose_name_plural = "Cache Territoriales"
        unique_together = [["gestionar_uid", "provincia"]]
        indexes = [
            models.Index(fields=["provincia", "activo"]),
        ]

    def __str__(self):
        return f"{self.nombre} - {self.provincia.nombre} ({self.gestionar_uid})"

    @property
    def esta_desactualizado(self):
        """
        Verifica si el territorial está desactualizado (más de 1 hora).
        """
        tiempo_limite = timezone.now() - timezone.timedelta(hours=1)
        return self.fecha_ultimo_sync < tiempo_limite

    def to_dict(self):
        """Convierte el objeto a diccionario para uso en frontend."""
        return {
            "gestionar_uid": self.gestionar_uid,
            "nombre": self.nombre,
            "desactualizado": self.esta_desactualizado,
        }


class TerritorialSyncLog(models.Model):
    """
    Log de sincronización con GESTIONAR para auditoría.
    """

    fecha = models.DateTimeField(auto_now_add=True)
    exitoso = models.BooleanField()
    territoriales_sincronizados = models.IntegerField(default=0)
    error_mensaje = models.TextField(blank=True)
    comedor_id = models.IntegerField(
        null=True, blank=True
    )  # Si sync fue para comedor específico

    class Meta:
        db_table = "comedores_territorial_sync_log"
        ordering = ["-fecha"]
        verbose_name = "Log Sync Territorial"
        verbose_name_plural = "Logs Sync Territoriales"

    def __str__(self):
        status = "Exitoso" if self.exitoso else "Error"
        return f"{self.fecha.strftime('%Y-%m-%d %H:%M')} - {status}"


class HistorialValidacion(models.Model):
    """
    Historial de validaciones de comedores.
    """

    comedor = models.ForeignKey(
        Comedor,
        on_delete=models.CASCADE,
        related_name="historial_validaciones",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    estado_validacion = models.CharField(
        max_length=20,
        choices=Comedor.ESTADOS_VALIDACION,
    )
    OPCIONES_NO_VALIDAR = [
        ("pac_inexistente_o_no_coincide", "PAC inexistente o no coincide"),
        ("sin_movimiento", "Sin movimiento"),
        ("no_se_reconoce_el_comedor", "No se reconoce el Comedor"),
        ("no_corresponde_a_la_dupla", "No corresponde a la dupla"),
        ("otro", "Otros"),
    ]

    @classmethod
    def get_opciones_no_validar(cls):
        """Retorna las opciones de no validación para uso en templates"""
        return cls.OPCIONES_NO_VALIDAR

    def get_opciones_display(self):
        """Retorna las opciones seleccionadas en formato legible"""
        if not self.opciones_no_validar:
            return "-"

        opciones_dict = dict(self.OPCIONES_NO_VALIDAR)
        opciones_texto = []

        for opcion in self.opciones_no_validar:
            if opcion in opciones_dict:
                opciones_texto.append(opciones_dict[opcion])

        return ", ".join(opciones_texto) if opciones_texto else "-"

    opciones_no_validar = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Opciones de no validación",
        help_text="Opciones seleccionadas cuando se marca como no validado",
    )
    comentario = models.TextField(
        verbose_name="Comentario",
        blank=True,
        null=True,
    )
    fecha_validacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de validación",
    )

    class Meta:
        ordering = ["-fecha_validacion"]
        verbose_name = "Historial de validación"
        verbose_name_plural = "Historiales de validación"
        indexes = [
            models.Index(fields=["comedor", "fecha_validacion"]),
        ]

    def __str__(self):
        fecha_str = self.fecha_validacion.strftime("%d/%m/%Y")
        return f"{self.comedor.nombre} - {self.estado_validacion} ({fecha_str})"
