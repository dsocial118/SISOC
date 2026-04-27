# pylint: disable=too-many-lines
from datetime import datetime

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.forms import ValidationError
from django.utils import timezone

from comedores.models import CategoriaComedor, Comedor, Referente, TipoDeComedor
from core.soft_delete import SoftDeleteModelMixin


def _nullable_char(max_length=255, **kwargs):
    return models.CharField(max_length=max_length, blank=True, null=True, **kwargs)


def _nullable_text(**kwargs):
    return models.TextField(blank=True, null=True, **kwargs)


def _nullable_bool(**kwargs):
    return models.BooleanField(blank=True, null=True, **kwargs)


def _nullable_positive_int(**kwargs):
    return models.PositiveIntegerField(blank=True, null=True, **kwargs)


def _scale_field(max_value):
    return models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(max_value)],
    )


class TipoInsumos(models.Model):
    """
    Opciones de tipos de insumos recibidos por un Comedor/Merendero
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de insumo recibido"
        verbose_name_plural = "Tipos de insumos recibidos"
        ordering = ["nombre"]


class TipoFrecuenciaInsumos(models.Model):
    """
    Opciones de frecuencias de insumos recibidos
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Frecuencia de insumos recibidos"
        verbose_name_plural = "Frecuencias de insumos recibidos"
        ordering = ["nombre"]


class TipoOtrosRecepcion(models.Model):
    """
    Opciones de otros tipos de insumos recibidos
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Otros tipos de insumos recibidos"
        verbose_name_plural = "Otros tipos de insumos recibidos"
        ordering = ["nombre"]


class TipoModuloBolsones(models.Model):
    """
    Opciones de frecuencias de entrega de bolsones
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Frecuencia de entrega de bolsones"
        verbose_name_plural = "Frecuencias de entrega de bolsones"
        ordering = ["nombre"]


class TipoFrecuenciaBolsones(models.Model):
    """
    Opciones de frecuencias de entrega de bolsones
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Frecuencia de entrega de bolsones"
        verbose_name_plural = "Frecuencias de entrega de bolsones"
        ordering = ["nombre"]


class TipoTecnologia(models.Model):
    """
    Opciones de tipos de tecnologia utilizada en un Comedor/Merendero
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de tecnologia"
        verbose_name_plural = "Tipos de tecnologia"
        ordering = ["nombre"]


class TipoAccesoComedor(models.Model):
    """
    Opciones de tipos de acceso al Comedor/Merendero
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de acceso al comedor"
        verbose_name_plural = "Tipos de acceso al comedor"
        ordering = ["nombre"]


class TipoDistanciaTransporte(models.Model):
    """
    Opciones de distancias de transporte al Comedor/Merendero
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Distancia de transporte"
        verbose_name_plural = "Distancias de transporte"
        ordering = ["nombre"]


class TipoAgua(models.Model):
    """
    Opciones de tipos de abastecimiento de agua de un Comedor/Merendero
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de abastecimiento de agua"
        verbose_name_plural = "Tipos de abastecimientos de agua"
        ordering = ["nombre"]


class TipoCombustible(models.Model):
    """
    Opciones de tipos de abastecimiento de combustible de un Comedor/Merendero
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de abastecimiento de combustible"
        verbose_name_plural = "Tipos de abastecimientos de combustible"
        ordering = ["nombre"]


class EspacioCocina(models.Model):
    """
    Informacion relacionada a la cocina y almacenamiento de alimentos
    """

    espacio_elaboracion_alimentos = models.BooleanField(
        default=False, blank=True, null=True
    )
    almacenamiento_alimentos_secos = models.BooleanField(
        default=False, blank=True, null=True
    )
    almacenamiento_alimentos_secos_otro = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="2.2.2.1 Si respondió 'No', especificar dónde almacenan",
    )
    heladera = models.BooleanField(default=False, blank=True, null=True)
    freezer = models.BooleanField(default=False, blank=True, null=True)
    recipiente_residuos_organicos = models.BooleanField(
        default=False, blank=True, null=True
    )
    recipiente_residuos_reciclables = models.BooleanField(
        default=False, blank=True, null=True
    )
    otros_residuos = models.BooleanField(default=False, blank=True, null=True)
    recipiente_otros_residuos = models.BooleanField(
        default=False, blank=True, null=True
    )
    abastecimiento_combustible = models.ManyToManyField(
        TipoCombustible,
        related_name="espacios",
        verbose_name="2.2.7 Para cocinar utiliza",
        blank=True,
    )
    abastecimiento_agua = models.ForeignKey(
        to=TipoAgua,
        on_delete=models.PROTECT,
        verbose_name="2.2.8 El abastecimiento del agua es con",
        blank=True,
        null=True,
    )
    abastecimiento_agua_otro = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="En caso de otro, especificar",
    )
    instalacion_electrica = models.BooleanField(default=False, blank=True, null=True)

    class Meta:
        verbose_name = "Espacio de cocina y almacenamiento de alimentos"
        verbose_name_plural = "Espacios de cocina y almacenamiento de alimentos"

    def __str__(self):
        return f"Cocina #{self.pk or 'sin id'}"


class TipoModalidadPrestacion(models.Model):
    """
    Opciones de modalidades de prestacion de un Comedor/Merendero
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de Modalidad de Prestación"
        verbose_name_plural = "Tipos de Modalidades de Prestación"
        ordering = ["nombre"]


class FuncionamientoPrestacion(models.Model):
    """
    Informacion relacionada al funcionamiento del Comedor/Merendero
    """

    modalidad_prestacion = models.ForeignKey(
        TipoModalidadPrestacion,
        on_delete=models.PROTECT,
        verbose_name="1.1.4 Modalidad de prestación",
        blank=True,
        null=True,
    )
    servicio_por_turnos = models.BooleanField(default=False)
    cantidad_turnos = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(3),
        ],
    )

    class Meta:
        verbose_name = "Funcionamiento de comedor"
        verbose_name_plural = "Funcionamientos de comedores"

    def __str__(self):
        modalidad = (
            self.modalidad_prestacion.nombre
            if self.modalidad_prestacion
            else "Sin modalidad"
        )
        turnos = self.cantidad_turnos if self.cantidad_turnos is not None else "-"
        return f"{modalidad} (turnos: {turnos})"


class FrecuenciaLimpieza(models.Model):
    """
    Opciones de frecuencias de limpieza de un Comedor/Merendero
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Frecuencia de limpieza"
        verbose_name_plural = "Frecuencias de limpieza"
        ordering = ["nombre"]


class TipoDesague(models.Model):
    """
    Opciones de tipos de desagues de hinodoro de un Comedor/Merendero
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de desague del hinodoro"
        verbose_name_plural = "Tipos de desagues del hinodoro"
        ordering = ["nombre"]


class TipoGestionQuejas(models.Model):
    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de gestion de quejas"
        verbose_name_plural = "Tipos de gestion de quejas"


class EspacioPrestacion(models.Model):
    """
    Informacion relacionada al espacio donde se brinda la prestacion del Comedor/Merendero
    """

    espacio_equipado = models.BooleanField(default=False, blank=True, null=True)
    tiene_ventilacion = models.BooleanField(default=False, blank=True, null=True)
    tiene_salida_emergencia = models.BooleanField(default=False, blank=True, null=True)
    salida_emergencia_senializada = models.BooleanField(
        default=False, blank=True, null=True
    )
    tiene_equipacion_incendio = models.BooleanField(
        default=False, blank=True, null=True
    )
    tiene_botiquin = models.BooleanField(default=False, blank=True, null=True)
    tiene_buena_iluminacion = models.BooleanField(default=False, blank=True, null=True)
    tiene_sanitarios = models.BooleanField(default=False, blank=True, null=True)
    desague_hinodoro = models.ForeignKey(
        to=TipoDesague,
        on_delete=models.PROTECT,
        verbose_name="2.3.9 Si la respuesta anterior es SI, el desagüe del inodoro es",
        blank=True,
        null=True,
    )
    gestion_quejas = models.ForeignKey(
        to=TipoGestionQuejas,
        on_delete=models.PROTECT,
        verbose_name=(
            "2.3.10 ¿El Comedor/Merendero cuenta con alguna forma de "
            "registro de los reclamos sobre la prestacion alimentaria"
        ),
        blank=True,
        null=True,
    )
    gestion_quejas_otro = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="En caso de otro, especificar",
    )
    informacion_quejas = models.BooleanField(default=False)
    frecuencia_limpieza = models.ForeignKey(
        to=FrecuenciaLimpieza,
        on_delete=models.PROTECT,
        verbose_name="2.4.1 ¿Con qué frecuencia se realiza la limpieza de las instalaciones?",
        blank=True,
        null=True,
    )
    frecuencia_limpieza_otro = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="2.4.2 Si eligió 'Otra frecuencia', especificar",
    )

    class Meta:
        verbose_name = "Espacio donde se brinda la prestacion del Comedor/Merendero"
        verbose_name_plural = (
            "Espacios donde se brinda la prestacion del Comedor/Merendero"
        )

    def __str__(self):
        return f"Espacio de prestación #{self.pk or 'sin id'}"


class TipoEspacio(models.Model):
    """
    Opciones de tipos de espacios fisicos para un Comedor/Merendero
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de espacio fisico"
        verbose_name_plural = "Tipos de espacios fisicos"
        ordering = ["nombre"]


class Espacio(models.Model):
    """
    Informacion relacionada al espacio fisico del Comedor/Merendero.
    Contiene la informacion de la cocina y la prestacion del Comedor/Merendero
    """

    tipo_espacio_fisico = models.ForeignKey(
        to=TipoEspacio,
        on_delete=models.PROTECT,
        verbose_name="2.1.1 ¿En qué tipo de espacio físico funciona el Comedor/Merendero?",
        blank=True,
        null=True,
    )
    espacio_fisico_otro = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="2.1.2 Si eligió 'Otro', especificar",
    )

    cocina = models.OneToOneField(
        to=EspacioCocina,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    prestacion = models.OneToOneField(
        to=EspacioPrestacion,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Espacio fisico de comedor"
        verbose_name_plural = "Espacios fisicos de comedores"

    def __str__(self):
        tipo = (
            self.tipo_espacio_fisico.nombre if self.tipo_espacio_fisico else "Sin tipo"
        )
        return f"Espacio ({tipo})"


class CantidadColaboradores(models.Model):
    """
    Opciones de cantidades de colaboradores de un Comedor/Merendero
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Cantidad de colaboradores"
        verbose_name_plural = "Cantidades de colaboradores"
        ordering = ["nombre"]


class Colaboradores(models.Model):
    """
    Informacion relacionada a las personas que realizan tareas en el Comedor/Merendero
    """

    cantidad_colaboradores = models.ForeignKey(
        to=CantidadColaboradores,
        on_delete=models.PROTECT,
        verbose_name="3.1.1 ¿Qué cantidad de personas realizan tareas en el Comedor / Merendero?",
        blank=True,
        null=True,
    )
    colaboradores_capacitados_alimentos = models.BooleanField(
        default=False,
        verbose_name="3.1.2 ¿El Comedor/Merendero cuentan con personas que realizan tareas capacitadas para la manipulación de alimentos?",
    )
    colaboradores_recibieron_capacitacion_alimentos = models.BooleanField(
        default=False, blank=True, null=True
    )
    colaboradores_capacitados_salud_seguridad = models.BooleanField(
        default=False, blank=True, null=True
    )
    colaboradores_recibieron_capacitacion_emergencias = models.BooleanField(
        default=False, blank=True, null=True
    )
    colaboradores_recibieron_capacitacion_violencia = models.BooleanField(
        default=False,
        blank=True,
        null=True,
        verbose_name=(
            "¿Los colaboradores recibieron capacitación sobre prevención de violencia de género "
            "incluyendo acoso sexual, explotación sexual y abuso infantil?"
        ),
    )

    def __str__(self):
        cantidad = (
            self.cantidad_colaboradores.nombre
            if self.cantidad_colaboradores
            else "Sin dato"
        )
        return f"Colaboradores: {cantidad}"


class FrecuenciaRecepcionRecursos(models.Model):
    """
    Opciones de frecuencias de recepcion de recursos para un Comedor/Merendero
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Frecuencia de recepcion de recursos"
        verbose_name_plural = "Frecuencias de recepcion de recursos"
        ordering = ["nombre"]


class TipoRecurso(models.Model):
    """
    Opciones de tipos de recursos recibidos por un Comedor/Merendero
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de recurso recibido"
        verbose_name_plural = "Tipos de recursos recibidos"
        ordering = ["nombre"]


class FuenteRecursos(models.Model):
    """
    Informacion relacionada a las fuentes de recursos del Comedor/Merendero
    """

    recibe_donaciones_particulares = models.BooleanField(default=False)
    frecuencia_donaciones_particulares = models.ForeignKey(
        to=FrecuenciaRecepcionRecursos,
        on_delete=models.PROTECT,
        verbose_name="4.1.8 Si recibe, ¿Con qué frecuencia recibe donaciones particulares?",
        related_name="frecuencia_donaciones_particulares",
        blank=True,
        null=True,
    )
    recursos_donaciones_particulares = models.ManyToManyField(
        TipoRecurso,
        related_name="fuentes_donaciones_particulares",
        verbose_name="4.1.9 ¿Qué tipo de recursos recibe de donaciones particulares?",
        blank=True,
    )

    recibe_estado_nacional = models.BooleanField(default=False)
    frecuencia_estado_nacional = models.ForeignKey(
        to=FrecuenciaRecepcionRecursos,
        on_delete=models.PROTECT,
        verbose_name="4.1.10 Si recibe, ¿Con qué frecuencia recibe del estado nacional?",
        related_name="frecuencia_estado_nacional",
        blank=True,
        null=True,
    )
    recursos_estado_nacional = models.ManyToManyField(
        TipoRecurso,
        related_name="fuentes_estado_nacional",
        verbose_name="4.1.11 ¿Qué tipo de recursos recibe del estado nacional?",
        blank=True,
    )

    recibe_estado_provincial = models.BooleanField(default=False)
    frecuencia_estado_provincial = models.ForeignKey(
        to=FrecuenciaRecepcionRecursos,
        on_delete=models.PROTECT,
        verbose_name="4.1.12 Si recibe, ¿Con qué frecuencia recibe del estado provincial?",
        related_name="frecuencia_estado_provincial",
        blank=True,
        null=True,
    )
    recursos_estado_provincial = models.ManyToManyField(
        TipoRecurso,
        related_name="fuentes_estado_provincial",
        verbose_name="4.1.13 ¿Qué tipo de recursos recibe del estado provincial?",
        blank=True,
    )

    recibe_estado_municipal = models.BooleanField(default=False)
    frecuencia_estado_municipal = models.ForeignKey(
        to=FrecuenciaRecepcionRecursos,
        on_delete=models.PROTECT,
        verbose_name="4.1.16Si recibe, ¿Con qué frecuencia recibe del estado municipal?",
        related_name="frecuencia_estado_municipal",
        blank=True,
        null=True,
    )
    recursos_estado_municipal = models.ManyToManyField(
        TipoRecurso,
        related_name="fuentes_estado_municipal",
        verbose_name="4.1.15 ¿Qué tipo de recursos recibe del estado municipal?",
        blank=True,
    )

    recibe_otros = models.BooleanField(default=False)
    frecuencia_otros = models.ForeignKey(
        to=FrecuenciaRecepcionRecursos,
        on_delete=models.PROTECT,
        verbose_name="4.1.18 Si recibe, ¿Con qué frecuencia recibe de otras fuentes?",
        related_name="frecuencia_otros",
        blank=True,
        null=True,
    )
    recursos_otros = models.ManyToManyField(
        TipoRecurso,
        related_name="fuentes_otros",
        verbose_name="4.1.19 ¿Qué tipo de recursos recibe de otras fuentes?",
        blank=True,
    )

    def clean(self) -> None:
        if self.recibe_donaciones_particulares and (
            not self.frecuencia_donaciones_particulares
            or not self.recursos_donaciones_particulares
        ):
            raise ValueError(
                "Si recibe donaciones particulares, debe completar la frecuencia y el tipo de recurso"
            )

        if self.recibe_estado_nacional and (
            not self.frecuencia_estado_nacional or not self.recursos_estado_nacional
        ):
            raise ValueError(
                "Si recibe del estado nacional, debe completar la frecuencia y el tipo de recurso"
            )

        if self.recibe_estado_provincial and (
            not self.frecuencia_estado_provincial or not self.recursos_estado_provincial
        ):
            raise ValueError(
                "Si recibe del estado provincial, debe completar la frecuencia y el tipo de recurso"
            )

        if self.recibe_estado_municipal and (
            not self.frecuencia_estado_municipal or not self.recursos_estado_municipal
        ):
            raise ValueError(
                "Si recibe del estado municipal, debe completar la frecuencia y el tipo de recurso"
            )

        if self.recibe_otros and (not self.frecuencia_otros or not self.recursos_otros):
            raise ValueError(
                "Si recibe otros recursos, debe completar la frecuencia y el tipo de recurso"
            )

        return super().clean()

    class Meta:
        verbose_name = "Fuente de recursos"
        verbose_name_plural = "Fuentes de recursos"

    def __str__(self):
        return f"Recursos #{self.pk or 'sin id'}"


class FuenteCompras(models.Model):
    """
    Informacion relacionada a la realizacion de compras para abastecer el Comedor/Merendero
    """

    almacen_cercano = models.BooleanField(default=False, blank=True, null=True)
    verduleria = models.BooleanField(default=False, blank=True, null=True)
    granja = models.BooleanField(default=False, blank=True, null=True)
    carniceria = models.BooleanField(default=False, blank=True, null=True)
    pescaderia = models.BooleanField(default=False, blank=True, null=True)
    supermercado = models.BooleanField(default=False, blank=True, null=True)
    mercado_central = models.BooleanField(default=False, blank=True, null=True)
    ferias_comunales = models.BooleanField(default=False, blank=True, null=True)
    mayoristas = models.BooleanField(default=False, blank=True, null=True)
    otro = models.BooleanField(default=False, blank=True, null=True)

    class Meta:
        verbose_name = "Fuente de compras"
        verbose_name_plural = "Fuentes de compras"

    def __str__(self):
        return f"Compras #{self.pk or 'sin id'}"


class Prestacion(models.Model):
    """
    Modelo que representa una prestación brindada en un Comedor/Merendero.
    """

    # TODO: Esto tiene que se refactorizado, pero se como hacer los formularios :p
    lunes_desayuno_actual = models.PositiveIntegerField(null=True, blank=True)
    lunes_desayuno_espera = models.PositiveIntegerField(null=True, blank=True)
    lunes_almuerzo_actual = models.PositiveIntegerField(null=True, blank=True)
    lunes_almuerzo_espera = models.PositiveIntegerField(null=True, blank=True)
    lunes_merienda_actual = models.PositiveIntegerField(null=True, blank=True)
    lunes_merienda_reforzada_actual = models.PositiveIntegerField(null=True, blank=True)
    lunes_merienda_espera = models.PositiveIntegerField(null=True, blank=True)
    lunes_merienda_reforzada_espera = models.PositiveIntegerField(null=True, blank=True)
    lunes_cena_actual = models.PositiveIntegerField(null=True, blank=True)
    lunes_cena_espera = models.PositiveIntegerField(null=True, blank=True)

    martes_desayuno_actual = models.PositiveIntegerField(null=True, blank=True)
    martes_desayuno_espera = models.PositiveIntegerField(null=True, blank=True)
    martes_almuerzo_actual = models.PositiveIntegerField(null=True, blank=True)
    martes_almuerzo_espera = models.PositiveIntegerField(null=True, blank=True)
    martes_merienda_actual = models.PositiveIntegerField(null=True, blank=True)
    martes_merienda_reforzada_actual = models.PositiveIntegerField(
        null=True, blank=True
    )
    martes_merienda_espera = models.PositiveIntegerField(null=True, blank=True)
    martes_merienda_reforzada_espera = models.PositiveIntegerField(
        null=True, blank=True
    )
    martes_cena_actual = models.PositiveIntegerField(null=True, blank=True)
    martes_cena_espera = models.PositiveIntegerField(null=True, blank=True)

    miercoles_desayuno_actual = models.PositiveIntegerField(null=True, blank=True)
    miercoles_desayuno_espera = models.PositiveIntegerField(null=True, blank=True)
    miercoles_almuerzo_actual = models.PositiveIntegerField(null=True, blank=True)
    miercoles_almuerzo_espera = models.PositiveIntegerField(null=True, blank=True)
    miercoles_merienda_actual = models.PositiveIntegerField(null=True, blank=True)
    miercoles_merienda_reforzada_actual = models.PositiveIntegerField(
        null=True, blank=True
    )
    miercoles_merienda_espera = models.PositiveIntegerField(null=True, blank=True)
    miercoles_merienda_reforzada_espera = models.PositiveIntegerField(
        null=True, blank=True
    )
    miercoles_cena_actual = models.PositiveIntegerField(null=True, blank=True)
    miercoles_cena_espera = models.PositiveIntegerField(null=True, blank=True)

    jueves_desayuno_actual = models.PositiveIntegerField(null=True, blank=True)
    jueves_desayuno_espera = models.PositiveIntegerField(null=True, blank=True)
    jueves_almuerzo_actual = models.PositiveIntegerField(null=True, blank=True)
    jueves_almuerzo_espera = models.PositiveIntegerField(null=True, blank=True)
    jueves_merienda_actual = models.PositiveIntegerField(null=True, blank=True)
    jueves_merienda_reforzada_actual = models.PositiveIntegerField(
        null=True, blank=True
    )
    jueves_merienda_espera = models.PositiveIntegerField(null=True, blank=True)
    jueves_merienda_reforzada_espera = models.PositiveIntegerField(
        null=True, blank=True
    )
    jueves_cena_actual = models.PositiveIntegerField(null=True, blank=True)
    jueves_cena_espera = models.PositiveIntegerField(null=True, blank=True)

    viernes_desayuno_actual = models.PositiveIntegerField(null=True, blank=True)
    viernes_desayuno_espera = models.PositiveIntegerField(null=True, blank=True)
    viernes_almuerzo_actual = models.PositiveIntegerField(null=True, blank=True)
    viernes_almuerzo_espera = models.PositiveIntegerField(null=True, blank=True)
    viernes_merienda_actual = models.PositiveIntegerField(null=True, blank=True)
    viernes_merienda_reforzada_actual = models.PositiveIntegerField(
        null=True, blank=True
    )
    viernes_merienda_espera = models.PositiveIntegerField(null=True, blank=True)
    viernes_merienda_reforzada_espera = models.PositiveIntegerField(
        null=True, blank=True
    )
    viernes_cena_actual = models.PositiveIntegerField(null=True, blank=True)
    viernes_cena_espera = models.PositiveIntegerField(null=True, blank=True)

    sabado_desayuno_actual = models.PositiveIntegerField(null=True, blank=True)
    sabado_desayuno_espera = models.PositiveIntegerField(null=True, blank=True)
    sabado_almuerzo_actual = models.PositiveIntegerField(null=True, blank=True)
    sabado_almuerzo_espera = models.PositiveIntegerField(null=True, blank=True)
    sabado_merienda_actual = models.PositiveIntegerField(null=True, blank=True)
    sabado_merienda_reforzada_actual = models.PositiveIntegerField(
        null=True, blank=True
    )
    sabado_merienda_espera = models.PositiveIntegerField(null=True, blank=True)
    sabado_merienda_reforzada_espera = models.PositiveIntegerField(
        null=True, blank=True
    )
    sabado_cena_actual = models.PositiveIntegerField(null=True, blank=True)
    sabado_cena_espera = models.PositiveIntegerField(null=True, blank=True)

    domingo_desayuno_actual = models.PositiveIntegerField(null=True, blank=True)
    domingo_desayuno_espera = models.PositiveIntegerField(null=True, blank=True)
    domingo_almuerzo_actual = models.PositiveIntegerField(null=True, blank=True)
    domingo_almuerzo_espera = models.PositiveIntegerField(null=True, blank=True)
    domingo_merienda_actual = models.PositiveIntegerField(null=True, blank=True)
    domingo_merienda_reforzada_actual = models.PositiveIntegerField(
        null=True, blank=True
    )
    domingo_merienda_espera = models.PositiveIntegerField(null=True, blank=True)
    domingo_merienda_reforzada_espera = models.PositiveIntegerField(
        null=True, blank=True
    )
    domingo_cena_actual = models.PositiveIntegerField(null=True, blank=True)
    domingo_cena_espera = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Prestacion"
        verbose_name_plural = "Prestaciones"

    def __str__(self):
        return f"Prestación #{self.pk or 'sin id'}"


class Anexo(models.Model):
    """
    Informacion relacionada a los anexos de un Comedor/Merendero
    """

    tipo_insumo = models.ForeignKey(
        to=TipoInsumos,
        on_delete=models.PROTECT,
        verbose_name="¿Qué tipo de insumo recibió?",
        blank=True,
        null=True,
    )
    frecuencia_insumo = models.ForeignKey(
        to=TipoFrecuenciaInsumos,
        on_delete=models.PROTECT,
        verbose_name="¿Con qué frecuencia recibió estos insumos?",
        blank=True,
        null=True,
    )
    tecnologia = models.ForeignKey(
        to=TipoTecnologia,
        on_delete=models.PROTECT,
        verbose_name="¿El espacio comunitario cuenta con?",
        blank=True,
        null=True,
    )
    acceso_comedor = models.ForeignKey(
        to=TipoAccesoComedor,
        on_delete=models.PROTECT,
        verbose_name="Al comedor se accede por...",
        blank=True,
        null=True,
    )
    distancia_transporte = models.ForeignKey(
        to=TipoDistanciaTransporte,
        on_delete=models.PROTECT,
        verbose_name="¿Qué distancia hay desde el comedor al transporte público más cercano?",
        blank=True,
        null=True,
    )
    comedor_merendero = models.BooleanField(default=False, blank=True, null=True)
    insumos_organizacion = models.BooleanField(default=False, blank=True, null=True)
    servicio_internet = models.BooleanField(default=False, null=True, blank=True)
    zona_inundable = models.BooleanField(default=False, blank=True, null=True)
    actividades_jardin_maternal = models.BooleanField(
        default=False, blank=True, null=True
    )
    actividades_jardin_infantes = models.BooleanField(
        default=False, blank=True, null=True
    )
    apoyo_escolar = models.BooleanField(default=False, blank=True, null=True)
    alfabetizacion_terminalidad = models.BooleanField(
        default=False, blank=True, null=True
    )
    capacitaciones_talleres = models.BooleanField(default=False, blank=True, null=True)
    promocion_salud = models.BooleanField(default=False, blank=True, null=True)
    actividades_discapacidad = models.BooleanField(default=False, blank=True, null=True)
    necesidades_alimentarias = models.BooleanField(default=False, blank=True, null=True)
    actividades_recreativas = models.BooleanField(default=False, blank=True, null=True)
    actividades_culturales = models.BooleanField(default=False, blank=True, null=True)
    emprendimientos_productivos = models.BooleanField(
        default=False, blank=True, null=True
    )
    actividades_religiosas = models.BooleanField(default=False, blank=True, null=True)
    actividades_huerta = models.BooleanField(default=False, blank=True, null=True)
    espacio_huerta = models.BooleanField(default=False, blank=True, null=True)
    otras_actividades = models.BooleanField(default=False, blank=True, null=True)
    cuales_otras_actividades = models.TextField(blank=True, null=True)
    veces_recibio_insumos_2024 = models.IntegerField(
        default=0,
        verbose_name="¿Cuántas veces recibió estos insumos en el año 2024?",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Anexo"
        verbose_name_plural = "Anexos"

    def __str__(self):
        insumo = self.tipo_insumo.nombre if self.tipo_insumo else "Sin insumo"
        return f"Anexo ({insumo})"


class MotivoExcepcion(models.Model):
    """
    Opciones de motivos de excepcion para los relevmaientos
    """

    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Motivo de excepcion"
        verbose_name_plural = "Motivos de excepcion"


class Excepcion(models.Model):

    motivo = models.ForeignKey(
        MotivoExcepcion, on_delete=models.PROTECT, blank=True, null=True
    )
    descripcion = models.TextField(blank=True, null=True)
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
    adjuntos = models.JSONField(default=list, blank=True, null=True)
    firma = models.CharField(max_length=600, blank=True, null=True)

    class Meta:
        verbose_name = "Excepcion de comedor"
        verbose_name_plural = "Excepciones de comedor"

    def __str__(self):
        motivo = self.motivo.nombre if self.motivo else "Sin motivo"
        return f"Excepción: {motivo}"


class PuntoEntregas(models.Model):
    tipo_comedor = models.ForeignKey(
        to=TipoDeComedor,
        on_delete=models.PROTECT,
        verbose_name="Tipo de comedor",
        blank=True,
        null=True,
    )
    reciben_otros_recepcion = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Otros",
    )
    frecuencia_recepcion_mercaderias = models.ManyToManyField(
        TipoFrecuenciaBolsones,
        related_name="frecuencia_recepcion_mercaderias",
        verbose_name="frecuencia de recepcion de mercaderias",
        blank=True,
    )
    frecuencia_entrega_bolsones = models.ForeignKey(
        to=TipoFrecuenciaBolsones,
        on_delete=models.PROTECT,
        verbose_name="Frecuencia de entrega de bolsones",
        blank=True,
        null=True,
    )
    tipo_modulo_bolsones = models.ForeignKey(
        to=TipoModuloBolsones,
        on_delete=models.PROTECT,
        verbose_name="Tipo de modulo de bolsones",
        blank=True,
        null=True,
    )
    otros_punto_entregas = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Otros punto de entrega",
    )
    existe_punto_entregas = models.BooleanField(default=False, blank=True, null=True)
    funciona_punto_entregas = models.BooleanField(default=False, blank=True, null=True)
    observa_entregas = models.BooleanField(default=False, blank=True, null=True)
    retiran_mercaderias_distribucion = models.BooleanField(
        default=False, blank=True, null=True
    )
    retiran_mercaderias_comercio = models.BooleanField(
        default=False, blank=True, null=True
    )
    reciben_dinero = models.BooleanField(default=False, blank=True, null=True)
    registran_entrega_bolsones = models.BooleanField(
        default=False, blank=True, null=True
    )

    def __str__(self):
        tipo = self.tipo_comedor.nombre if self.tipo_comedor else "Sin tipo"
        return f"Punto de entregas ({tipo})"


class Relevamiento(SoftDeleteModelMixin, models.Model):

    estado = models.CharField(max_length=255, blank=True, null=True)
    comedor = models.ForeignKey(
        to=Comedor,
        on_delete=models.CASCADE,
    )
    fecha_visita = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    territorial_nombre = models.CharField(max_length=255, blank=True, null=True)
    territorial_uid = models.CharField(max_length=255, blank=True, null=True)
    funcionamiento = models.OneToOneField(
        to=FuncionamientoPrestacion, on_delete=models.PROTECT, blank=True, null=True
    )
    espacio = models.OneToOneField(
        to=Espacio, on_delete=models.PROTECT, blank=True, null=True
    )
    colaboradores = models.OneToOneField(
        to=Colaboradores, on_delete=models.PROTECT, blank=True, null=True
    )
    recursos = models.OneToOneField(
        to=FuenteRecursos, on_delete=models.PROTECT, blank=True, null=True
    )
    compras = models.OneToOneField(
        to=FuenteCompras, on_delete=models.PROTECT, blank=True, null=True
    )
    prestacion = models.OneToOneField(
        to=Prestacion, on_delete=models.PROTECT, blank=True, null=True
    )
    observacion = models.TextField(blank=True, null=True)
    docPDF = models.URLField(blank=True, null=True)
    responsable_es_referente = models.BooleanField(default=True, blank=True, null=True)
    responsable_relevamiento = models.ForeignKey(
        to=Referente,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="responsable_relevamientos",
    )
    anexo = models.OneToOneField(
        to=Anexo, on_delete=models.PROTECT, blank=True, null=True
    )
    excepcion = models.OneToOneField(
        to=Excepcion, on_delete=models.PROTECT, blank=True, null=True
    )
    imagenes = models.JSONField(default=list, blank=True, null=True)
    punto_entregas = models.OneToOneField(
        to=PuntoEntregas, on_delete=models.PROTECT, blank=True, null=True
    )

    def save(self, *args, **kwargs):
        self.validate_relevamientos_activos()
        self.set_referente_como_responsable()

        super().save(*args, **kwargs)

    def set_referente_como_responsable(self):
        """
        Si el responsable es el referente del comedor, sincronizar el campo
        ``responsable_relevamiento`` con el referente actual.
        """
        if self.responsable_es_referente and self.comedor and self.comedor.referente:
            self.responsable_relevamiento = self.comedor.referente

    def validate_relevamientos_activos(self):
        if self.estado in ["Pendiente", "Visita pendiente"]:
            relevamiento_existente = (
                Relevamiento.objects.filter(
                    comedor=self.comedor, estado__in=["Pendiente", "Visita pendiente"]
                )
                .exclude(pk=self.pk)
                .exists()
            )

            if relevamiento_existente:
                raise ValidationError(
                    f"Ya existe un relevamiento activo para el comedor '{self.comedor}'."
                )

    class Meta:
        indexes = [
            models.Index(fields=["comedor"]),
        ]
        unique_together = [["comedor", "fecha_visita"]]
        verbose_name = "Relevamiento"
        verbose_name_plural = "Relevamientos"

    def __str__(self):
        comedor = self.comedor.nombre if self.comedor else "Comedor sin nombre"
        fecha = (
            self.fecha_visita.date()
            if isinstance(self.fecha_visita, datetime)
            else self.fecha_visita
        )
        fecha_text = (
            fecha.strftime("%Y-%m-%d") if hasattr(fecha, "strftime") else "sin fecha"
        )
        return f"Relevamiento {fecha_text} - {comedor}"


class FuncionamientoSeguimiento(models.Model):
    ABIERTO_FUNCIONANDO = "Abierto en funcionamiento"
    ABIERTO_SIN_FUNCIONAR = "Abierto sin funcionamiento"
    CERRADO = "Cerrado"
    FUNCIONAMIENTO_CHOICES = [
        (ABIERTO_FUNCIONANDO, ABIERTO_FUNCIONANDO),
        (ABIERTO_SIN_FUNCIONAR, ABIERTO_SIN_FUNCIONAR),
        (CERRADO, CERRADO),
    ]

    funcionamiento = _nullable_char(choices=FUNCIONAMIENTO_CHOICES)

    class Meta:
        verbose_name = "Funcionamiento de primer seguimiento"
        verbose_name_plural = "Funcionamientos de primer seguimiento"

    def __str__(self):
        return self.funcionamiento or "Sin funcionamiento"


class ServiciosBasicosSeguimiento(models.Model):
    agua_potable = _nullable_bool()
    gas_red = _scale_field(4)
    gas_envasado = _scale_field(4)
    electricidad = _scale_field(4)
    lenia_carbon = _scale_field(4)
    otros_cocina = _nullable_char()
    banio = _nullable_char()
    recipiente = _nullable_char()
    otro_recipiente = _nullable_char()
    observan_animales = _nullable_bool()
    elementos_guardados = _nullable_bool()

    class Meta:
        verbose_name = "Servicios basicos de primer seguimiento"
        verbose_name_plural = "Servicios basicos de primer seguimiento"

    def __str__(self):
        return f"Servicios basicos seguimiento #{self.pk or 'sin id'}"


class AlmacenamientoAlimentosSeguimiento(models.Model):
    alimentos_secos_cerrados = _scale_field(4)
    alimentos_secos_cerrados_adecuados = _scale_field(4)
    alimentos_secos_desparramados = _scale_field(4)
    alimentos_secos_noseobservan = _scale_field(4)
    otros_alimentos_secos = _nullable_char()
    heladera_existe = _nullable_bool()
    freezer_existe = _nullable_bool()
    almacenado_cerrados_heladera = _scale_field(11)
    almacenado_cerrados_freezer = _scale_field(11)
    almacenado_cerradoscondiciones_heladera = _scale_field(11)
    almacenado_cerradoscondiciones_freezer = _scale_field(11)
    almacenado_desparramados_heladera = _scale_field(11)
    almacenado_desparramados_freezer = _scale_field(11)
    almacenado_etiquetados_heladera = _scale_field(11)
    almacenado_etiquetados_freezer = _scale_field(11)
    almacenado_noseobservan_heladera = _scale_field(11)
    almacenado_noseobservan_freezer = _scale_field(11)
    almacenado_otro = _nullable_char()

    class Meta:
        verbose_name = "Almacenamiento de alimentos de primer seguimiento"
        verbose_name_plural = "Almacenamientos de alimentos de primer seguimiento"

    def __str__(self):
        return f"Almacenamiento seguimiento #{self.pk or 'sin id'}"


class CondicionesHigieneSeguimiento(models.Model):
    ADECUADA = "Adecuada"
    MEDIANAMENTE_ADECUADA = "Medianamente adecuada"
    INADECUADA = "Inadecuada"
    HIGIENE_CHOICES = [
        (ADECUADA, ADECUADA),
        (MEDIANAMENTE_ADECUADA, MEDIANAMENTE_ADECUADA),
        (INADECUADA, INADECUADA),
    ]

    condiciones_piso_limpieza = _nullable_char(choices=HIGIENE_CHOICES)
    condiciones_piso_orden = _nullable_char(choices=HIGIENE_CHOICES)
    condiciones_mesada_limpieza = _nullable_char(choices=HIGIENE_CHOICES)
    condiciones_mesada_orden = _nullable_char(choices=HIGIENE_CHOICES)
    condiciones_mesas_limpieza = _nullable_char(choices=HIGIENE_CHOICES)
    condiciones_mesas_orden = _nullable_char(choices=HIGIENE_CHOICES)
    condiciones_bacha_limpieza = _nullable_char(choices=HIGIENE_CHOICES)
    condiciones_bachas_orden = _nullable_char(choices=HIGIENE_CHOICES)
    condiciones_equipamiento_limpieza = _nullable_char(choices=HIGIENE_CHOICES)
    condiciones_equipamiento_orden = _nullable_char(choices=HIGIENE_CHOICES)
    condiciones_utensillos_limpieza = _nullable_char(choices=HIGIENE_CHOICES)
    condiciones_utensillos_orden = _nullable_char(choices=HIGIENE_CHOICES)
    entregan_viandas = _nullable_char(choices=HIGIENE_CHOICES)

    class Meta:
        verbose_name = "Condiciones de higiene de primer seguimiento"
        verbose_name_plural = "Condiciones de higiene de primer seguimiento"

    def __str__(self):
        return f"Higiene seguimiento #{self.pk or 'sin id'}"


class TareasComedorSeguimiento(models.Model):
    tareas_comedor_cant_personas = models.ForeignKey(
        to=CantidadColaboradores,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    tareas_capacitacion = _nullable_char()
    tareas_capacitacion_especificar = _nullable_char()

    class Meta:
        verbose_name = "Tareas de comedor de primer seguimiento"
        verbose_name_plural = "Tareas de comedor de primer seguimiento"

    def __str__(self):
        return f"Tareas seguimiento #{self.pk or 'sin id'}"


class RecursosSeguimiento(models.Model):
    fuente_recursos = models.OneToOneField(
        to=FuenteRecursos,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    recursos_comedor_estado_nacional = _nullable_bool()
    recursos_comedor_estado_nacional_frecuencia = _nullable_char()
    recursos_comedor_estado_nacional_recibe = _nullable_char()
    recursos_comedor_estado_provincial = _nullable_bool()
    recursos_comedor_estado_provincial_frecuencia = _nullable_char()
    recursos_comedor_estado_provincial_recibe = _nullable_char()
    recursos_comedor_estado_municipal = _nullable_bool()
    recursos_comedor_estado_municipal_frecuencia = _nullable_char()
    recursos_comedor_estado_municipal_recibe = _nullable_char()
    recursos_comedor_donaciones = _nullable_bool()
    recursos_comedor_donaciones_frecuencia = _nullable_char()
    recursos_comedor_donaciones_recibe = _nullable_char()
    financiamiento_principal = _nullable_char()
    financiamiento_principal_otros = _nullable_char()
    financiaminento_otras_necesidades = _nullable_bool()
    financiaminento_otras_necesidades_paraque = _nullable_char()
    financiaminento_otras_necesidades_frecuencia = _nullable_char()

    class Meta:
        verbose_name = "Recursos de primer seguimiento"
        verbose_name_plural = "Recursos de primer seguimiento"

    def __str__(self):
        return f"Recursos seguimiento #{self.pk or 'sin id'}"


class ComprasSeguimiento(models.Model):
    fuente_compras = models.OneToOneField(
        to=FuenteCompras,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    lugares_compra = _nullable_char()
    lugares_compra_otros = _nullable_char()
    frecuencia_compras = _nullable_char()
    otra_frecuencia_compras = _nullable_char()
    quien_realiza_compras = _nullable_char()
    quien_realiza_compras_otro = _nullable_char()
    elije_alimentos_compra = _nullable_char(
        choices=[("Siempre", "Siempre"), ("A veces", "A veces"), ("Nunca", "Nunca")]
    )

    class Meta:
        verbose_name = "Compras de primer seguimiento"
        verbose_name_plural = "Compras de primer seguimiento"

    def __str__(self):
        return f"Compras seguimiento #{self.pk or 'sin id'}"


class FrecuenciaCompraAlimentosSeguimiento(models.Model):
    frecuencia_compra_hortalizas_frutas = _nullable_char()
    frecuencia_compra_leche_yogur_queso = _nullable_char()
    frecuencia_compra_carnes = _nullable_char()
    frecuencia_compra_legumbres = _nullable_char()
    frecuencia_compra_alimentos_secos = _nullable_char()
    frecuencia_compra_pan = _nullable_char()
    frecuencia_compra_huevos = _nullable_char()
    frecuencia_compra_otros = _nullable_char()

    class Meta:
        verbose_name = "Frecuencia de compra de alimentos de primer seguimiento"
        verbose_name_plural = "Frecuencias de compra de alimentos de primer seguimiento"

    def __str__(self):
        return f"Frecuencia compra seguimiento #{self.pk or 'sin id'}"


class MenuSeguimiento(models.Model):
    id_menu = _nullable_char(unique=True)
    tipo_prestacion = _nullable_char()
    cantidad_personas_menu = _nullable_positive_int()
    cambios_menu = _nullable_bool()
    cambios_cuales = _nullable_char()
    cambios_porque = _nullable_char()
    menu_semana_pasada_lunes = _nullable_char()
    menu_semana_pasada_martes = _nullable_char()
    menu_semana_pasada_miercoles = _nullable_char()
    menu_semana_pasada_jueves = _nullable_char()
    menu_semana_pasada_viernes = _nullable_char()
    menu_semana_pasada_sabado = _nullable_char()
    menu_semana_pasada_domingo = _nullable_char()
    menu_preestablecido = _nullable_bool()
    menu_preestablecido_porquien = _nullable_char()
    frecuencia_menu_preestablecido = _nullable_char()
    menu_preestablecido_porque = _nullable_char()
    modalidad_prestacion_del_dia = models.ForeignKey(
        to=TipoModalidadPrestacion,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    considera_menu_variado = _nullable_bool()
    considera_menu_saludable = _nullable_bool()
    considera_menu_porque = _nullable_char()
    considera_menu_tamanio_porciones = _nullable_bool()
    considera_personas_conformes = _nullable_bool()
    considera_personas_conformes_porque = _nullable_char()
    mejora_alimentacion_ofrecida = _nullable_bool()

    class Meta:
        verbose_name = "Menu de primer seguimiento"
        verbose_name_plural = "Menus de primer seguimiento"

    def __str__(self):
        return self.id_menu or f"Menu seguimiento #{self.pk or 'sin id'}"


class RegistroAsistenciaSeguimiento(models.Model):
    registro_asistencia = _nullable_bool()
    registro_asistencia_quien = _nullable_char()
    registro_asistencia_metodo = _nullable_char()
    asisten_personas_calle = _nullable_bool()
    asisten_personas_calle_cantidad = _nullable_positive_int()
    cantidad_asistencia_total = _nullable_positive_int()

    class Meta:
        verbose_name = "Registro de asistencia de primer seguimiento"
        verbose_name_plural = "Registros de asistencia de primer seguimiento"

    def __str__(self):
        return f"Registro asistencia seguimiento #{self.pk or 'sin id'}"


class FrecuenciaAlimentosSeguimiento(models.Model):
    frecuencia_alimentos_alm_cena_frutas = _nullable_char()
    frecuencia_alimentos_alm_cena_verduras = _nullable_char()
    frecuencia_alimentos_alm_cena_carne = _nullable_char()
    frecuencia_alimentos_alm_cena_pollo = _nullable_char()
    frecuencia_alimentos_alm_cena_pescado = _nullable_char()
    frecuencia_alimentos_alm_cena_fideos = _nullable_char()
    frecuencia_alimentos_alm_cena_legumbres = _nullable_char()
    frecuencia_alimentos_alm_cena_ultraprocesados = _nullable_char()
    frecuencia_alimentos_alm_cena_huevos = _nullable_char()
    frecuencia_alimentos_des_merienda_leche = _nullable_char()
    frecuencia_alimentos_des_merienda_te = _nullable_char()
    frecuencia_alimentos_des_merienda_mate_cocido = _nullable_char()
    frecuencia_alimentos_des_merienda_yogurt = _nullable_char()
    frecuencia_alimentos_des_merienda_queso = _nullable_char()
    frecuencia_alimentos_des_merienda_fruta = _nullable_char()
    frecuencia_alimentos_des_merienda_pan = _nullable_char()
    frecuencia_alimentos_des_merienda_galletitas = _nullable_char()
    frecuencia_alimentos_des_merienda_mermelada_dulce = _nullable_char()

    class Meta:
        verbose_name = "Frecuencia de alimentos de primer seguimiento"
        verbose_name_plural = "Frecuencias de alimentos de primer seguimiento"

    def __str__(self):
        return f"Frecuencia alimentos seguimiento #{self.pk or 'sin id'}"


class ActividadesExtrasSeguimiento(models.Model):
    id_actividad = _nullable_char(unique=True)
    talleres_recreativos = _nullable_bool()
    talleres_recreativos_donde = _nullable_char()
    talleres_recreativos_frecuencia = _nullable_char()
    apoyo_educativo = _nullable_bool()
    apoyo_educativo_donde = _nullable_char()
    apoyo_educativo_frecuencia = _nullable_char()
    grupos_contencion = _nullable_bool()
    grupos_contencion_donde = _nullable_char()
    grupos_contencion_frecuencia = _nullable_char()
    actividades_deportivas = _nullable_bool()
    actividades_deportivas_donde = _nullable_char()
    actividades_deportivas_frecuencia = _nullable_char()
    talleres_oficio = _nullable_bool()
    talleres_oficio_donde = _nullable_char()
    talleres_oficio_frecuencia = _nullable_char()
    huerta = _nullable_bool()
    huerta_donde = _nullable_char()
    huerta_frecuencia = _nullable_char()
    actividades_culturales = _nullable_bool()
    actividades_culturales_donde = _nullable_char()
    actividades_culturales_frecuencia = _nullable_char()
    actividades_religiosas = _nullable_bool()
    actividades_religiosas_donde = _nullable_char()
    actividades_religiosas_frecuencia = _nullable_char()
    actividades_discapacidad = _nullable_bool()
    actividades_discapacidad_donde = _nullable_char()
    actividades_discapacidad_frecuencia = _nullable_char()
    ayuda_tramites = _nullable_bool()
    ayuda_tramites_donde = _nullable_char()
    ayuda_tramites_frecuencia = _nullable_char()
    servicios_legales = _nullable_bool()
    servicios_legales_donde = _nullable_char()
    servicios_legales_frecuencia = _nullable_char()
    terminalidad_educativa = _nullable_bool()
    terminalidad_educativa_donde = _nullable_char()
    terminalidad_educativa_frecuencia = _nullable_char()
    emprendimientos_productivos = _nullable_bool()
    emprendimientos_productivos_donde = _nullable_char()
    emprendimientos_productivos_frecuencia = _nullable_char()
    promocion_salud = _nullable_bool()
    promocion_salud_donde = _nullable_char()
    promocion_salud_frecuencia = _nullable_char()
    otro = _nullable_bool()
    otro_donde = _nullable_char()
    otro_frecuencia = _nullable_char()

    class Meta:
        verbose_name = "Actividades extras de primer seguimiento"
        verbose_name_plural = "Actividades extras de primer seguimiento"

    def __str__(self):
        return self.id_actividad or f"Actividad seguimiento #{self.pk or 'sin id'}"


class TarjetaSeguimiento(models.Model):
    id_tarjeta = _nullable_char(unique=True)
    persona_responsable = _nullable_bool()
    llegada_tarjeta = _nullable_bool()
    mes_notificado = _nullable_bool()
    conforme_tarjeta = _nullable_bool()
    conforme_porque = _nullable_char()

    class Meta:
        verbose_name = "Tarjeta de primer seguimiento"
        verbose_name_plural = "Tarjetas de primer seguimiento"

    def __str__(self):
        return self.id_tarjeta or f"Tarjeta seguimiento #{self.pk or 'sin id'}"


class RendicionCuentasSeguimiento(models.Model):
    id_rendicion = _nullable_char(unique=True)
    persona_encargada = _nullable_bool()
    recibio_capacitacion = _nullable_bool()
    norecibio_porque = _nullable_bool()
    sencilla_plataforma = _nullable_bool()
    nosencilla_porque = _nullable_bool()
    inconvenientes_carga = _nullable_bool()
    incovenientes_porque = _nullable_char()

    class Meta:
        verbose_name = "Rendicion de cuentas de primer seguimiento"
        verbose_name_plural = "Rendiciones de cuentas de primer seguimiento"

    def __str__(self):
        return self.id_rendicion or f"Rendicion seguimiento #{self.pk or 'sin id'}"


class AsistenciaTecnicaSeguimiento(models.Model):
    id_asistencia = _nullable_char(unique=True)
    socio_organizativo = _scale_field(4)
    alimentario_nutricion = _scale_field(4)
    seguridad_higiene = _scale_field(4)
    administrativo_rendicion = _scale_field(4)
    otro = _nullable_char()

    class Meta:
        verbose_name = "Asistencia tecnica de primer seguimiento"
        verbose_name_plural = "Asistencias tecnicas de primer seguimiento"

    def __str__(self):
        return self.id_asistencia or f"Asistencia seguimiento #{self.pk or 'sin id'}"


class CierreSeguimiento(models.Model):
    COMPLETA = "Completa"
    PARCIAL = "Parcial"
    NO_CORRESPONDE = "No corresponde"
    REALIZO_FORMA_CHOICES = [
        (COMPLETA, COMPLETA),
        (PARCIAL, PARCIAL),
        (NO_CORRESPONDE, NO_CORRESPONDE),
    ]

    info_adicional = _nullable_char()
    realizo_forma = _nullable_char(choices=REALIZO_FORMA_CHOICES)
    comentarios_finales = _nullable_text()
    firma_entrevistado = _nullable_char(max_length=600)
    firma_tecnico = _nullable_char(max_length=600)

    class Meta:
        verbose_name = "Cierre de primer seguimiento"
        verbose_name_plural = "Cierres de primer seguimiento"

    def __str__(self):
        return f"Cierre seguimiento #{self.pk or 'sin id'}"


class PrimerSeguimiento(models.Model):
    ESTADO_ASIGNADO = "Asignado"
    ESTADO_EN_PROCESO = "En Proceso"
    ESTADO_COMPLETO = "Completo"
    ESTADO_CHOICES = [
        (ESTADO_ASIGNADO, ESTADO_ASIGNADO),
        (ESTADO_EN_PROCESO, ESTADO_EN_PROCESO),
        (ESTADO_COMPLETO, ESTADO_COMPLETO),
    ]

    fecha_hora = models.DateTimeField(null=True, blank=True)
    id_relevamiento = models.OneToOneField(
        to=Relevamiento,
        on_delete=models.PROTECT,
        related_name="primer_seguimiento",
    )
    tecnico = _nullable_char()
    referente = models.ForeignKey(
        to=Referente,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    estado = _nullable_char(choices=ESTADO_CHOICES)
    funcionamiento = models.OneToOneField(
        to=FuncionamientoSeguimiento,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    servicios_basicos = models.OneToOneField(
        to=ServiciosBasicosSeguimiento,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    almacenamiento_alimentos = models.OneToOneField(
        to=AlmacenamientoAlimentosSeguimiento,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    condiciones_higiene = models.OneToOneField(
        to=CondicionesHigieneSeguimiento,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    tareas_comedor = models.OneToOneField(
        to=TareasComedorSeguimiento,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    recursos = models.OneToOneField(
        to=RecursosSeguimiento,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    compras = models.OneToOneField(
        to=ComprasSeguimiento,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    frecuencia_compra_alimentos = models.OneToOneField(
        to=FrecuenciaCompraAlimentosSeguimiento,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    menu = models.OneToOneField(
        to=MenuSeguimiento,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    registro_asistencia = models.OneToOneField(
        to=RegistroAsistenciaSeguimiento,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    frecuencia_alimentos = models.OneToOneField(
        to=FrecuenciaAlimentosSeguimiento,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    actividades_extras = models.OneToOneField(
        to=ActividadesExtrasSeguimiento,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    tarjeta = models.OneToOneField(
        to=TarjetaSeguimiento,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    rendicion_cuentas = models.OneToOneField(
        to=RendicionCuentasSeguimiento,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    asistencia_tecnica = models.OneToOneField(
        to=AsistenciaTecnicaSeguimiento,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    cierre = models.OneToOneField(
        to=CierreSeguimiento,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    @property
    def cod_pnud(self):
        return getattr(self.id_relevamiento.comedor, "codigo_de_proyecto", None)

    class Meta:
        indexes = [
            models.Index(fields=["estado"]),
        ]
        verbose_name = "Primer seguimiento de relevamiento"
        verbose_name_plural = "Primeros seguimientos de relevamiento"

    def __str__(self):
        return f"Primer seguimiento #{self.pk or 'sin id'}"


class PrestacionSeguimiento(models.Model):
    seguimiento = models.ForeignKey(
        to=PrimerSeguimiento,
        on_delete=models.CASCADE,
        related_name="prestaciones",
    )
    id_prestacion_seg = _nullable_char(unique=True)
    dias_prestacion = _nullable_char()
    tipo_prestacion = _nullable_char()
    ap_presencial = _nullable_positive_int()
    ap_vianda = _nullable_positive_int()
    de_presencial = _nullable_positive_int()
    de_vianda = _nullable_positive_int()

    class Meta:
        verbose_name = "Prestacion de primer seguimiento"
        verbose_name_plural = "Prestaciones de primer seguimiento"

    def __str__(self):
        return (
            self.id_prestacion_seg or f"Prestacion seguimiento #{self.pk or 'sin id'}"
        )


class ItemRecetaSeguimiento(models.Model):
    menu = models.ForeignKey(
        to=MenuSeguimiento,
        on_delete=models.CASCADE,
        related_name="receta_items",
    )
    id_item_receta = _nullable_char(unique=True)
    ingrediente = _nullable_char()
    unidad_medida = _nullable_char()
    cantidad_medida = _nullable_char()

    class Meta:
        verbose_name = "Item de receta de primer seguimiento"
        verbose_name_plural = "Items de receta de primer seguimiento"

    def __str__(self):
        return self.id_item_receta or f"Item receta seguimiento #{self.pk or 'sin id'}"


class ClasificacionComedor(models.Model):
    puntuacion_total = models.IntegerField()
    categoria = models.ForeignKey(
        to=CategoriaComedor, on_delete=models.SET_NULL, null=True
    )
    comedor = models.ForeignKey(to=Comedor, on_delete=models.SET_NULL, null=True)
    relevamiento = models.ForeignKey(
        to=Relevamiento, on_delete=models.SET_NULL, null=True
    )
    fecha = models.DateTimeField(default=timezone.now, blank=True)

    def __str__(self):
        return str(self.puntuacion_total)

    class Meta:
        verbose_name = "Clasificacion de Comedor"
        verbose_name_plural = "Clasificaciones de Comedor"
