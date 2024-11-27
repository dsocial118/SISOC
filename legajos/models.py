from datetime import date  # pylint: disable=too-many-lines

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse

from configuraciones.models import (
    Alertas,
    CategoriaAlertas,
    Circuito,
    Organismos,
    PlanesSociales,
    Programas,
)
from configuraciones.models import Provincia
from configuraciones.models import Municipio
from configuraciones.models import Departamento
from configuraciones.models import Localidad
from configuraciones.models import Asentamiento
from usuarios.models import User, Usuarios

# Modelo para choices de dimension educacion


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


class EstadoEducativo(models.Model):
    estado = models.CharField(max_length=255)

    def __str__(self):
        return str(self.estado)

    class Meta:
        verbose_name = "Estado Educativo"
        verbose_name_plural = "Estados Educativos"


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


# TODO : Crear choices para instituciones educativas
class InstitucionesEducativas(models.Model):
    institucion = models.CharField(
        max_length=255,
    )

    def __str__(self):
        return str(self.institucion)

    class Meta:
        verbose_name = "Institucion Educativa"
        verbose_name_plural = "Instituciones Educativas"


# Fin de modelo para choices de dimension educacion

# Modelo para choices de dimension Vivienda


class CantidadAmbientes(models.Model):
    cantidad = models.CharField(max_length=255)

    def __str__(self):
        return str(self.cantidad)

    class Meta:
        verbose_name = "Cantidad de Ambientes"
        verbose_name_plural = "Cantidades de Ambientes"


class CondicionDe(models.Model):
    condicion = models.CharField(max_length=255)

    def __str__(self):
        return str(self.condicion)

    class Meta:
        verbose_name = "Condición de"
        verbose_name_plural = "Condiciones de"


class ContextoCasa(models.Model):
    contexto = models.CharField(max_length=255)

    def __str__(self):
        return str(self.contexto)

    class Meta:
        verbose_name = "Contexto de Casa"
        verbose_name_plural = "Contextos de Casa"


class TipoAyudaHogar(models.Model):
    tipo = models.CharField(max_length=255)

    def __str__(self):
        return str(self.tipo)

    class Meta:
        verbose_name = "Tipo de Ayuda al Hogar"
        verbose_name_plural = "Tipos de Ayuda al Hogar"


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


class TipoEstadoVivienda(models.Model):
    tipo = models.CharField(max_length=255)

    def __str__(self):
        return str(self.tipo)

    class Meta:
        verbose_name = "Tipo de Estado de Vivienda"
        verbose_name_plural = "Tipos de Estado de Vivienda"


# Fin de modelo para choices de dimension Vivienda


# Modelo para choices de datos personales
class EstadoCivil(models.Model):
    estado = models.CharField(max_length=20)

    def __str__(self):
        return str(self.estado)

    class Meta:
        verbose_name = "Estado Civil"
        verbose_name_plural = "Estados Civiles"


class Sexo(models.Model):
    sexo = models.CharField(max_length=10)

    def __str__(self):
        return str(self.sexo)

    class Meta:
        verbose_name = "Sexo"
        verbose_name_plural = "Sexos"


class Genero(models.Model):
    genero = models.CharField(max_length=20)

    def __str__(self):
        return str(self.genero)

    class Meta:
        verbose_name = "Género"
        verbose_name_plural = "Géneros"


class GeneroPronombre(models.Model):
    pronombre = models.CharField(max_length=10)

    def __str__(self):
        return str(self.pronombre)

    class Meta:
        verbose_name = "Género Pronombre"
        verbose_name_plural = "Géneros Pronombres"


class TipoDoc(models.Model):
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


# fin de modelo para choices de datos personales
# Modelo para choices de dimension trabajo y salud


class TipoDiscapacidad(models.Model):
    tipo = models.CharField(max_length=255)

    def __str__(self):
        return str(self.tipo)

    class Meta:
        verbose_name = "Tipo de Discapacidad"
        verbose_name_plural = "Tipos de Discapacidad"


class TipoEnfermedad(models.Model):
    tipo = models.CharField(max_length=255)

    def __str__(self):
        return str(self.tipo)

    class Meta:
        verbose_name = "Tipo de Enfermedad"
        verbose_name_plural = "Tipos de Enfermedad"


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


class NoBusquedaLaboral(models.Model):
    motivo = models.CharField(max_length=255)

    def __str__(self):
        return str(self.motivo)

    class Meta:
        verbose_name = "Motivo de No Búsqueda Laboral"
        verbose_name_plural = "Motivos de No Búsqueda Laboral"


class Nivel(models.Model):
    nivel = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nivel)

    class Meta:
        verbose_name = "Nivel"
        verbose_name_plural = "Niveles"


class Accion(models.Model):
    accion = models.CharField(max_length=255)

    def __str__(self):
        return str(self.accion)

    class Meta:
        verbose_name = "Acción"
        verbose_name_plural = "Acciones"


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


class EstadoIntervencion(models.Model):
    estado = models.CharField(max_length=255)

    def __str__(self):
        return str(self.estado)

    class Meta:
        verbose_name = "Estado de Intervención"
        verbose_name_plural = "Estados de Intervención"


class EstadoLlamado(models.Model):
    estado = models.CharField(max_length=255)

    def __str__(self):
        return str(self.estado)

    class Meta:
        verbose_name = "Estado de Llamado"
        verbose_name_plural = "Estados de Llamado"


class Importancia(models.Model):
    importancia = models.CharField(max_length=255)

    def __str__(self):
        return str(self.importancia)

    class Meta:
        verbose_name = "Importancia"
        verbose_name_plural = "Importancias"


# fin de modelo para choices de dimension trabajo y salud


class Legajos(models.Model):
    """

    Guardao de los perfiles de las personas con las que interviene el Municipio.
    """

    apellido = models.CharField(max_length=255)
    nombre = models.CharField(max_length=255)
    fecha_nacimiento = models.DateField()
    tipo_doc = models.ForeignKey(
        TipoDoc,
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
    pisodpto = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Piso/Dpto (optativo)"
    )
    # TODO: choice viene de configuraciones.choices remplazar despues.
    circuito = models.ForeignKey(
        Circuito, on_delete=models.SET_NULL, null=True, blank=True
    )
    torrepasillo = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Torre / Pasillo (optativo)"
    )
    escaleramanzana = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Escalera / Manzana (optativo)",
    )

    codigopostal = models.IntegerField(
        null=True, blank=True, verbose_name="Código Postal"
    )
    telefono = models.IntegerField(null=True, blank=True)
    telefonoalt = models.IntegerField(
        null=True, blank=True, verbose_name="Telefono Alternativo"
    )
    email = models.EmailField(null=True, blank=True)
    foto = models.ImageField(upload_to="legajos", blank=True, null=True)
    m2m_alertas = models.ManyToManyField(Alertas, through="LegajoAlertas", blank=True)
    m2m_familiares = models.ManyToManyField(
        "self", through="LegajoGrupoFamiliar", symmetrical=True, blank=True
    )
    observaciones = models.CharField(
        max_length=500, blank=True, null=True, verbose_name="Observaciones (optativo)"
    )
    estado = models.BooleanField(default=True)
    creado_por = models.ForeignKey(
        Usuarios,
        related_name="creado_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    modificado_por = models.ForeignKey(
        Usuarios,
        related_name="modificado_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    creado = models.DateField(auto_now_add=True)
    modificado = models.DateField(auto_now=True)
    fk_provincia = models.ForeignKey(
        Provincia, on_delete=models.SET_NULL, null=True, blank=True
    )
    fk_municipio = models.ForeignKey(
        Municipio, on_delete=models.SET_NULL, null=True, blank=True
    )
    fk_localidad = models.ForeignKey(
        Localidad, on_delete=models.SET_NULL, null=True, blank=True
    )
    fk_departamento = models.ForeignKey(
        Departamento, on_delete=models.SET_NULL, null=True, blank=True
    )
    fk_asentamiento = models.ForeignKey(
        Asentamiento, on_delete=models.SET_NULL, null=True, blank=True
    )
    cuil = models.BigIntegerField(null=True, blank=True)
    _id = models.CharField(max_length=255, null=True, blank=True)
    cuit = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"

    def validate_unique(self, exclude=None):
        qs = Legajos.objects.filter(
            tipo_doc=self.tipo_doc,
            documento=self.documento,
            apellido=self.apellido,
            nombre=self.nombre,
            fecha_nacimiento=self.fecha_nacimiento,
        )

        if self.pk:
            qs = qs.exclude(pk=self.pk)

        if qs.exists():
            raise ValidationError(
                "Ya existe un legajo con ese TIPO y NÚMERO de documento."
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
        unique_together = ["tipo_doc", "documento"]
        ordering = ["apellido"]
        verbose_name = "Legajo"
        verbose_name_plural = "Legajos"
        indexes = [
            models.Index(fields=["apellido"]),
            models.Index(fields=["fecha_nacimiento"]),
            models.Index(fields=["documento"]),
            models.Index(fields=["observaciones"]),
        ]

    def get_absolute_url(self):
        return reverse("legajos_ver", kwargs={"pk": self.pk})


class LegajoGrupoFamiliar(models.Model):
    """
    Guardado de las relaciones familiares de los vecinos y vecinas registrados, con una valoración que permita conocer el estado

    del vínculo desde la consideración de cada parte involucrada.
    """

    fk_legajo_1 = models.ForeignKey(
        Legajos, related_name="fk_legajo1", on_delete=models.CASCADE
    )
    fk_legajo_2 = models.ForeignKey(
        Legajos, related_name="fk_legajo2", on_delete=models.CASCADE
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
        return f"Legajo: {self.fk_legajo_1} - Familiar: {self.fk_legajo_2} - Vínculo: {self.vinculo}"

    class Meta:
        ordering = ["fk_legajo_2"]
        unique_together = ["fk_legajo_1", "fk_legajo_2"]
        verbose_name = "LegajoGrupoFamiliar"
        verbose_name_plural = "LegajosGrupoFamiliar"
        indexes = [
            models.Index(fields=["fk_legajo_1_id"]),
            models.Index(fields=["fk_legajo_2_id"]),
        ]

    def get_absolute_url(self):
        return reverse("legajogrupofamiliar_ver", kwargs={"pk": self.pk})


def convertir_positivo(value):
    if value is None:
        return 0
    if int(value) < 0:
        return int(value) * -1
    return int(value)


class DimensionFamilia(models.Model):
    """
    Guardado de la informacion de salud asociada a un Legajo.
    """

    fk_legajo = models.OneToOneField(Legajos, on_delete=models.CASCADE)
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
        return f"{self.fk_legajo}"

    class Meta:
        ordering = ["fk_legajo"]
        verbose_name = "DimensionFamilia"
        verbose_name_plural = "DimensionesFamilia"

    def get_absolute_url(self):
        return reverse("legajos_ver", kwargs={"pk": self.fk_legajo.id})


class DimensionVivienda(models.Model):
    """
    Guardado de los datos de vivienda asociados a un Legajo.
    """

    fk_legajo = models.OneToOneField(Legajos, on_delete=models.CASCADE)
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

    ContextoCasa = models.ForeignKey(
        ContextoCasa,
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
        return f"{self.fk_legajo}"

    class Meta:
        ordering = ["fk_legajo"]
        verbose_name = "DimensionVivienda"
        verbose_name_plural = "DimensionesVivienda"
        indexes = [models.Index(fields=["fk_legajo"])]

    def get_absolute_url(self):
        return reverse("legajos_ver", kwargs={"pk": self.fk_legajo.id})


class DimensionSalud(models.Model):
    """
    Guardado de la informacion de salud asociada a un Legajo.
    """

    fk_legajo = models.OneToOneField(Legajos, on_delete=models.CASCADE)
    lugares_atencion = models.ForeignKey(
        CentrosSalud,
        verbose_name="Centro de Salud en donde se atiende",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    frec_controles = models.ForeignKey(
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
        return f"{self.fk_legajo}"

    class Meta:
        ordering = ["fk_legajo"]
        verbose_name = "DimensionSalud"
        verbose_name_plural = "DimensionesSalud"
        indexes = [models.Index(fields=["fk_legajo"])]

    def get_absolute_url(self):
        return reverse("legajos_ver", kwargs={"pk": self.fk_legajo.id})


class DimensionEducacion(models.Model):
    fk_legajo = models.OneToOneField(Legajos, on_delete=models.CASCADE)
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

    # TODO: Crear choices para instituciones educativas
    institucion = models.ForeignKey(
        InstitucionesEducativas,
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
    obs_educacion = models.CharField(
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
    barrioInstitucion = models.CharField(
        verbose_name="Barrio", max_length=255, null=True, blank=True
    )
    calleInstitucion = models.CharField(
        verbose_name="Calle", max_length=255, null=True, blank=True
    )
    numeroInstitucion = models.CharField(
        verbose_name="Número", max_length=255, null=True, blank=True
    )
    nivelIncompleto = models.ForeignKey(
        MotivoNivelIncompleto,
        verbose_name="¿Cuál fue el motivo principal por el que no terminaste tus estudios?",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nivel_incompleto_dimension",
    )
    sinEduFormal = models.ForeignKey(
        MotivoNivelIncompleto,
        verbose_name="¿Cuál fue el motivo principal por el que nunca asististe a un establecimiento educativo?",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sin_edu_formal_dimension",
    )
    realizandoCurso = models.BooleanField(
        verbose_name="¿Actualmente te encontrás haciendo algún curso de capacitación?",
        default=False,
    )
    areaCurso = models.ForeignKey(
        AreaCurso,
        verbose_name="¿En qué áreas?",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="area_curso_dimension",
    )
    interesCapLab = models.BooleanField(
        verbose_name="¿Tenés interés en realizar cursos de capacitación laboral?",
        default=False,
    )
    oficio = models.BooleanField(
        verbose_name="¿Tenés conocimiento de algún oficio?",
        default=False,
    )
    areaOficio = models.ForeignKey(
        AreaCurso,
        verbose_name="¿En qué áreas?",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="area_oficio_dimension",
    )

    # Migraciones para fix de DAD-118
    interesEstudio = models.BooleanField(
        verbose_name="¿Le interesa estudiar?",
        default=False,
    )
    interesCurso = models.BooleanField(
        verbose_name="¿le interesa algun curso?",
        default=False,
    )

    def __str__(self):
        return f"{self.fk_legajo}"

    class Meta:
        ordering = ["fk_legajo"]
        verbose_name = "DimensionEducacion"
        verbose_name_plural = "DimensionesEducacion"
        indexes = [models.Index(fields=["fk_legajo"])]

    def get_absolute_url(self):
        return reverse("legajos_ver", kwargs={"pk": self.fk_legajo.id})


class DimensionEconomia(models.Model):
    """
    Guardado de los datos económicos asociados a un Legajo.
    """

    fk_legajo = models.OneToOneField(Legajos, on_delete=models.CASCADE)
    m2m_planes = models.ManyToManyField(PlanesSociales, blank=True)
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
        return f"{self.fk_legajo}"

    class Meta:
        ordering = ["fk_legajo"]
        verbose_name = "DimensionEconomica"
        verbose_name_plural = "DimensionesEconomicas"
        indexes = [models.Index(fields=["fk_legajo"])]

    def get_absolute_url(self):
        return reverse("legajos_ver", kwargs={"pk": self.fk_legajo.id})


class DimensionTrabajo(models.Model):
    fk_legajo = models.OneToOneField(Legajos, on_delete=models.CASCADE)
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
    TiempoBusquedaLaboral = models.ForeignKey(
        TiempoBusquedaLaboral,
        verbose_name="¿Cuánto hace que buscás trabajo?",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    busquedaLaboral = models.BooleanField(
        verbose_name="¿Buscaste trabajo en los últimos 30 días?",
        null=True,
        blank=True,
    )
    noBusquedaLaboral = models.ForeignKey(
        NoBusquedaLaboral,
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
        return f"{self.fk_legajo}"

    class Meta:
        ordering = ["fk_legajo"]
        verbose_name = "DimensionLaboral"
        verbose_name_plural = "DimensionesLaborales"
        indexes = [models.Index(fields=["fk_legajo"])]

    def get_absolute_url(self):
        return reverse("dimensionlaboral_ver", kwargs={"pk": self.pk})


class LegajoAlertas(models.Model):
    """
    Registro de Alertas de vulnerabilidad asociadas a un Legajo determinado Tanto el alta como la baja se guardan en un historial del alertas.
    """

    fk_alerta = models.ForeignKey(
        Alertas, related_name="alerta", on_delete=models.CASCADE
    )
    fk_legajo = models.ForeignKey(
        Legajos, related_name="legajo_alerta", on_delete=models.CASCADE
    )
    fecha_inicio = models.DateField(auto_now=True)
    creada_por = models.ForeignKey(
        Usuarios,
        related_name="creada_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    observaciones = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return str(
            f"'fk_alerta': {self.fk_alerta}, 'fk_legajo': {self.fk_legajo}"
            f"'observaciones': {self.observaciones}, 'fecha_inicio': {self.fecha_inicio}, 'creada_por':{self.creada_por}",
        )

    class Meta:
        ordering = ["-fecha_inicio"]
        unique_together = ["fk_legajo", "fk_alerta"]
        verbose_name = "LegajoAlertas"
        verbose_name_plural = "LegajosAlertas"
        indexes = [
            models.Index(fields=["fk_alerta"]),
            models.Index(fields=["fk_legajo"]),
        ]

    def get_absolute_url(self):
        return reverse("legajoalertas_ver", kwargs={"pk": self.pk})


class HistorialLegajoAlertas(models.Model):
    """
    Guardado de historial de los distintos movimientos (CREACION/ELIMINACION)  de alertas de vulnerabilidad asociadas a un Legajo.
    Se graban a traves funciones detalladas en el archivo signals.py de esta app.
    """

    fk_alerta = models.ForeignKey(
        Alertas, related_name="hist_alerta", on_delete=models.CASCADE
    )
    fk_legajo = models.ForeignKey(
        Legajos, related_name="hist_legajo_alerta", on_delete=models.CASCADE
    )
    observaciones = models.CharField(max_length=255, null=True, blank=True)
    creada_por = models.ForeignKey(
        Usuarios,
        related_name="hist_creada_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    eliminada_por = models.ForeignKey(
        Usuarios,
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
        return str(self.fk_alerta.fk_categoria.dimension)

    # Método para calcular el estado (Activa o Inactiva) basado en la existencia de fecha_fin
    @property
    def estado(self):
        return "Activa" if self.fecha_fin is None else "Inactiva"

    class Meta:
        ordering = ["-fecha_inicio"]
        verbose_name = "HistorialLegajoAlertas"
        verbose_name_plural = "HistorialesLegajoAlertas"
        indexes = [models.Index(fields=["fk_legajo"])]


class LegajosDerivaciones(models.Model):
    """
    Registro de todas las derivaciones a programas que funcionen dentro del sistema.
    """

    fk_legajo = models.ForeignKey(Legajos, on_delete=models.CASCADE)
    fk_programa_solicitante = models.ForeignKey(
        Programas, related_name="programa_solicitante", on_delete=models.CASCADE
    )
    fk_programa = models.ForeignKey(
        Programas, related_name="programa_derivado", on_delete=models.CASCADE
    )
    fk_organismo = models.ForeignKey(
        Organismos, on_delete=models.CASCADE, null=True, blank=True
    )
    detalles = models.CharField(max_length=500, null=True, blank=True)
    fk_usuario = models.ForeignKey(User, on_delete=models.CASCADE)
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
    m2m_alertas = models.ManyToManyField(CategoriaAlertas, blank=True)
    archivos = models.FileField(upload_to="legajos/archivos", null=True, blank=True)
    motivo_rechazo = models.ForeignKey(
        Rechazo, on_delete=models.SET_NULL, null=True, blank=True
    )
    obs_rechazo = models.CharField(max_length=500, null=True, blank=True)
    fecha_rechazo = models.DateField(null=True, blank=True)
    fecha_creado = models.DateField(auto_now_add=True, null=True, blank=True)
    fecha_modificado = models.DateField(auto_now=True)

    def __str__(self):
        return self.fk_legajo.apellido + ", " + self.fk_legajo.nombre

    class Meta:
        ordering = ["-fecha_creado"]
        verbose_name = "LegajoDerivacion"
        verbose_name_plural = "LegajosDerivaciones"
        indexes = [models.Index(fields=["fk_legajo"]), models.Index(fields=["estado"])]

    def get_absolute_url(self):
        return reverse("legajosderivaciones_ver", kwargs={"pk": self.pk})


class LegajosArchivos(models.Model):
    """
    Archivos asociados a un legajo. En la view se separaran los archivos de imagen de los documentos (para mostrar los primeros enun carousel)
    """

    fk_legajo = models.ForeignKey(Legajos, on_delete=models.CASCADE)
    archivo = models.FileField(upload_to="legajos/archivos/")
    fecha = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=255)

    class Meta:
        indexes = [models.Index(fields=["fk_legajo"])]

    def __str__(self):
        return f"Archivo {self.id} del legajo {self.fk_legajo}"


class LegajoGrupoHogar(models.Model):
    """
    Guardado de las relaciones familiares de los vecinos y vecinas registrados,
    con una valoración que permita conocer el estado del vínculo desde la
    consideración de cada parte involucrada.
    """

    fk_legajo_1Hogar = models.ForeignKey(
        Legajos, on_delete=models.CASCADE, related_name="hogar_1"
    )
    fk_legajo_2Hogar = models.ForeignKey(
        Legajos, on_delete=models.CASCADE, related_name="hogar_2"
    )
    estado_relacion = models.ForeignKey(
        EstadoRelacion, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"Legajo: {self.fk_legajo_1Hogar} - Hogar: {self.fk_legajo_2Hogar}"

    class Meta:
        ordering = ["fk_legajo_2Hogar"]
        verbose_name = "LegajoGrupoHogarForm"
        verbose_name_plural = "LegajoGrupoHogarForm"
        indexes = [
            models.Index(fields=["fk_legajo_1Hogar"]),
            models.Index(fields=["fk_legajo_2Hogar"]),
        ]

    def get_absolute_url(self):
        return reverse("LegajoGrupoHogarForm_ver", kwargs={"pk": self.pk})


class TipoIntervencion(models.Model):
    """
    Guardado de los tipos de intervenciones realizadas a un legajo.
    """

    nombre = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nombre}"

    class Meta:
        verbose_name = "TipoIntervencion"
        verbose_name_plural = "TiposIntervencion"


class SubIntervencion(models.Model):
    """
    Guardado de las SubIntervencion realizadas a un legajo.
    """

    nombre = models.CharField(max_length=255)
    fk_subintervencion = models.ForeignKey(
        TipoIntervencion, on_delete=models.SET_NULL, default=1, null=True
    )

    def __str__(self):
        return f"{self.nombre}"

    class Meta:
        verbose_name = "SubIntervencion"
        verbose_name_plural = "SubIntervenciones"


class EstadosIntervencion(models.Model):
    """
    Guardado de los estados de las intervenciones realizadas a un legajo.
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


class Intervencion(models.Model):
    """
    Guardado de las intervenciones realizadas a un legajo.
    """

    fk_legajo = models.ForeignKey(Legajos, on_delete=models.SET_NULL, null=True)
    fk_usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fk_subintervencion = models.ForeignKey(
        SubIntervencion, on_delete=models.SET_NULL, null=True
    )
    fk_tipo_intervencion = models.ForeignKey(
        TipoIntervencion, on_delete=models.SET_NULL, null=True
    )
    fecha = models.DateTimeField(auto_now_add=True)
    fk_direccion = models.ManyToManyField(Direccion)
    fk_estado = models.ForeignKey(
        EstadosIntervencion, on_delete=models.SET_NULL, default=1, null=True
    )

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Intervencion"
        verbose_name_plural = "Intervenciones"
        indexes = [models.Index(fields=["fk_legajo"])]


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


class EstadosLlamados(models.Model):
    """
    Guardado de los estados de las intervenciones realizadas a un legajo.
    """

    nombre = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nombre}"

    class Meta:
        verbose_name = "EstadoLlamado"
        verbose_name_plural = "EstadosLlamados"


class TipoLlamado(models.Model):
    """
    Guardado de los tipos de llamados realizados a un legajo.
    """

    nombre = models.CharField(max_length=255)
    fk_programas_llamados = models.ForeignKey(
        ProgramasLlamados, on_delete=models.SET_NULL, null=True
    )

    def __str__(self):
        return f"{self.nombre}"

    class Meta:
        verbose_name = "TipoLlamado"
        verbose_name_plural = "TiposLammado"


class SubTipoLlamado(models.Model):
    """
    Guardado de los SubTipoLlamado realizados a un legajo.
    """

    def __str__(self):
        return f"{self.nombre}"

    nombre = models.CharField(max_length=255)
    fk_tipo_llamado = models.ForeignKey(
        TipoLlamado, on_delete=models.SET_NULL, default=1, null=True
    )

    class Meta:
        verbose_name = "SubTipoLlamado"
        verbose_name_plural = "SubTiposLlamado"


class Llamado(models.Model):
    """
    Guardado de los llamados realizados a un legajo.
    """

    fk_legajo = models.ForeignKey(Legajos, on_delete=models.SET_NULL, null=True)
    fk_usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fk_subtipollamado = models.ForeignKey(
        SubTipoLlamado, on_delete=models.SET_NULL, null=True
    )
    fk_tipo_llamado = models.ForeignKey(
        TipoLlamado, on_delete=models.SET_NULL, null=True
    )
    fecha = models.DateTimeField(auto_now_add=True)
    fk_estado = models.ForeignKey(
        EstadosLlamados, on_delete=models.SET_NULL, default=1, null=True
    )
    fk_programas_llamados = models.ForeignKey(
        ProgramasLlamados, on_delete=models.SET_NULL, null=True
    )

    observaciones = models.CharField(max_length=500)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Llamado"
        verbose_name_plural = "Llamados"
        indexes = [models.Index(fields=["fk_legajo"])]
