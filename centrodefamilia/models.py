# centrodefamilia/models.py
"""
[Informe Cabal] 
- Agrega modelos: CabalArchivo e InformeCabalRegistro para auditoría y registros históricos.
- Flujos impactados: carga y procesamiento de Excel CABAL desde centro_list → vista historial → modal.
- Dependencias: views/informecabal.py, services/informe_cabal_service.py, templates/informecabal/*.html, static/js/informecabal.js
"""
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.indexes import GinIndex
from ciudadanos.models import Ciudadano
from core.models import Dia, Localidad, Municipio, Provincia, Sexo
from organizaciones.models import Organizacion

class Centro(models.Model):
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

class Categoria(models.Model):
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

class Actividad(models.Model):
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

class ActividadCentro(models.Model):
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

class ParticipanteActividad(models.Model):
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
    archivo = models.ForeignKey(CabalArchivo, on_delete=models.CASCADE, related_name="registros")
    centro = models.ForeignKey(Centro, null=True, blank=True, on_delete=models.SET_NULL)

    # Campos del Excel
    nro_tarjeta = models.CharField(max_length=50)
    nro_auto = models.CharField(max_length=50)
    mti = models.CharField(max_length=20)
    nro_comercio = models.CharField(max_length=50)
    razon_social = models.CharField(max_length=255, blank=True)
    importe = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    fecha_trx = models.DateField(null=True, blank=True)
    moneda_origen = models.CharField(max_length=10, blank=True)
    importe_mon_origen = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    importe_pesos = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
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

# (Dejamos tu modelo Expediente tal cual, sin uso en este flujo)
class Expediente(models.Model):
    centro = models.ForeignKey(
        Centro, on_delete=models.CASCADE, related_name="expedientes_cabal"
    )
    archivo = models.FileField(upload_to="informes_cabal/")
    periodo = models.DateField(help_text="Fecha del informe")
    fecha_subida = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    procesado = models.BooleanField(default=False)
    errores = models.TextField(blank=True)

    class Meta:
        verbose_name = "Expediente CABAL"
        verbose_name_plural = "Expedientes CABAL"
        indexes = [
            models.Index(fields=["centro", "periodo"]),
        ]
