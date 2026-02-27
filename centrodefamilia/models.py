from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.indexes import GinIndex
from django.utils import timezone
from ciudadanos.models import Ciudadano
from core.models import Dia, Localidad, Municipio, Provincia, Sexo
from core.soft_delete import SoftDeleteModelMixin
from organizaciones.models import Organizacion


class Centro(SoftDeleteModelMixin, models.Model):
    TIPO_CHOICES = [
        ("faro", "faro"),
        ("adherido", "Adherido"),
    ]
    nombre = models.CharField(max_length=200)
    referente = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        limit_choices_to={"groups__name": "ReferenteCentro"},
        related_name="centros",
        null=True,
        blank=False,
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    faro_asociado = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"tipo": "faro", "activo": True},
    )
    codigo = models.CharField(max_length=20, unique=True)
    foto = models.ImageField(upload_to="centros/", blank=True, null=True)
    activo = models.BooleanField(default=True)
    organizacion_asociada = models.ForeignKey(
        Organizacion,
        on_delete=models.CASCADE,
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
    calle = models.CharField(max_length=255, blank=True, null=True)
    numero = models.PositiveIntegerField(blank=True, null=True)
    domicilio_actividad = models.CharField(
        max_length=255, verbose_name="Domicilio de actividades"
    )
    telefono = models.CharField(max_length=50, verbose_name="Teléfono")
    celular = models.CharField(max_length=50, verbose_name="Celular")
    correo = models.EmailField(max_length=100, verbose_name="Correo electrónico")
    sitio_web = models.URLField(
        max_length=200, blank=True, null=True, verbose_name="Sitio web"
    )
    link_redes = models.URLField(
        max_length=200, blank=True, null=True, verbose_name="Redes sociales"
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

    def __str__(self):
        return self.nombre

    class Meta:
        indexes = [
            GinIndex(
                fields=["nombre"], name="centro_nombre_trgm", opclasses=["gin_trgm_ops"]
            ),
        ]


class Categoria(SoftDeleteModelMixin, models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la Categoría")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        indexes = [
            GinIndex(
                fields=["nombre"],
                name="categoria_nombre_trgm",
                opclasses=["gin_trgm_ops"],
            ),
        ]


class Actividad(SoftDeleteModelMixin, models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la Actividad")
    categoria = models.ForeignKey(
        Categoria, on_delete=models.CASCADE, verbose_name="Categoría"
    )

    def __str__(self):
        return self.nombre

    class Meta:
        indexes = [
            GinIndex(
                fields=["nombre"],
                name="actividad_nombre_trgm",
                opclasses=["gin_trgm_ops"],
            ),
        ]


class ActividadCentro(SoftDeleteModelMixin, models.Model):
    ESTADO_CHOICES = [
        ("planificada", "Planificada"),
        ("en_curso", "En curso"),
        ("finalizada", "Finalizada"),
    ]
    centro = models.ForeignKey(Centro, on_delete=models.CASCADE, verbose_name="Centro")
    actividad = models.ForeignKey(
        Actividad, on_delete=models.CASCADE, verbose_name="Actividad"
    )
    cantidad_personas = models.PositiveIntegerField(
        verbose_name="Cantidad Estimada de Participantes"
    )
    dias = models.ManyToManyField(
        to=Dia,
        related_name="DiaActividad",
        blank=True,
    )
    sexoact = models.ManyToManyField(
        to=Sexo,
        related_name="sexoactividad",
        verbose_name="Actividad Dirigida a ",
        blank=True,
    )
    horariosdesde = models.TimeField()
    horarioshasta = models.TimeField(null=True, blank=True)
    precio = models.PositiveIntegerField(
        verbose_name="PrecioActividad", null=True, blank=True
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="planificada",
        verbose_name="Estado",
    )

    def __str__(self):
        return f"{self.actividad.nombre} en {self.centro.nombre}"

    class Meta:
        verbose_name = "Actividad del Centro"
        verbose_name_plural = "Actividades por Centro"
        indexes = [
            models.Index(fields=["centro", "estado"]),
            GinIndex(
                fields=["estado"],
                name="actividadcentro_estado_trgm",
                opclasses=["gin_trgm_ops"],
            ),
        ]


class ParticipanteActividad(SoftDeleteModelMixin, models.Model):
    ESTADO_INSCRIPCION = [
        ("inscrito", "Inscrito"),
        ("lista_espera", "Lista de Espera"),
        ("dado_baja", "Dado de Baja"),
    ]

    actividad_centro = models.ForeignKey(
        ActividadCentro, on_delete=models.CASCADE, verbose_name="Actividad del Centro"
    )
    ciudadano = models.ForeignKey(
        Ciudadano, on_delete=models.CASCADE, verbose_name="Ciudadano"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_INSCRIPCION,
        default="inscrito",
        verbose_name="Estado de Inscripción",
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Registro"
    )
    fecha_modificacion = models.DateTimeField(
        auto_now=True, verbose_name="Fecha de Última Modificación"
    )

    def __str__(self):
        return (
            f"{self.ciudadano.apellido}, {self.ciudadano.nombre} - "
            f"{self.actividad_centro} [{self.estado}]"
        )

    class Meta:
        verbose_name = "Participante"
        verbose_name_plural = "Participantes"
        indexes = [
            models.Index(fields=["actividad_centro"]),
            GinIndex(
                fields=["estado"],
                name="participante_estado_trgm",
                opclasses=["gin_trgm_ops"],
            ),
        ]
        unique_together = ("actividad_centro", "ciudadano")


class ParticipanteActividadHistorial(models.Model):
    participante = models.ForeignKey(
        ParticipanteActividad, on_delete=models.CASCADE, related_name="historial"
    )
    estado_anterior = models.CharField(
        max_length=20,
        choices=ParticipanteActividad.ESTADO_INSCRIPCION,
        verbose_name="Estado Anterior",
        null=True,
        blank=True,
    )
    estado_nuevo = models.CharField(
        max_length=20,
        choices=ParticipanteActividad.ESTADO_INSCRIPCION,
        verbose_name="Estado Nuevo",
    )
    fecha_cambio = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Cambio"
    )
    usuario = models.ForeignKey(
        User, on_delete=models.PROTECT, verbose_name="Usuario que realizó el cambio"
    )

    def __str__(self):
        return (
            f"{self.participante}: {self.estado_anterior or '—'} -> {self.estado_nuevo} "
            f"en {self.fecha_cambio.strftime('%Y-%m-%d %H:%M')}"
        )

    class Meta:
        verbose_name = "Historial de Inscripción"
        verbose_name_plural = "Historial de Inscripciones"
        ordering = ["-fecha_cambio"]


# ——— NUEVO MÓDULO INFORME CABAL ———


class CabalArchivo(models.Model):
    """
    Archivo subido para Informe Cabal con auditoría y totales.
    """

    archivo = models.FileField(upload_to="informes_cabal/")
    nombre_original = models.CharField(max_length=255)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    advertencia_nombre_duplicado = models.BooleanField(default=False)
    total_filas = models.PositiveIntegerField(default=0)
    total_validas = models.PositiveIntegerField(default=0)
    total_invalidas = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.nombre_original} ({self.fecha_subida:%Y-%m-%d %H:%M})"

    class Meta:
        verbose_name = "Archivo CABAL"
        verbose_name_plural = "Archivos CABAL"
        indexes = [
            models.Index(fields=["fecha_subida"]),
            models.Index(fields=["nombre_original"]),
        ]


class InformeCabalRegistro(models.Model):
    """
    Registro histórico: una fila por línea del Excel.
    Si no hay match de NroComercio → Centro.codigo, centro queda NULL y se marca no_coincidente=True.
    """

    archivo = models.ForeignKey(
        CabalArchivo, on_delete=models.CASCADE, related_name="registros"
    )
    centro = models.ForeignKey(Centro, null=True, blank=True, on_delete=models.SET_NULL)

    # Campos del Excel
    nro_tarjeta = models.CharField(max_length=50)
    nro_auto = models.CharField(max_length=50)
    mti = models.CharField(max_length=20)
    nro_comercio = models.CharField(max_length=50)
    razon_social = models.CharField(max_length=255, blank=True)
    importe = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    fecha_trx = models.DateField(null=True, blank=True)
    moneda_origen = models.CharField(max_length=10, blank=True)
    importe_mon_origen = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    importe_pesos = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    cant_cuotas = models.IntegerField(null=True, blank=True)
    motivo_rechazo = models.CharField(max_length=50, blank=True)
    desc_motivo_rechazo = models.CharField(max_length=255, blank=True)
    disponibles = models.CharField(max_length=50, blank=True)

    # Flags / meta
    no_coincidente = models.BooleanField(default=False)
    fila_numero = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Registro CABAL"
        verbose_name_plural = "Registros CABAL"
        indexes = [
            models.Index(fields=["archivo"]),
            models.Index(fields=["centro"]),
            models.Index(fields=["nro_comercio"]),
            models.Index(fields=["fecha_trx"]),
        ]


# ——— MODELOS DE BENEFICIARIOS ———


class Responsable(SoftDeleteModelMixin, models.Model):
    GENERO_CHOICES = [
        ("F", "Femenino"),
        ("M", "Masculino"),
        ("X", "Otro/No binario"),
    ]

    VINCULO_PARENTAL_CHOICES = [
        ("Padre/Madre", "Padre/Madre"),
        ("Tutor/Tutora", "Tutor/Tutora"),
    ]

    vinculo_parental = models.CharField(max_length=50, choices=VINCULO_PARENTAL_CHOICES)

    cuil = models.BigIntegerField(unique=True)
    dni = models.PositiveIntegerField(unique=True)
    apellido = models.CharField(max_length=100)
    nombre = models.CharField(max_length=100)
    genero = models.CharField(max_length=20, choices=GENERO_CHOICES)
    fecha_nacimiento = models.DateField()

    provincia = models.ForeignKey(
        Provincia, on_delete=models.PROTECT, null=True, blank=True
    )
    municipio = models.ForeignKey(
        Municipio, on_delete=models.PROTECT, null=True, blank=True
    )
    localidad = models.ForeignKey(
        Localidad, on_delete=models.PROTECT, null=True, blank=True
    )
    codigo_postal = models.IntegerField(null=True, blank=True)

    calle = models.CharField(max_length=150)
    altura = models.IntegerField(null=True, blank=True)
    piso_vivienda = models.CharField(max_length=10, null=True, blank=True)
    departamento_vivienda = models.CharField(max_length=10, null=True, blank=True)
    barrio = models.CharField(max_length=100, null=True, blank=True)
    monoblock = models.CharField(max_length=100, null=True, blank=True)

    prefijo_celular = models.CharField(
        null=True,
        blank=True,
        max_length=4,
    )
    numero_celular = models.CharField(
        null=True,
        blank=True,
        max_length=12,
    )
    prefijo_telefono_fijo = models.CharField(
        null=True,
        blank=True,
        max_length=4,
    )
    numero_telefono_fijo = models.CharField(
        null=True,
        blank=True,
        max_length=12,
    )

    correo_electronico = models.EmailField(max_length=150, null=True, blank=True)

    # Auditoría
    creado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="responsables_creados",
        null=True,
        blank=True,
    )
    fecha_creado = models.DateTimeField(default=timezone.now)
    fecha_modificado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.cuil})"

    class Meta:
        ordering = ["apellido", "nombre"]


class Beneficiario(SoftDeleteModelMixin, models.Model):
    GENERO_CHOICES = [
        ("F", "Femenino"),
        ("M", "Masculino"),
        ("X", "Otro/No binario"),
    ]

    NIVEL_EDUCATIVO_ACTUAL_CHOICES = [
        ("Jardín", "Jardín"),
        ("Primario", "Primario"),
        ("Secundario", "Secundario"),
    ]

    MAXIMO_NIVEL_EDUCATIVO_CHOICES = [
        ("Sin instrucción", "Sin instrucción"),
        ("Jardín incompleto", "Jardín incompleto"),
        ("Jardín completo", "Jardín completo"),
        ("Primario incompleto", "Primario incompleto"),
        ("Primario completo", "Primario completo"),
        ("Secundario incompleto", "Secundario incompleto"),
        ("Secundario completo", "Secundario completo"),
    ]

    ACTIVIDAD_PREFERIDA_CHOICES = [
        ("Deportiva", "Deportiva"),
        ("Cultural/Artística", "Cultural/Artística"),
        ("Educativa", "Educativa"),
    ]

    # Identificación
    cuil = models.BigIntegerField(unique=True)
    dni = models.PositiveIntegerField(unique=True)
    apellido = models.CharField(max_length=100)
    nombre = models.CharField(max_length=100)
    genero = models.CharField(max_length=20, choices=GENERO_CHOICES)
    fecha_nacimiento = models.DateField()

    # De que tabla de beneficiarios provienen los datos
    provincia_tabla = models.CharField(max_length=100, blank=True, null=True)
    municipio_tabla = models.CharField(max_length=100, blank=True, null=True)
    localidad_tabla = models.CharField(max_length=150, blank=True, null=True)

    # Domicilio
    domicilio = models.CharField(max_length=255)
    provincia = models.ForeignKey(
        Provincia, on_delete=models.PROTECT, null=True, blank=True
    )
    municipio = models.ForeignKey(
        Municipio, on_delete=models.PROTECT, null=True, blank=True
    )
    localidad = models.ForeignKey(
        Localidad, on_delete=models.PROTECT, null=True, blank=True
    )
    codigo_postal = models.IntegerField(null=True, blank=True)
    calle = models.CharField(max_length=150)
    altura = models.IntegerField(null=True, blank=True)
    piso_vivienda = models.CharField(max_length=10, null=True, blank=True)
    departamento_vivienda = models.CharField(max_length=10, null=True, blank=True)
    barrio = models.CharField(max_length=100, null=True, blank=True)
    monoblock = models.CharField(max_length=100, null=True, blank=True)

    # Contacto
    prefijo_celular = models.CharField(
        null=True,
        blank=True,
        max_length=4,
    )
    numero_celular = models.CharField(
        null=True,
        blank=True,
        max_length=12,
    )
    prefijo_telefono_fijo = models.CharField(
        null=True,
        blank=True,
        max_length=4,
    )
    numero_telefono_fijo = models.CharField(null=True, blank=True, max_length=12)
    correo_electronico = models.EmailField(max_length=150, null=True, blank=True)

    # Académico
    estado_academico = models.BooleanField(default=False)
    nivel_educativo_actual = models.CharField(
        max_length=20, choices=NIVEL_EDUCATIVO_ACTUAL_CHOICES, null=True, blank=True
    )
    maximo_nivel_educativo = models.CharField(
        max_length=50, choices=MAXIMO_NIVEL_EDUCATIVO_CHOICES
    )
    institucion_academica = models.CharField(max_length=150, null=True, blank=True)

    # Actividades
    actividad_preferida = models.JSONField(default=list, blank=True)
    actividades_extracurriculares = models.BooleanField(default=False)
    actividades_detalle = models.ManyToManyField("Actividad", blank=True)

    # Relación con Responsable
    responsable = models.ForeignKey(
        "Responsable", on_delete=models.PROTECT, related_name="beneficiarios"
    )

    # Auditoría
    creado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="beneficiarios_creados",
        null=True,
        blank=True,
    )
    fecha_creado = models.DateTimeField(default=timezone.now)
    fecha_modificado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.cuil})"

    class Meta:
        ordering = ["apellido", "nombre"]


class BeneficiarioResponsable(SoftDeleteModelMixin, models.Model):
    """Tabla para manejar vínculos específicos entre beneficiario y responsable"""

    VINCULO_PARENTAL_CHOICES = [
        ("Padre/Madre", "Padre/Madre"),
        ("Tutor/Tutora", "Tutor/Tutora"),
    ]

    beneficiario = models.ForeignKey(Beneficiario, on_delete=models.CASCADE)
    responsable = models.ForeignKey(Responsable, on_delete=models.CASCADE)
    vinculo_parental = models.CharField(max_length=50, choices=VINCULO_PARENTAL_CHOICES)

    fecha_creado = models.DateTimeField(default=timezone.now)
    fecha_modificado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.beneficiario} - {self.responsable} ({self.vinculo_parental})"

    class Meta:
        unique_together = ["beneficiario", "responsable"]
        verbose_name = "Vínculo Beneficiario-Responsable"
        verbose_name_plural = "Vínculos Beneficiario-Responsable"


class PadronBeneficiarios(models.Model):
    cuil = models.CharField(max_length=20, db_column="CUITBenef")
    dni = models.CharField(max_length=20, db_column="DNIBenef", primary_key=True)
    genero = models.CharField(max_length=1, db_column="Sexo")
    provincia_tabla = models.CharField(
        max_length=100, db_column="Provincia", blank=True, null=True
    )
    municipio_tabla = models.CharField(
        max_length=100, db_column="Municipio", blank=True, null=True
    )

    class Meta:
        managed = False
        db_table = "padron_beneficiarios"


class BeneficiariosResponsablesRenaper(models.Model):
    iD_TRAMITE_PRINCIPAL = models.CharField(max_length=50, blank=True, null=True)
    iD_TRAMITE_TARJETA_REIMPRESA = models.CharField(
        max_length=50, blank=True, null=True
    )
    dni = models.CharField(max_length=20, blank=True, null=True)
    genero = models.CharField(max_length=20, blank=True, null=True)
    ejemplar = models.CharField(max_length=5, blank=True, null=True)
    vencimiento = models.CharField(max_length=20, blank=True, null=True)
    emision = models.CharField(max_length=20, blank=True, null=True)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    nombres = models.CharField(max_length=100, blank=True, null=True)
    fechaNacimiento = models.CharField(max_length=20, blank=True, null=True)
    cuil = models.CharField(max_length=20, blank=True, null=True)
    calle = models.CharField(max_length=150, blank=True, null=True)
    numero = models.CharField(max_length=20, blank=True, null=True)
    piso = models.CharField(max_length=10, blank=True, null=True)
    departamento = models.CharField(max_length=10, blank=True, null=True)
    cpostal = models.CharField(max_length=20, blank=True, null=True)
    barrio = models.CharField(max_length=100, blank=True, null=True)
    monoblock = models.CharField(max_length=100, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    municipio = models.CharField(max_length=100, blank=True, null=True)
    provincia = models.CharField(max_length=100, blank=True, null=True)
    pais = models.CharField(max_length=100, blank=True, null=True)
    codigoError = models.CharField(max_length=20, blank=True, null=True)
    codigof = models.CharField(max_length=20, blank=True, null=True)
    mensaf = models.CharField(max_length=255, blank=True, null=True)
    origenf = models.CharField(max_length=100, blank=True, null=True)
    fechaf = models.CharField(max_length=20, blank=True, null=True)
    idciudadano = models.CharField(max_length=50, blank=True, null=True)
    nroError = models.CharField(max_length=20, blank=True, null=True)
    descripcionError = models.CharField(max_length=255, blank=True, null=True)

    tipo = models.CharField(
        max_length=50, blank=True, null=True
    )  # Beneficiario o Responsable
    fecha_creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.apellido or ''}, {self.nombres or ''} ({self.cuil or ''})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["dni", "genero", "tipo"],
                name="unique_dni_genero_tipo",
            )
        ]
