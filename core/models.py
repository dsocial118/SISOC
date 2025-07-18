from django.db import models


class Provincia(models.Model):
    """
    Guardado de las provincias de los vecinos y vecinas registrados.
    """

    nombre = models.CharField(max_length=255)

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


class Prestacion(models.Model):
    """
    Modelo unificado para prestaciones de comedores.
    Reemplaza el modelo complejo de relevamientos con un diseño más limpio.
    """
    from comedores.models import Comedor

    comedor = models.ForeignKey(
        Comedor, on_delete=models.CASCADE, related_name="prestaciones"
    )
    dia = models.CharField(
        max_length=20,
        choices=[
            ("lunes", "Lunes"),
            ("martes", "Martes"),
            ("miercoles", "Miércoles"),
            ("jueves", "Jueves"),
            ("viernes", "Viernes"),
            ("sabado", "Sábado"),
            ("domingo", "Domingo"),
        ],
        verbose_name="Día de la semana",
    )
    desayuno = models.BooleanField(default=False, verbose_name="Desayuno")
    almuerzo = models.BooleanField(default=False, verbose_name="Almuerzo")
    merienda = models.BooleanField(default=False, verbose_name="Merienda")
    cena = models.BooleanField(default=False, verbose_name="Cena")
    merienda_reforzada = models.BooleanField(
        default=False, verbose_name="Merienda reforzada"
    )

    # Campos adicionales para cantidad (opcional - para migración desde relevamientos)
    desayuno_cantidad_actual = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Cantidad actual desayuno"
    )
    desayuno_cantidad_espera = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Cantidad esperada desayuno"
    )
    almuerzo_cantidad_actual = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Cantidad actual almuerzo"
    )
    almuerzo_cantidad_espera = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Cantidad esperada almuerzo"
    )
    merienda_cantidad_actual = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Cantidad actual merienda"
    )
    merienda_cantidad_espera = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Cantidad esperada merienda"
    )
    cena_cantidad_actual = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Cantidad actual cena"
    )
    cena_cantidad_espera = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Cantidad esperada cena"
    )
    merienda_reforzada_cantidad_actual = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Cantidad actual merienda reforzada"
    )
    merienda_reforzada_cantidad_espera = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Cantidad esperada merienda reforzada"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Prestación - {self.comedor.nombre} - {self.dia}"

    class Meta:
        verbose_name = "Prestación"
        verbose_name_plural = "Prestaciones"
        unique_together = ["comedor", "dia"]
        ordering = ["comedor", "dia"]
