from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.forms import ValidationError
from django.utils import timezone

from comedores.models.comedor import (
    Comedor,
    Referente,
    TipoDeComedor,
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

    class Meta:
        verbose_name = "Espacio donde se brinda la prestacion del Comedor/Merendero"
        verbose_name_plural = (
            "Espacios donde se brinda la prestacion del Comedor/Merendero"
        )


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
    lunes_merienda_espera = models.PositiveIntegerField(null=True, blank=True)
    lunes_cena_actual = models.PositiveIntegerField(null=True, blank=True)
    lunes_cena_espera = models.PositiveIntegerField(null=True, blank=True)

    martes_desayuno_actual = models.PositiveIntegerField(null=True, blank=True)
    martes_desayuno_espera = models.PositiveIntegerField(null=True, blank=True)
    martes_almuerzo_actual = models.PositiveIntegerField(null=True, blank=True)
    martes_almuerzo_espera = models.PositiveIntegerField(null=True, blank=True)
    martes_merienda_actual = models.PositiveIntegerField(null=True, blank=True)
    martes_merienda_espera = models.PositiveIntegerField(null=True, blank=True)
    martes_cena_actual = models.PositiveIntegerField(null=True, blank=True)
    martes_cena_espera = models.PositiveIntegerField(null=True, blank=True)

    miercoles_desayuno_actual = models.PositiveIntegerField(null=True, blank=True)
    miercoles_desayuno_espera = models.PositiveIntegerField(null=True, blank=True)
    miercoles_almuerzo_actual = models.PositiveIntegerField(null=True, blank=True)
    miercoles_almuerzo_espera = models.PositiveIntegerField(null=True, blank=True)
    miercoles_merienda_actual = models.PositiveIntegerField(null=True, blank=True)
    miercoles_merienda_espera = models.PositiveIntegerField(null=True, blank=True)
    miercoles_cena_actual = models.PositiveIntegerField(null=True, blank=True)
    miercoles_cena_espera = models.PositiveIntegerField(null=True, blank=True)

    jueves_desayuno_actual = models.PositiveIntegerField(null=True, blank=True)
    jueves_desayuno_espera = models.PositiveIntegerField(null=True, blank=True)
    jueves_almuerzo_actual = models.PositiveIntegerField(null=True, blank=True)
    jueves_almuerzo_espera = models.PositiveIntegerField(null=True, blank=True)
    jueves_merienda_actual = models.PositiveIntegerField(null=True, blank=True)
    jueves_merienda_espera = models.PositiveIntegerField(null=True, blank=True)
    jueves_cena_actual = models.PositiveIntegerField(null=True, blank=True)
    jueves_cena_espera = models.PositiveIntegerField(null=True, blank=True)

    viernes_desayuno_actual = models.PositiveIntegerField(null=True, blank=True)
    viernes_desayuno_espera = models.PositiveIntegerField(null=True, blank=True)
    viernes_almuerzo_actual = models.PositiveIntegerField(null=True, blank=True)
    viernes_almuerzo_espera = models.PositiveIntegerField(null=True, blank=True)
    viernes_merienda_actual = models.PositiveIntegerField(null=True, blank=True)
    viernes_merienda_espera = models.PositiveIntegerField(null=True, blank=True)
    viernes_cena_actual = models.PositiveIntegerField(null=True, blank=True)
    viernes_cena_espera = models.PositiveIntegerField(null=True, blank=True)

    sabado_desayuno_actual = models.PositiveIntegerField(null=True, blank=True)
    sabado_desayuno_espera = models.PositiveIntegerField(null=True, blank=True)
    sabado_almuerzo_actual = models.PositiveIntegerField(null=True, blank=True)
    sabado_almuerzo_espera = models.PositiveIntegerField(null=True, blank=True)
    sabado_merienda_actual = models.PositiveIntegerField(null=True, blank=True)
    sabado_merienda_espera = models.PositiveIntegerField(null=True, blank=True)
    sabado_cena_actual = models.PositiveIntegerField(null=True, blank=True)
    sabado_cena_espera = models.PositiveIntegerField(null=True, blank=True)

    domingo_desayuno_actual = models.PositiveIntegerField(null=True, blank=True)
    domingo_desayuno_espera = models.PositiveIntegerField(null=True, blank=True)
    domingo_almuerzo_actual = models.PositiveIntegerField(null=True, blank=True)
    domingo_almuerzo_espera = models.PositiveIntegerField(null=True, blank=True)
    domingo_merienda_actual = models.PositiveIntegerField(null=True, blank=True)
    domingo_merienda_espera = models.PositiveIntegerField(null=True, blank=True)
    domingo_cena_actual = models.PositiveIntegerField(null=True, blank=True)
    domingo_cena_espera = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Prestacion"
        verbose_name_plural = "Prestaciones"


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


class Relevamiento(models.Model):

    estado = models.CharField(max_length=255, blank=True, null=True)
    comedor = models.ForeignKey(
        to=Comedor,
        on_delete=models.CASCADE,
    )
    fecha_visita = models.DateTimeField(null=True, blank=True)
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
        if self.responsable_es_referente:
            self.responsable = self.comedor.referente

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


class CategoriaComedor(models.Model):
    nombre = models.CharField(max_length=255)
    puntuacion_min = models.IntegerField()
    puntuacion_max = models.IntegerField()

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Categoria de Comedor"
        verbose_name_plural = "Categorias de Comedor"


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
