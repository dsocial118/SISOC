from datetime import date  # pylint: disable=too-many-lines

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User

from configuraciones.models import Provincia, Localidad, Municipio, Sexo


class Dimension(models.Model):
    dimension = models.CharField(max_length=255)

    def __str__(self):
        return str(self.dimension)

    class Meta:
        verbose_name = "Dimensión"
        verbose_name_plural = "Dimensiones"


class Jurisdiccion(models.Model):
    jurisdiccion = models.CharField(max_length=255)

    def __str__(self):
        return str(self.jurisdiccion)

    class Meta:
        verbose_name = "Jurisdicción"
        verbose_name_plural = "Jurisdicciones"


class Secretarias(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    observaciones = models.CharField(max_length=500, null=True, blank=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    def clean(self):
        self.nombre = self.nombre.capitalize()

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Secretaría"
        verbose_name_plural = "Secretarías"

    def get_absolute_url(self):
        return reverse("secretarias_ver", kwargs={"pk": self.pk})


class Subsecretarias(models.Model):
    secretaria = models.ForeignKey(Secretarias, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255, unique=True)
    observaciones = models.CharField(
        max_length=500,
        null=True,
        blank=True,
    )
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    def clean(self):
        self.nombre = self.nombre.capitalize()

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Subsecretaría"
        verbose_name_plural = "Subecretarías"

    def get_absolute_url(self):
        return reverse("subsecretarias_ver", kwargs={"pk": self.pk})


class Programa(models.Model):
    subsecretaria = models.ForeignKey(Subsecretarias, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255, unique=True)
    estado = models.BooleanField(default=True)
    observaciones = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.nombre

    def clean(self):
        self.nombre = self.nombre.capitalize()

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Programa"
        verbose_name_plural = "Programas"

    def get_absolute_url(self):
        return reverse("programas_ver", kwargs={"pk": self.pk})


class PlanSocial(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    jurisdiccion = models.ForeignKey(
        Jurisdiccion, on_delete=models.CASCADE, null=True, blank=True
    )
    estado = models.BooleanField(default=True)
    observaciones = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.nombre

    def clean(self):
        self.nombre = self.nombre.capitalize()

    class Meta:
        ordering = ["nombre"]
        verbose_name = "PlanSocial"
        verbose_name_plural = "PlanesSociales"

    def get_absolute_url(self):
        return reverse("planes_sociales_ver", kwargs={"pk": self.pk})


class TipoOrganismo(models.Model):
    tipo = models.CharField(max_length=255)

    def __str__(self):
        return str(self.tipo)

    class Meta:
        verbose_name = "Tipo de Organismo"
        verbose_name_plural = "Tipos de Organismos"


class Organismo(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    tipo = models.ForeignKey(
        TipoOrganismo, on_delete=models.CASCADE, null=True, blank=True
    )
    calle = models.CharField(max_length=255, null=True, blank=True)
    altura = models.IntegerField(null=True, blank=True)
    piso = models.CharField(max_length=255, null=True, blank=True)
    barrio = models.CharField(max_length=255, null=True, blank=True)
    localidad = models.ForeignKey(
        Localidad, on_delete=models.CASCADE, null=True, blank=True
    )
    telefono = models.IntegerField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    estado = models.BooleanField(default=True)
    observaciones = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.nombre

    def clean(self):
        self.nombre = self.nombre.capitalize()

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Organismo"
        verbose_name_plural = "Organismos"

    def get_absolute_url(self):
        return reverse("organismos_ver", kwargs={"pk": self.pk})


class Circuito(models.Model):
    circuito = models.CharField(max_length=255)

    def __str__(self):
        return str(self.circuito)

    class Meta:
        verbose_name = "Circuito"
        verbose_name_plural = "Circuitos"


class CategoriaAlerta(models.Model):
    """
    Descripciones cortas que agrupan distintos tipos de alertas de vulnerabilidad.
    """

    nombre = models.CharField(max_length=255, unique=True)
    dimension = models.ForeignKey(
        Dimension, on_delete=models.CASCADE, null=True, blank=True
    )
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    def clean(self):
        self.nombre = self.nombre.capitalize()

    class Meta:
        ordering = ["nombre"]
        verbose_name = "CategoriaAlertas"
        verbose_name_plural = "CategoriasAlertas"

    def get_absolute_url(self):
        return reverse("categoriaalertas_ver", kwargs={"pk": self.pk})


class Alerta(models.Model):
    """
    Indicadores de vulnerabilidad, relacionados a una categoría específica a traves de una FK.
    """

    nombre = models.CharField(max_length=255, unique=True)
    categoria = models.ForeignKey(CategoriaAlerta, on_delete=models.CASCADE)
    estado = models.BooleanField(default=True)
    gravedad = models.CharField(max_length=500, null=False, blank=False)

    def __str__(self):
        return self.nombre

    def clean(self):
        self.nombre = self.nombre.capitalize()

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Alerta"
        verbose_name_plural = "Alertas"
        indexes = [
            models.Index(fields=["categoria"]),
            models.Index(fields=["gravedad"]),
        ]

    def get_absolute_url(self):
        return reverse("alertas_ver", kwargs={"pk": self.pk})


class NivelEducativo(models.Model):
    nivel = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nivel)

    class Meta:
        verbose_name = "Nivel Educativo"
        verbose_name_plural = "Niveles Educativos"


class EstadoNivelEducativo(models.Model):
    estado = models.CharField(max_length=255)

    def __str__(self):
        return str(self.estado)

    class Meta:
        verbose_name = "Estado Nivel Educativo"
        verbose_name_plural = "Estados Niveles Educativos"


class AsisteEscuela(models.Model):
    asiste = models.CharField(max_length=255)

    def __str__(self):
        return str(self.asiste)

    class Meta:
        verbose_name = "Asiste Escuela"
        verbose_name_plural = "Asiste Escuelas"


class MotivoNivelIncompleto(models.Model):
    motivo = models.CharField(max_length=255)

    def __str__(self):
        return str(self.motivo)

    class Meta:
        verbose_name = "Motivo Nivel Incompleto"
        verbose_name_plural = "Motivos Niveles Incompletos"


class AreaCurso(models.Model):
    area = models.CharField(max_length=255)

    def __str__(self):
        return str(self.area)

    class Meta:
        verbose_name = "Area Curso"
        verbose_name_plural = "Areas Cursos"


class TipoGestion(models.Model):
    gestion = models.CharField(max_length=255)

    def __str__(self):
        return str(self.gestion)

    class Meta:
        verbose_name = "Tipo Gestion"
        verbose_name_plural = "Tipos Gestion"


class Grado(models.Model):
    grado = models.CharField(max_length=255)

    def __str__(self):
        return str(self.grado)

    class Meta:
        verbose_name = "Grado"
        verbose_name_plural = "Grados"


class Turno(models.Model):
    turno = models.CharField(max_length=255)

    def __str__(self):
        return str(self.turno)

    class Meta:
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"


class InstitucionEducativas(models.Model):
    institucion = models.CharField(
        max_length=255,
    )

    def __str__(self):
        return str(self.institucion)

    class Meta:
        verbose_name = "Institucion Educativa"
        verbose_name_plural = "Instituciones Educativas"


class CantidadAmbientes(models.Model):
    cantidad = models.CharField(max_length=255)

    def __str__(self):
        return str(self.cantidad)

    class Meta:
        verbose_name = "Cantidad de Ambientes"
        verbose_name_plural = "Cantidades de Ambientes"


class Condicion(models.Model):
    condicion = models.CharField(max_length=255)

    def __str__(self):
        return str(self.condicion)

    class Meta:
        verbose_name = "Condición de"
        verbose_name_plural = "Condiciones de"


class UbicacionVivienda(models.Model):
    contexto = models.CharField(max_length=255)

    def __str__(self):
        return str(self.contexto)

    class Meta:
        verbose_name = "Contexto de Casa"
        verbose_name_plural = "Contextos de Casa"


class TipoVivienda(models.Model):
    tipo = models.CharField(max_length=255)

    def __str__(self):
        return str(self.tipo)

    class Meta:
        verbose_name = "Tipo de Vivienda"
        verbose_name_plural = "Tipos de Vivienda"


class TipoPosesionVivienda(models.Model):
    tipo = models.CharField(max_length=255)

    def __str__(self):
        return str(self.tipo)

    class Meta:
        verbose_name = "Tipo de Posesión de Vivienda"
        verbose_name_plural = "Tipos de Posesión de Vivienda"


class TipoPisosVivienda(models.Model):
    tipo = models.CharField(max_length=255)

    def __str__(self):
        return str(self.tipo)

    class Meta:
        verbose_name = "Tipo de Pisos de Vivienda"
        verbose_name_plural = "Tipos de Pisos de Vivienda"


class TipoTechoVivienda(models.Model):
    tipo = models.CharField(max_length=255)

    def __str__(self):
        return str(self.tipo)

    class Meta:
        verbose_name = "Tipo de Techo de Vivienda"
        verbose_name_plural = "Tipos de Techo de Vivienda"


class Agua(models.Model):
    tipo = models.CharField(max_length=255)

    def __str__(self):
        return str(self.tipo)

    class Meta:
        verbose_name = "Agua"
        verbose_name_plural = "Aguas"


class Desague(models.Model):
    tipo = models.CharField(max_length=255)

    def __str__(self):
        return str(self.tipo)

    class Meta:
        verbose_name = "Desagüe"
        verbose_name_plural = "Desagües"


class Inodoro(models.Model):
    tipo = models.CharField(max_length=255)

    def __str__(self):
        return str(self.tipo)

    class Meta:
        verbose_name = "Inodoro"
        verbose_name_plural = "Inodoros"


class Gas(models.Model):
    tipo = models.CharField(max_length=255)

    def __str__(self):
        return str(self.tipo)

    class Meta:
        verbose_name = "Gas"
        verbose_name_plural = "Gases"


class TipoConstruccionVivienda(models.Model):
    tipo = models.CharField(max_length=255)

    def __str__(self):
        return str(self.tipo)

    class Meta:
        verbose_name = "Tipo de Construcción de Vivienda"
        verbose_name_plural = "Tipos de Construcción de Vivienda"


class EstadoCivil(models.Model):
    estado = models.CharField(max_length=20)

    def __str__(self):
        return str(self.estado)

    class Meta:
        verbose_name = "Estado Civil"
        verbose_name_plural = "Estados Civiles"


class TipoDocumento(models.Model):
    tipo = models.CharField(max_length=20)

    def __str__(self):
        return str(self.tipo)

    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documentos"


class Nacionalidad(models.Model):
    nacionalidad = models.CharField(max_length=50)

    def __str__(self):
        return str(self.nacionalidad)

    class Meta:
        verbose_name = "Nacionalidad"
        verbose_name_plural = "Nacionalidades"


class CentrosSalud(models.Model):
    centro = models.CharField(max_length=255)

    def __str__(self):
        return str(self.centro)

    class Meta:
        verbose_name = "Centro de Salud"
        verbose_name_plural = "Centros de Salud"


class Frecuencia(models.Model):
    frecuencia = models.CharField(max_length=255)

    def __str__(self):
        return str(self.frecuencia)

    class Meta:
        verbose_name = "Frecuencia"
        verbose_name_plural = "Frecuencias"


class ModoContratacion(models.Model):
    modo = models.CharField(max_length=255)

    def __str__(self):
        return str(self.modo)

    class Meta:
        verbose_name = "Modo de Contratación"
        verbose_name_plural = "Modos de Contratación"


class ActividadRealizada(models.Model):
    actividad = models.CharField(max_length=255)

    def __str__(self):
        return str(self.actividad)

    class Meta:
        verbose_name = "Actividad Realizada"
        verbose_name_plural = "Actividades Realizadas"


class DuracionTrabajo(models.Model):
    duracion = models.CharField(max_length=255)

    def __str__(self):
        return str(self.duracion)

    class Meta:
        verbose_name = "Duración del Trabajo"
        verbose_name_plural = "Duraciones del Trabajo"


class AportesJubilacion(models.Model):
    aporte = models.CharField(max_length=255)

    def __str__(self):
        return str(self.aporte)

    class Meta:
        verbose_name = "Aporte Jubilación"
        verbose_name_plural = "Aportes Jubilación"


class TiempoBusquedaLaboral(models.Model):
    tiempo = models.CharField(max_length=255)

    def __str__(self):
        return str(self.tiempo)

    class Meta:
        verbose_name = "Tiempo de Búsqueda Laboral"
        verbose_name_plural = "Tiempos de Búsqueda Laboral"


class NobusquedaLaboral(models.Model):
    motivo = models.CharField(max_length=255)

    def __str__(self):
        return str(self.motivo)

    class Meta:
        verbose_name = "Motivo de No Búsqueda Laboral"
        verbose_name_plural = "Motivos de No Búsqueda Laboral"


class EstadoRelacion(models.Model):
    estado = models.CharField(max_length=255)

    def __str__(self):
        return str(self.estado)

    class Meta:
        verbose_name = "Estado de Relación"
        verbose_name_plural = "Estados de Relación"


class EstadoDerivacion(models.Model):
    estado = models.CharField(max_length=255)

    def __str__(self):
        return str(self.estado)

    class Meta:
        verbose_name = "Estado de Derivación"
        verbose_name_plural = "Estados de Derivación"


class VinculoFamiliar(models.Model):
    vinculo = models.CharField(max_length=255)
    inverso = models.CharField(max_length=255)

    def __str__(self):
        return str(self.vinculo)

    class Meta:
        verbose_name = "Vínculo Familiar"
        verbose_name_plural = "Vínculos Familiares"


class Rechazo(models.Model):
    motivo = models.CharField(max_length=255)

    def __str__(self):
        return str(self.motivo)

    class Meta:
        verbose_name = "Motivo de Rechazo"
        verbose_name_plural = "Motivos de Rechazo"


class Importancia(models.Model):
    importancia = models.CharField(max_length=255)

    def __str__(self):
        return str(self.importancia)

    class Meta:
        verbose_name = "Importancia"
        verbose_name_plural = "Importancias"


class Ciudadano(models.Model):
    """

    Guardao de los perfiles de las personas con las que interviene el Municipio.
    """

    apellido = models.CharField(max_length=255)
    nombre = models.CharField(max_length=255)
    fecha_nacimiento = models.DateField()
    tipo_documento = models.ForeignKey(
        TipoDocumento,
        verbose_name="Tipo documento",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    documento = models.PositiveIntegerField(
        validators=[MinValueValidator(3000000), MaxValueValidator(100000000)],
        null=True,
        blank=True,
    )
    sexo = models.ForeignKey(
        Sexo,
        on_delete=models.SET_NULL,
        null=True,
    )
    nacionalidad = models.ForeignKey(
        Nacionalidad, on_delete=models.SET_NULL, null=True, blank=True
    )
    estado_civil = models.ForeignKey(
        EstadoCivil, on_delete=models.SET_NULL, null=True, blank=True
    )
    calle = models.CharField(max_length=255, null=True, blank=True)
    altura = models.IntegerField(null=True, blank=True)
    latitud = models.CharField(max_length=255, null=True, blank=True)
    longitud = models.CharField(max_length=255, null=True, blank=True)
    piso_departamento = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Piso/Dpto (optativo)"
    )
    circuito = models.ForeignKey(
        Circuito, on_delete=models.SET_NULL, null=True, blank=True
    )
    torre_pasillo = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Torre / Pasillo (optativo)"
    )
    escalera_manzana = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Escalera / Manzana (optativo)",
    )

    codigo_postal = models.IntegerField(
        null=True, blank=True, verbose_name="Código Postal"
    )
    telefono = models.IntegerField(null=True, blank=True)
    telefono_alternativo = models.IntegerField(
        null=True, blank=True, verbose_name="Telefono Alternativo"
    )
    email = models.EmailField(null=True, blank=True)
    foto = models.ImageField(upload_to="ciudadanos", blank=True, null=True)
    alertas = models.ManyToManyField(Alerta, blank=True)
    familiares = models.ManyToManyField(
        "self", through="GrupoFamiliar", symmetrical=True, blank=True
    )
    observaciones = models.CharField(
        max_length=500, blank=True, null=True, verbose_name="Observaciones (optativo)"
    )
    estado = models.BooleanField(default=True)
    creado_por = models.ForeignKey(
        User,
        related_name="creado_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    modificado_por = models.ForeignKey(
        User,
        related_name="modificado_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    creado = models.DateField(auto_now_add=True)
    modificado = models.DateField(auto_now=True)
    provincia = models.ForeignKey(
        Provincia, on_delete=models.SET_NULL, null=True, blank=True
    )
    municipio = models.ForeignKey(
        Municipio, on_delete=models.SET_NULL, null=True, blank=True
    )
    localidad = models.ForeignKey(
        Localidad, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"

    def validate_unique(self, exclude=None):
        qs = Ciudadano.objects.filter(
            tipo_documento=self.tipo_documento,
            documento=self.documento,
            apellido=self.apellido,
            nombre=self.nombre,
            fecha_nacimiento=self.fecha_nacimiento,
        )

        if self.pk:
            qs = qs.exclude(pk=self.pk)

        if qs.exists():
            raise ValidationError(
                "Ya existe un ciudadano con ese TIPO y NÚMERO de documento."
            )

    def clean(self):
        # Separar y capitalizar las palabras en el campo "apellido"
        self.apellido = " ".join(word.title() for word in self.apellido.split())
        # Separar y capitalizar las palabras en el campo "nombre"
        self.nombre = " ".join(word.title() for word in self.nombre.split())

        if self.calle:
            self.calle = self.calle.capitalize()

        if self.fecha_nacimiento and self.fecha_nacimiento > date.today():
            raise ValidationError(
                "La fecha de nacimiento debe ser menor o igual a la fecha actual."
            )

    def edad(self):
        today = date.today()

        if self.fecha_nacimiento:
            age = today.year - self.fecha_nacimiento.year
            if today.month < self.fecha_nacimiento.month or (
                today.month == self.fecha_nacimiento.month
                and today.day < self.fecha_nacimiento.day
            ):
                age -= 1

            if age == 0:
                # Calcular la cantidad de meses entre las fechas
                months = (
                    (today.year - self.fecha_nacimiento.year) * 12
                    + today.month
                    - self.fecha_nacimiento.month
                )
                if months == 0:
                    # Calcular la cantidad de días entre las fechas
                    days = (today - self.fecha_nacimiento).days
                    return f"{days} días"
                return f"{months} meses"
            return f"{age}"

        return "-"

    class Meta:
        unique_together = ["tipo_documento", "documento"]
        ordering = ["apellido"]
        verbose_name = "Ciudadano"
        verbose_name_plural = "Ciudadano"
        indexes = [
            models.Index(fields=["apellido"]),
            models.Index(fields=["fecha_nacimiento"]),
            models.Index(fields=["documento"]),
            models.Index(fields=["observaciones"]),
        ]

    def get_absolute_url(self):
        return reverse("ciudadanos_ver", kwargs={"pk": self.pk})


class GrupoFamiliar(models.Model):
    """
    Guardado de las relaciones familiares de los vecinos y vecinas registrados, con una valoración que permita conocer el estado

    del vínculo desde la consideración de cada parte involucrada.
    """

    ciudadano_1 = models.ForeignKey(
        Ciudadano, related_name="ciudadano1", on_delete=models.CASCADE
    )
    ciudadano_2 = models.ForeignKey(
        Ciudadano, related_name="ciudadano2", on_delete=models.CASCADE
    )
    vinculo = models.ForeignKey(
        VinculoFamiliar, on_delete=models.SET_NULL, null=True, blank=True
    )
    vinculo_inverso = models.CharField(max_length=255, blank=True, null=True)
    estado_relacion = models.ForeignKey(
        EstadoRelacion, on_delete=models.SET_NULL, null=True, blank=True
    )
    conviven = models.BooleanField(null=True, blank=True)
    cuidador_principal = models.BooleanField(null=True, blank=True)
    observaciones = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"Ciudadano: {self.ciudadano_1} - Familiar: {self.ciudadano_2} - Vínculo: {self.vinculo}"

    class Meta:
        ordering = ["ciudadano_2"]
        unique_together = ["ciudadano_1", "ciudadano_2"]
        verbose_name = "GrupoFamiliar"
        verbose_name_plural = "CiudadanosGrupoFamiliar"
        indexes = [
            models.Index(fields=["ciudadano_1_id"]),
            models.Index(fields=["ciudadano_2_id"]),
        ]

    def get_absolute_url(self):
        return reverse("grupofamiliar_ver", kwargs={"pk": self.pk})


def convertir_positivo(value):
    if value is None:
        return 0
    if int(value) < 0:
        return int(value) * -1
    return int(value)


class DimensionFamilia(models.Model):
    """
    Guardado de la informacion de salud asociada a un Ciudadano.
    """

    ciudadano = models.OneToOneField(Ciudadano, on_delete=models.CASCADE)
    cant_hijos = models.SmallIntegerField(
        verbose_name="Cantidad de hijos", null=True, blank=True
    )
    otro_responsable = models.BooleanField(
        verbose_name="¿Hay otro adulto responsable? (Padre o apoyo en la crianza)",
        null=True,
        blank=True,
    )
    hay_embarazadas = models.BooleanField(
        verbose_name="Personas en el hogar embarazadas", null=True, blank=True
    )
    hay_prbl_smental = models.BooleanField(
        verbose_name="Personas en el hogar con problemas de salud mental",
        null=True,
        blank=True,
    )
    hay_fam_discapacidad = models.BooleanField(
        verbose_name="Personas en el hogar con discapacidad", null=True, blank=True
    )
    hay_enf_cronica = models.BooleanField(
        verbose_name="Personas en el hogar con enfermedades crónicas",
        null=True,
        blank=True,
    )
    hay_priv_libertad = models.BooleanField(
        verbose_name="Personas en el hogar privados de su libertad",
        null=True,
        blank=True,
    )
    obs_familia = models.CharField(
        verbose_name="Observaciones", max_length=500, blank=True, null=True
    )
    creado = models.DateField(auto_now_add=True)
    modificado = models.DateField(auto_now=True)

    def clean(self):
        super().clean()
        if self.cant_hijos is not None and self.cant_hijos < 0:
            raise ValidationError(
                {"cant_hijos": "La cantidad de hijos debe ser un número positivo."}
            )

    def __str__(self):
        return f"{self.ciudadano}"

    class Meta:
        ordering = ["ciudadano"]
        verbose_name = "DimensionFamilia"
        verbose_name_plural = "DimensionesFamilia"

    def get_absolute_url(self):
        return reverse("ciudadanos_ver", kwargs={"pk": self.ciudadano.id})


class DimensionVivienda(models.Model):
    """
    Guardado de los datos de vivienda asociados a un Ciudadano.
    """

    ciudadano = models.OneToOneField(Ciudadano, on_delete=models.CASCADE)
    tipo = models.ForeignKey(
        TipoVivienda,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    material = models.ForeignKey(
        TipoConstruccionVivienda,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    pisos = models.ForeignKey(
        TipoPisosVivienda,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    posesion = models.ForeignKey(
        TipoPosesionVivienda,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    cant_ambientes = models.ForeignKey(
        CantidadAmbientes,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    cant_convivientes = models.SmallIntegerField(
        verbose_name="¿Cuántas personas viven en la vivienda?",
        null=True,
        blank=True,
        default=0,
    )
    cant_menores = models.SmallIntegerField(
        verbose_name="¿Cuántos de ellos son menores de 18 años?", null=True, blank=True
    )
    cant_camas = models.SmallIntegerField(
        verbose_name="¿Cuántas camas/ colchones posee?", null=True, blank=True
    )
    cant_hogares = models.SmallIntegerField(
        verbose_name="¿Cuantos hogares hay en la vivienda?", null=True, blank=True
    )
    obs_vivienda = models.CharField(
        verbose_name="Observaciones", max_length=500, blank=True, null=True
    )
    creado = models.DateField(auto_now_add=True)
    modificado = models.DateField(auto_now=True)
    # Nuevos campos

    ubicacion_vivienda = models.ForeignKey(
        UbicacionVivienda,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    gas = models.ForeignKey(
        Gas,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    techos = models.ForeignKey(
        TipoTechoVivienda,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    agua = models.ForeignKey(
        Agua,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    desague = models.ForeignKey(
        Desague,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # Migraciones para fix de DAD-106
    hay_banio = models.ForeignKey(
        Inodoro,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    hay_desmoronamiento = models.BooleanField(
        verbose_name="Existe riesgo de desmoronamiento?",
        default=False,
    )
    PoseenCelular = models.BooleanField(
        verbose_name="¿En tu hogar cuentan con Teléfonos celulares?",
        default=False,
    )
    PoseenPC = models.BooleanField(
        verbose_name="¿En tu hogar cuentan con Computadoras? (de escritorio / laptop / tablet) ",
        default=False,
    )
    Poseeninternet = models.BooleanField(
        verbose_name="En tu hogar cuentan con Internet (a través del celular o por conexión en la vivienda - wifi)",
        default=False,
    )
    hay_agua_caliente = models.BooleanField(
        verbose_name="¿Posee Agua caliente?",
        default=False,
    )

    def save(self, *args, **kwargs):
        self.cant_convivientes = convertir_positivo(self.cant_convivientes)
        self.cant_menores = convertir_positivo(self.cant_menores)
        self.cant_camas = convertir_positivo(self.cant_camas)
        self.cant_hogares = convertir_positivo(self.cant_hogares)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ciudadano}"

    class Meta:
        ordering = ["ciudadano"]
        verbose_name = "DimensionVivienda"
        verbose_name_plural = "DimensionesVivienda"
        indexes = [models.Index(fields=["ciudadano"])]

    def get_absolute_url(self):
        return reverse("ciudadanos_ver", kwargs={"pk": self.ciudadano.id})


class DimensionSalud(models.Model):
    """
    Guardado de la informacion de salud asociada a un Ciudadano.
    """

    ciudadano = models.OneToOneField(Ciudadano, on_delete=models.CASCADE)
    lugares_atencion = models.ForeignKey(
        CentrosSalud,
        verbose_name="Centro de Salud en donde se atiende",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    frecuencia_controles_medicos = models.ForeignKey(
        Frecuencia,
        verbose_name="¿Con qué frecuencia realiza controles médicos?",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    hay_obra_social = models.BooleanField(
        verbose_name="¿Posee cobertura de salud?", null=True, blank=True
    )
    hay_enfermedad = models.BooleanField(
        verbose_name="¿Posee alguna enfermedad recurrente o crónica?",
        null=True,
        blank=True,
    )
    hay_discapacidad = models.BooleanField(
        verbose_name="¿Posee alguna discapacidad?", null=True, blank=True
    )
    hay_cud = models.BooleanField(
        verbose_name="¿Posee certificado de discapacidad?", null=True, blank=True
    )
    obs_salud = models.CharField(
        verbose_name="Observaciones", max_length=500, blank=True, null=True
    )
    creado = models.DateField(auto_now_add=True)
    modificado = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.ciudadano}"

    class Meta:
        ordering = ["ciudadano"]
        verbose_name = "DimensionSalud"
        verbose_name_plural = "DimensionesSalud"
        indexes = [models.Index(fields=["ciudadano"])]

    def get_absolute_url(self):
        return reverse("ciudadanos_ver", kwargs={"pk": self.ciudadano.id})


class DimensionEducacion(models.Model):
    ciudadano = models.OneToOneField(Ciudadano, on_delete=models.CASCADE)
    max_nivel = models.ForeignKey(
        NivelEducativo,
        verbose_name="Máximo nivel educativo alcanzado",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="max_nivel_dimension",
    )
    estado_nivel = models.ForeignKey(
        EstadoNivelEducativo,
        verbose_name="Estado del nivel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    asiste_escuela = models.ForeignKey(
        AsisteEscuela,
        verbose_name="¿Asistís o asististe alguna vez a algún establecimiento educativo?",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    institucion = models.ForeignKey(
        InstitucionEducativas,
        verbose_name="Escuela",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    gestion = models.ForeignKey(
        TipoGestion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Tipo de gestión",
    )
    ciclo = models.ForeignKey(
        NivelEducativo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ciclo_dimension",
    )
    grado = models.ForeignKey(Grado, on_delete=models.SET_NULL, null=True, blank=True)
    turno = models.ForeignKey(
        Turno, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Turno"
    )
    observaciones = models.CharField(
        max_length=500, verbose_name="Observaciones", null=True, blank=True
    )
    creado = models.DateField(auto_now_add=True)
    modificado = models.DateField(auto_now=True)
    acepta_terminos = models.BooleanField(
        verbose_name="Acepto los términos y condiciones", default=False
    )
    # Nuevos campos dimencion estudio
    provinciaInstitucion = models.ForeignKey(
        Provincia,
        on_delete=models.SET_NULL,
        verbose_name="Provincia de la institucion",
        null=True,
        blank=True,
    )
    localidadInstitucion = models.ForeignKey(
        Localidad,
        on_delete=models.SET_NULL,
        verbose_name="Localidad de la institucion",
        null=True,
        blank=True,
    )
    municipioInstitucion = models.ForeignKey(
        Municipio,
        on_delete=models.SET_NULL,
        verbose_name="Municipio de la institucion",
        null=True,
        blank=True,
    )
    barrio_institucion = models.CharField(
        verbose_name="Barrio", max_length=255, null=True, blank=True
    )
    calle_institucion = models.CharField(
        verbose_name="Calle", max_length=255, null=True, blank=True
    )
    numero_institucion = models.CharField(
        verbose_name="Número", max_length=255, null=True, blank=True
    )
    nivel_incompleto = models.ForeignKey(
        MotivoNivelIncompleto,
        verbose_name="¿Cuál fue el motivo principal por el que no terminaste tus estudios?",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nivel_incompleto_dimension",
    )
    sin_educacion_formal = models.ForeignKey(
        MotivoNivelIncompleto,
        verbose_name="¿Cuál fue el motivo principal por el que nunca asististe a un establecimiento educativo?",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sin_edu_formal_dimension",
    )
    realizando_curso = models.BooleanField(
        verbose_name="¿Actualmente te encontrás haciendo algún curso de capacitación?",
        default=False,
    )
    area_curso = models.ForeignKey(
        AreaCurso,
        verbose_name="¿En qué áreas?",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="area_curso_dimension",
    )
    interes_capacitacion_laboral = models.BooleanField(
        verbose_name="¿Tenés interés en realizar cursos de capacitación laboral?",
        default=False,
    )
    oficio = models.BooleanField(
        verbose_name="¿Tenés conocimiento de algún oficio?",
        default=False,
    )
    area_oficio = models.ForeignKey(
        AreaCurso,
        verbose_name="¿En qué áreas?",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="area_oficio_dimension",
    )

    interes_estudio = models.BooleanField(
        verbose_name="¿Le interesa estudiar?",
        default=False,
    )
    interes_curso = models.BooleanField(
        verbose_name="¿le interesa algun curso?",
        default=False,
    )

    def __str__(self):
        return f"{self.ciudadano}"

    class Meta:
        ordering = ["ciudadano"]
        verbose_name = "DimensionEducacion"
        verbose_name_plural = "DimensionesEducacion"
        indexes = [models.Index(fields=["ciudadano"])]

    def get_absolute_url(self):
        return reverse("ciudadanos_ver", kwargs={"pk": self.ciudadano.id})


class DimensionEconomia(models.Model):
    """
    Guardado de los datos económicos asociados a un Ciudadano.
    """

    ciudadano = models.OneToOneField(Ciudadano, on_delete=models.CASCADE)
    planes = models.ManyToManyField(PlanSocial, blank=True)
    cant_aportantes = models.SmallIntegerField(
        verbose_name="¿Cuántos miembros reciben ingresos por plan social o aportan al grupo familiar?",
        null=True,
        blank=True,
    )
    obs_economia = models.CharField(
        max_length=500, verbose_name="Observaciones", null=True, blank=True
    )
    creado = models.DateField(auto_now_add=True)
    modificado = models.DateField(auto_now=True)

    # Migraciones para fix de DAD-123

    ingresos = models.PositiveIntegerField(
        verbose_name="Ingresos Mensuales ", null=True, blank=True
    )
    recibe_plan = models.BooleanField(
        verbose_name="¿Recibe planes sociales?",
        default=False,
    )

    def save(self, *args, **kwargs):
        self.ingresos = convertir_positivo(self.ingresos)
        self.cant_aportantes = convertir_positivo(self.cant_aportantes)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ciudadano}"

    class Meta:
        ordering = ["ciudadano"]
        verbose_name = "DimensionEconomica"
        verbose_name_plural = "DimensionesEconomicas"
        indexes = [models.Index(fields=["ciudadano"])]

    def get_absolute_url(self):
        return reverse("ciudadanos_ver", kwargs={"pk": self.ciudadano.id})


class DimensionTrabajo(models.Model):
    ciudadano = models.OneToOneField(Ciudadano, on_delete=models.CASCADE)
    modo_contratacion = models.ForeignKey(
        ModoContratacion, on_delete=models.SET_NULL, null=True, blank=True
    )
    ocupacion = models.CharField(max_length=255, null=True, blank=True)
    obs_trabajo = models.CharField(
        max_length=500, verbose_name="Observaciones", null=True, blank=True
    )
    creado = models.DateField(auto_now_add=True)
    modificado = models.DateField(auto_now=True)
    # NUEVOS CAMPOS DIMENSION TRABAJO
    horasSemanales = models.CharField(
        verbose_name=(
            "Considerando todas las actividades que realizás en una semana, "
            "por las que recibís algún pago, sea en dinero o en especie, "
            "¿cuántas horas por semana trabajas habitualmente?"
        ),
        max_length=255,
        null=True,
        blank=True,
    )
    actividadRealizadaComo = models.ForeignKey(
        ActividadRealizada,
        verbose_name="Esa actividad la realizás como…",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    duracionTrabajo = models.ForeignKey(
        DuracionTrabajo,
        verbose_name="¿Este trabajo es…",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    aportesJubilacion = models.ForeignKey(
        AportesJubilacion,
        verbose_name="Por ese trabajo, ¿te descuentan jubilación o aportas vos mismo?",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    Tiempobusqueda_laboral = models.ForeignKey(
        TiempoBusquedaLaboral,
        verbose_name="¿Cuánto hace que buscás trabajo?",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    busqueda_laboral = models.BooleanField(
        verbose_name="¿Buscaste trabajo en los últimos 30 días?",
        null=True,
        blank=True,
    )
    nobusqueda_laboral = models.ForeignKey(
        NobusquedaLaboral,
        verbose_name="¿Por qué motivo no buscaste trabajo? (Indicá el motivo principal)",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # Migraciones para fix de DAD-128
    conviviente_trabaja = models.BooleanField(
        verbose_name="¿Conviviente trabaja?",
        null=True,
        blank=True,
    )
    tiene_trabajo = models.BooleanField(
        verbose_name="¿Actualmente realizás alguna actividad laboral, productiva o comunitaria?",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.ciudadano}"

    class Meta:
        ordering = ["ciudadano"]
        verbose_name = "DimensionLaboral"
        verbose_name_plural = "DimensionesLaborales"
        indexes = [models.Index(fields=["ciudadano"])]

    def get_absolute_url(self):
        return reverse("dimensionlaboral_ver", kwargs={"pk": self.pk})


class CiudadanoPrograma(models.Model):
    programas = models.ForeignKey(
        Programa, related_name="programa_ciudadano", on_delete=models.CASCADE
    )
    ciudadano = models.ForeignKey(
        Ciudadano, related_name="ciudadano_programa", on_delete=models.CASCADE
    )
    fecha_creado = models.DateField(auto_now=True)
    creado_por = models.ForeignKey(
        User,
        related_name="prog_creado_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-fecha_creado"]
        verbose_name = "CiudadanoProgramas"
        verbose_name_plural = "CiudadanosProgramas"


class HistorialCiudadanoProgramas(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    accion = models.CharField(
        max_length=10, choices=[("agregado", "Agregado"), ("eliminado", "Eliminado")]
    )
    programa = models.ForeignKey(
        Programa, related_name="hist_prog_ciudadano", on_delete=models.CASCADE
    )
    ciudadano = models.ForeignKey(
        Ciudadano, related_name="hist_ciudadano_programa", on_delete=models.CASCADE
    )
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Historial CiudadanoPrograma"
        verbose_name_plural = "Historial CiudadanosProgramas"

    def __str__(self):
        return f"{self.fecha} - {self.accion} - {self.programa} - {self.ciudadano}"


class HistorialAlerta(models.Model):
    """
    Guardado de historial de los distintos movimientos (CREACION/ELIMINACION)  de alertas de vulnerabilidad asociadas a un Ciudadano.
    Se graban a traves funciones detalladas en el archivo signals.py de esta app.
    """

    alerta = models.ForeignKey(
        Alerta, related_name="hist_alerta", on_delete=models.CASCADE
    )
    ciudadano = models.ForeignKey(
        Ciudadano, related_name="hist_ciudadano_alerta", on_delete=models.CASCADE
    )
    observaciones = models.CharField(max_length=255, null=True, blank=True)
    creada_por = models.ForeignKey(
        User,
        related_name="hist_creada_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    eliminada_por = models.ForeignKey(
        User,
        related_name="hist_eliminada_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    fecha_inicio = models.DateField(auto_now=True)
    fecha_fin = models.DateField(null=True, blank=True)
    # Campo para almacenar los meses en los que estuvo activa
    meses_activa = models.JSONField(default=list, blank=True)

    def __str__(self):
        return str(self.alerta.categoria.dimension)

    # Método para calcular el estado (Activa o Inactiva) basado en la existencia de fecha_fin
    @property
    def estado(self):
        return "Activa" if self.fecha_fin is None else "Inactiva"

    class Meta:
        ordering = ["-fecha_inicio"]
        verbose_name = "HistorialAlerta"
        verbose_name_plural = "HistorialesAlerta"
        indexes = [models.Index(fields=["ciudadano"])]


class Derivacion(models.Model):
    """
    Registro de todas las derivaciones a programas que funcionen dentro del sistema.
    """

    ciudadano = models.ForeignKey(Ciudadano, on_delete=models.CASCADE)
    programa_solicitante = models.ForeignKey(
        Programa, related_name="programa_solicitante", on_delete=models.CASCADE
    )
    programa = models.ForeignKey(
        Programa, related_name="programa_derivado", on_delete=models.CASCADE
    )
    organismo = models.ForeignKey(
        Organismo, on_delete=models.CASCADE, null=True, blank=True
    )
    detalles = models.CharField(max_length=500, null=True, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    importancia = models.ForeignKey(
        Importancia, on_delete=models.SET_NULL, null=True, blank=True, default="Alta"
    )
    estado = models.ForeignKey(
        EstadoDerivacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default="Pendiente",
    )
    alertas = models.ManyToManyField(CategoriaAlerta, blank=True)
    archivos = models.FileField(upload_to="ciudadanos/archivos", null=True, blank=True)
    motivo_rechazo = models.ForeignKey(
        Rechazo, on_delete=models.SET_NULL, null=True, blank=True
    )
    obs_rechazo = models.CharField(max_length=500, null=True, blank=True)
    fecha_rechazo = models.DateField(null=True, blank=True)
    fecha_creado = models.DateField(auto_now_add=True, null=True, blank=True)
    fecha_modificado = models.DateField(auto_now=True)

    def __str__(self):
        return self.ciudadano.apellido + ", " + self.ciudadano.nombre

    class Meta:
        ordering = ["-fecha_creado"]
        verbose_name = "CiudadanoDerivacion"
        verbose_name_plural = "CiudadanosDerivaciones"
        indexes = [models.Index(fields=["ciudadano"]), models.Index(fields=["estado"])]

    def get_absolute_url(self):
        return reverse("ciudadanosderivaciones_ver", kwargs={"pk": self.pk})


class Archivo(models.Model):
    """
    Archivos asociados a un ciudadano. En la view se separaran los archivos de imagen de los documentos (para mostrar los primeros enun carousel)
    """

    ciudadano = models.ForeignKey(Ciudadano, on_delete=models.CASCADE)
    archivo = models.FileField(upload_to="ciudadanos/archivos/")
    fecha = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=255)

    class Meta:
        indexes = [models.Index(fields=["ciudadano"])]

    def __str__(self):
        return f"Archivo {self.id} del ciudadano {self.ciudadano}"


class GrupoHogar(models.Model):
    """
    Guardado de las relaciones familiares de los vecinos y vecinas registrados,
    con una valoración que permita conocer el estado del vínculo desde la
    consideración de cada parte involucrada.
    """

    ciudadano_1Hogar = models.ForeignKey(
        Ciudadano, on_delete=models.CASCADE, related_name="hogar_1"
    )
    ciudadano_2Hogar = models.ForeignKey(
        Ciudadano, on_delete=models.CASCADE, related_name="hogar_2"
    )
    estado_relacion = models.ForeignKey(
        EstadoRelacion, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"Ciudadano: {self.ciudadano_1Hogar} - Hogar: {self.ciudadano_2Hogar}"

    class Meta:
        ordering = ["ciudadano_2Hogar"]
        verbose_name = "GrupoHogarForm"
        verbose_name_plural = "GrupoHogarForm"
        indexes = [
            models.Index(fields=["ciudadano_1Hogar"]),
            models.Index(fields=["ciudadano_2Hogar"]),
        ]

    def get_absolute_url(self):
        return reverse("GrupoHogarForm_ver", kwargs={"pk": self.pk})


class TipoIntervencion(models.Model):
    """
    Guardado de los tipos de intervenciones realizadas a un ciudadano.
    """

    nombre = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nombre}"

    class Meta:
        verbose_name = "TipoIntervencion"
        verbose_name_plural = "TiposIntervencion"


class SubIntervencion(models.Model):
    """
    Guardado de las SubIntervencion realizadas a un ciudadano.
    """

    nombre = models.CharField(max_length=255)
    subintervencion = models.ForeignKey(
        TipoIntervencion, on_delete=models.SET_NULL, default=1, null=True
    )

    def __str__(self):
        return f"{self.nombre}"

    class Meta:
        verbose_name = "SubIntervencion"
        verbose_name_plural = "SubIntervenciones"


class EstadoIntervencion(models.Model):
    """
    Guardado de los estados de las intervenciones realizadas a un ciudadano.
    """

    nombre = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nombre}"

    class Meta:
        verbose_name = "EstadosIntervencion"
        verbose_name_plural = "EstadosIntervenciones"


class Direccion(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nombre}"


# TODO: Unificar con el modelo Intervencion de Comedores
class Intervencion(models.Model):
    """
    Guardado de las intervenciones realizadas a un ciudadano.
    """

    ciudadano = models.ForeignKey(Ciudadano, on_delete=models.SET_NULL, null=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    subintervencion = models.ForeignKey(
        SubIntervencion, on_delete=models.SET_NULL, null=True
    )
    tipo_intervencion = models.ForeignKey(
        TipoIntervencion, on_delete=models.SET_NULL, null=True
    )
    fecha = models.DateTimeField(auto_now_add=True)
    direccion = models.ManyToManyField(Direccion)
    estado = models.ForeignKey(
        EstadoIntervencion, on_delete=models.SET_NULL, default=1, null=True
    )

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Intervencion"
        verbose_name_plural = "Intervenciones"
        indexes = [models.Index(fields=["ciudadano"])]


class ProgramasLlamados(models.Model):
    """
    Guardado de los programas a los que se llama.
    """

    nombre = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nombre}"

    class Meta:
        verbose_name = "ProgramasLlamados"
        verbose_name_plural = "ProgramasLlamados"


class EstadoLlamado(models.Model):
    """
    Guardado de los estados de las intervenciones realizadas a un ciudadano.
    """

    nombre = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nombre}"

    class Meta:
        verbose_name = "EstadoLlamado"
        verbose_name_plural = "EstadosLlamados"


class TipoLlamado(models.Model):
    """
    Guardado de los tipos de llamados realizados a un ciudadano.
    """

    nombre = models.CharField(max_length=255)
    programas_llamados = models.ForeignKey(
        ProgramasLlamados, on_delete=models.SET_NULL, null=True
    )

    def __str__(self):
        return f"{self.nombre}"

    class Meta:
        verbose_name = "TipoLlamado"
        verbose_name_plural = "TiposLammado"


class SubtipoLlamado(models.Model):
    """
    Guardado de los subtipo_llamado realizados a un ciudadano.
    """

    def __str__(self):
        return f"{self.nombre}"

    nombre = models.CharField(max_length=255)
    tipo_llamado = models.ForeignKey(
        TipoLlamado, on_delete=models.SET_NULL, default=1, null=True
    )

    class Meta:
        verbose_name = "subtipo_llamado"
        verbose_name_plural = "SubTiposLlamado"


class Llamado(models.Model):
    """
    Guardado de los llamados realizados a un ciudadano.
    """

    ciudadano = models.ForeignKey(Ciudadano, on_delete=models.SET_NULL, null=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    subtipo_llamado = models.ForeignKey(
        SubtipoLlamado, on_delete=models.SET_NULL, null=True
    )
    tipo_llamado = models.ForeignKey(TipoLlamado, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.ForeignKey(
        EstadoLlamado, on_delete=models.SET_NULL, default=1, null=True
    )
    programas_llamados = models.ForeignKey(
        ProgramasLlamados, on_delete=models.SET_NULL, null=True
    )

    observaciones = models.CharField(max_length=500)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Llamado"
        verbose_name_plural = "Llamados"
        indexes = [models.Index(fields=["ciudadano"])]
