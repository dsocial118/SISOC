from django.conf import settings
from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class MontoPrestacionPrograma(models.Model):
    programa = models.CharField(
        max_length=255, verbose_name="Programa", blank=True, null=True
    )
    desayuno_valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor desayuno",
        blank=True,
        null=True,
    )
    almuerzo_valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor almuerzo",
        blank=True,
        null=True,
    )
    merienda_valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor merienda",
        blank=True,
        null=True,
    )
    cena_valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor cena",
        blank=True,
        null=True,
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de creación"
    )
    fecha_modificacion = models.DateTimeField(
        auto_now=True, verbose_name="Fecha de modificación"
    )
    usuario_creador = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    def __str__(self):
        return str(self.programa)

    class Meta:
        ordering = ["id"]
        verbose_name = "Prestación"
        verbose_name_plural = "Prestaciones"


class Nacionalidad(models.Model):
    nacionalidad = models.CharField(max_length=50)

    def __str__(self):
        return str(self.nacionalidad)

    class Meta:
        verbose_name = "Nacionalidad"
        verbose_name_plural = "Nacionalidades"


class Programa(models.Model):
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


class Provincia(models.Model):
    """
    Guardado de las provincias de los vecinos y vecinas registrados.
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        ordering = ["id"]
        verbose_name = "Provincia"
        verbose_name_plural = "Provincia"


class Mes(models.Model):

    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        ordering = ["id"]
        verbose_name = "Mes"
        verbose_name_plural = "Meses"


class Dia(models.Model):

    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        ordering = ["id"]
        verbose_name = "Dia"
        verbose_name_plural = "Dias"


class Turno(models.Model):

    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        ordering = ["id"]
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"


class Municipio(models.Model):
    """
    Guardado de los municipios de los vecinos y vecinas registrados.
    """

    nombre = models.CharField(max_length=255)
    provincia = models.ForeignKey(
        Provincia, on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return str(self.nombre)

    class Meta:
        ordering = ["id"]
        verbose_name = "Municipio"
        verbose_name_plural = "Municipio"
        unique_together = (
            "nombre",
            "provincia",
        )


class Localidad(models.Model):
    """
    Guardado de las localidades de los vecinos y vecinas registrados.
    """

    nombre = models.CharField(max_length=255)
    municipio = models.ForeignKey(
        Municipio, on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Localidad"
        verbose_name_plural = "Localidad"
        unique_together = (
            "nombre",
            "municipio",
        )


class Sexo(models.Model):
    sexo = models.CharField(max_length=10)

    def __str__(self):
        return str(self.sexo)

    class Meta:
        verbose_name = "Sexo"
        verbose_name_plural = "Sexos"


class FiltroFavorito(models.Model):
    """Filtro avanzado guardado por usuario y seccion."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="filtros_favoritos",
    )
    seccion = models.CharField(max_length=100)
    nombre = models.CharField(max_length=120)
    filtros = models.JSONField(default=dict)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fecha_creacion"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "seccion", "nombre"],
                name="unico_filtro_favorito_usuario_seccion_nombre",
            )
        ]

    def __str__(self):
        return f"{self.usuario_id} - {self.seccion} - {self.nombre}"


class PreferenciaColumnas(models.Model):
    """Preferencias de columnas por listado y usuario."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferencias_columnas",
    )
    listado = models.CharField(max_length=150)
    columnas = models.JSONField(default=list)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha_actualizacion"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "listado"],
                name="unica_preferencia_columnas_usuario_listado",
            )
        ]

    def __str__(self):
        return f"{self.usuario_id} - {self.listado}"
