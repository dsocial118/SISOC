from django.db import models
from django.forms import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User

from configuraciones.models import Provincia


class Rubro(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Rubro"
        verbose_name_plural = "Rubros"


class TipoPersonaJuridica(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de Persona Jurídica"
        verbose_name_plural = "Tipos de Personas Jurídicas"


class Objetivo(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Objetivo"
        verbose_name_plural = "Objetivos"


class TipoActividad(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de Actividad"
        verbose_name_plural = "Tipos de Actividad"


class TipoComunidad(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de Comunidad"
        verbose_name_plural = "Tipos de Comunidad"


class CantidadIntegrantes(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Cantidad de Integrantes"
        verbose_name_plural = "Cantidades de Integrantes"


class Genero(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Género"
        verbose_name_plural = "Géneros"


class TipoInmueble(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de Inmueble"
        verbose_name_plural = "Tipos de Inmueble"


class TipoInternet(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de Internet"
        verbose_name_plural = "Tipos de Internet"


class TipoDispositivosMoviles(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de Dispositivos Móviles"
        verbose_name_plural = "Tipos de Dispositivos Móviles"


class PlataformaComunicacion(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Plataforma de Comunicación"
        verbose_name_plural = "Plataformas de Comunicación"


class RedSocial(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Red Social"
        verbose_name_plural = "Redes Sociales"


class Comprador(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Comprador"
        verbose_name_plural = "Compradores"


class EstudiosAlcanzados(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Estudios Alcanzados"
        verbose_name_plural = "Estudios Alcanzados"


class TipoOcupacion(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de Ocupación"
        verbose_name_plural = "Tipos de Ocupación"


class CondicionOcupacion(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Condición de Ocupación"
        verbose_name_plural = "Condiciones de Ocupación"


class OcupacionHorasSemanales(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Ocupación Horas Semanales"
        verbose_name_plural = "Ocupaciones Horas Semanales"


class IngresoPromedioFamiliar(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Ingreso Promedio Familiar"
        verbose_name_plural = "Ingresos Promedio Familiar"


class CantidadClientes(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Cantidad de Clientes"
        verbose_name_plural = "Cantidades de Clientes"


class LugarComercializacion(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Lugar de Comercialización"
        verbose_name_plural = "Lugares de Comercialización"


class ModalidadComercializacion(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Modalidad de Comercialización"
        verbose_name_plural = "Modalidades de Comercialización"


class FijacionPrecios(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Fijación de Precios"
        verbose_name_plural = "Fijaciones de Precios"


class CantidadCompetidores(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Cantidad de Competidores"
        verbose_name_plural = "Cantidades de Competidores"


class ConocimientoCompetidores(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Conocimiento de Competidores"
        verbose_name_plural = "Conocimientos de Competidores"


class InteractuaCompetidores(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Interacción con Competidores"
        verbose_name_plural = "Interacciones con Competidores"


class ModalidadCompras(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Modalidad de Compras"
        verbose_name_plural = "Modalidades de Compras"


class PlazoCompraCredito(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Plazo de Compra a Crédito"
        verbose_name_plural = "Plazos de Compra a Crédito"


class MedioPlanificacion(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Medio de Planificación"
        verbose_name_plural = "Medios de Planificación"


class CanalesVentas(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Canal de Ventas"
        verbose_name_plural = "Canales de Ventas"


class DestinoMaterialesRecuperados(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Destino de Materiales Recuperados"
        verbose_name_plural = "Destinos de Materiales Recuperados"


class ModalidadCicloProductivo(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Modalidad de Ciclo Productivo"
        verbose_name_plural = "Modalidades de Ciclo Productivo"


class AbstractPersoneria(models.Model):
    # Ubicacion
    direccion = models.CharField(max_length=255, verbose_name="Dirección")
    localidad = models.CharField(max_length=255, verbose_name="Localidad")
    codigo_postal = models.PositiveBigIntegerField(verbose_name="Codigo postal")
    provincia = models.ForeignKey(
        Provincia, on_delete=models.PROTECT, verbose_name="Provincia"
    )

    # Datos del proyecto
    proyecto_nombre = models.CharField(
        max_length=255, verbose_name="Nombre del Proyecto"
    )
    proyecto_tipo_actividad = models.ForeignKey(
        TipoActividad,
        on_delete=models.PROTECT,
        related_name="personeria_tipo_actividad",
        verbose_name="Tipo de Actividad del Proyecto",
    )
    proyecto_rubro = models.ForeignKey(
        Rubro, on_delete=models.PROTECT, verbose_name="Rubro del Proyecto"
    )
    proyecto_objetivo = models.ForeignKey(
        Objetivo, on_delete=models.PROTECT, verbose_name="Objetivo del Proyecto"
    )
    proyecto_costo = models.PositiveBigIntegerField(verbose_name="Costo del Proyecto")
    proyecto_pertenece_comunidad_indigena = models.BooleanField(
        default=False, verbose_name="¿El proyecto pertenece a una comunidad indigena?"
    )
    proyecto_comunidad_indigena = models.CharField(
        max_length=255, blank=True, null=True
    )
    proyecto_practicas_regenerativas = models.BooleanField(
        default=False,
        verbose_name="¿El proyecto esta vinculado a prácticas regenerativas/agroecológicas",
    )

    def clean(self):
        if (
            self.proyecto_pertenece_comunidad_indigena
            and self.proyecto_comunidad_indigena == ""
        ):
            raise ValidationError("Debe aclarar a que comunidad indigena pertenece.")
        return super().clean()

    class Meta:
        abstract = True


class PersonaJuridica(AbstractPersoneria):
    nombre = models.CharField(max_length=255, verbose_name="Nombre de la Organización")
    tipo = models.ForeignKey(
        TipoPersonaJuridica,
        on_delete=models.PROTECT,
        verbose_name="Tipo de Organización",
    )
    fecha_creacion = models.DateField(verbose_name="Fecha de Creación")
    numero_personeria_juridica = models.CharField(
        max_length=255, verbose_name="Número de Personería Jurídica"
    )
    fecha_otorgamiento = models.DateField(verbose_name="Fecha de otorgamiento")
    cuit = models.PositiveBigIntegerField(verbose_name="CUIT")
    domicilio_legal = models.CharField(
        max_length=255, verbose_name="Domicilio Legal y Electrónico"
    )

    autoridad_nombre_completo = models.CharField(
        max_length=255, verbose_name="Nombre completo de la autoridad"
    )
    autoridad_dni = models.PositiveBigIntegerField(verbose_name="DNI de la autoridad")
    autoridad_cuit = models.PositiveBigIntegerField(verbose_name="CUIT de la autoridad")
    autoridad_rol = models.CharField(max_length=255, verbose_name="Rol de la autoridad")

    proyecto_tipo_actividad = models.ForeignKey(
        TipoActividad,
        on_delete=models.PROTECT,
        related_name="organizacion_tipo_actividad",
    )

    def __str__(self) -> str:
        return str(self.nombre)

    class Meta:
        verbose_name = "Organización"
        verbose_name_plural = "Organizaciones"


class PersonaFisica(AbstractPersoneria):
    nombre_completo = models.CharField(max_length=255, verbose_name="Nombre completo")
    dni = models.PositiveBigIntegerField(verbose_name="DNI")
    fecha_nacimiento = models.DateField(verbose_name="Fecha de nacimiento")
    cuil = models.PositiveBigIntegerField(verbose_name="CUIL")
    domicilio_real = models.CharField(max_length=255, verbose_name="Domicilio real")
    mail = models.EmailField(verbose_name="Correo electrónico")
    telefono = models.PositiveBigIntegerField(verbose_name="Teléfono")

    proyecto_tipo_actividad = models.ForeignKey(
        TipoActividad,
        on_delete=models.PROTECT,
        related_name="persona_tipo_actividad",
    )

    def __str__(self) -> str:
        return str(self.nombre_completo)

    class Meta:
        verbose_name = "Persona"
        verbose_name_plural = "Personas"


class LineaDeAccion(models.Model):
    # Fortalecimiento Productivo
    produccion_apoyo_tecnico = models.BooleanField(
        default=False, verbose_name="Apoyo técnico para mejorar competitividad"
    )
    produccion_maquinaria = models.BooleanField(
        default=False, verbose_name="Acceso a máquinas, herramientas e insumos"
    )
    produccion_tecnologias = models.BooleanField(
        default=False, verbose_name="Incorporación de nuevas tecnologías"
    )
    produccion_entrega = models.BooleanField(
        default=False, verbose_name="Entrega directa según stock"
    )

    # Comercialización
    comercializacion_fortalecimiento_institucional = models.BooleanField(
        default=False, verbose_name="Fortalecimiento Institucional"
    )
    comercializacion_apoyo_tecnologico = models.BooleanField(
        default=False, verbose_name="Apoyo Tecnológico"
    )
    comercializacion_habilidades_blandas = models.BooleanField(
        default=False, verbose_name="Habilidades Blandas para la Comercialización"
    )
    comercializacion_fortalecimiento_unidades = models.BooleanField(
        default=False,
        verbose_name="Fortalecimiento de la Comercialización de Unidades Productivas",
    )

    # Economia circular
    circular_fortalecimiento = models.BooleanField(
        default=False,
        verbose_name="Fortalecimiento a recuperadores de base, organizaciones y sistemas locales de reciclado",
    )
    circular_practicas_sostenibles = models.BooleanField(
        default=False, verbose_name="Implementación de prácticas sostenibles"
    )
    circular_materiales_reciclados = models.BooleanField(
        default=False, verbose_name="Uso de materiales reciclados"
    )
    circular_reduccion_residuos = models.BooleanField(
        default=False, verbose_name="Reducción de residuos"
    )

    fundamentacion = models.TextField(verbose_name="Fundamentos del proyecto")

    destinatarios_directos = models.FileField(
        upload_to="destinatarios_directos/", verbose_name="Destinatarios directos"
    )
    destinatarios_indirectos = models.PositiveBigIntegerField(
        verbose_name="Destinatarios indirectos"
    )

    @property
    def cantidad_destinatarios_directos(self):
        return self.destinatario_set.count()


class Presupuesto(models.Model):
    linea_de_accion = models.ForeignKey(
        LineaDeAccion, on_delete=models.PROTECT, related_name="presupuestos"
    )
    tipo_actividad = models.CharField(max_length=255)
    tipo_producto = models.CharField(max_length=255)
    nombre_producto = models.CharField(max_length=255)
    cantidad_producto = models.PositiveBigIntegerField()
    costo_unitario = models.PositiveBigIntegerField()

    @property
    def costo_total(self):
        return self.cantidad_producto * self.costo_unitario


class AbstractDiagnostico(models.Model):
    # Bloque 2: Estructura economica
    tipo_actividad = models.ManyToManyField(
        TipoActividad, verbose_name="Tipo de actividad"
    )
    rubro = models.ForeignKey(
        Rubro, on_delete=models.PROTECT, verbose_name="Rubro de la organización"
    )
    banco = models.BooleanField(default=False, verbose_name="¿Opera con algún banco?")
    banco_nombre = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="¿Cual banco?"
    )
    cuenta_digital = models.BooleanField(
        default=False, verbose_name="¿Tiene alguna cuenta digital?"
    )
    financiamiento = models.BooleanField(
        default=False, verbose_name="¿Posee otras fuentes de financiamiento y/o apoyo?"
    )
    financiamiento_nombre = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="¿Cual financiamiento?"
    )
    tipo_inmueble = models.ForeignKey(
        TipoInmueble,
        on_delete=models.PROTECT,
        verbose_name="El inmueble afectado a la actividad es de tipo",
    )
    ingresos_mensuales = models.PositiveBigIntegerField(
        verbose_name="Ingresos promedios mensuales"
    )
    egresos_mensuales = models.PositiveBigIntegerField(
        verbose_name="Egresos promedios mensuales"
    )
    ganancias_mensuales = models.PositiveBigIntegerField(
        verbose_name="Excede o ganancias (ventas - costo del mes)"
    )

    # Bloque 3: Conectividad
    internet = models.BooleanField(
        default=False, verbose_name="¿Cuenta con acceso a internet?"
    )
    tipo_internet = models.ForeignKey(
        TipoInternet,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name="Tipo de acceso a internet",
    )
    dispositivos_conectados = models.PositiveBigIntegerField(
        blank=True, null=True, verbose_name="Número de dispositivos conectados"
    )
    tipo_dispositivos_moviles = models.ManyToManyField(
        TipoDispositivosMoviles,
        verbose_name="Tipo de dispositivos móviles",
    )
    plataforma_comunicacion = models.ManyToManyField(
        PlataformaComunicacion, verbose_name="Plataformas de comunicación utilizadas"
    )
    redes_sociales = models.ManyToManyField(
        RedSocial, verbose_name="Uso de redes sociales"
    )

    # Bloque 4: Comercializacion
    comprador = models.ForeignKey(
        Comprador, on_delete=models.PROTECT, verbose_name="¿A quién le vende?"
    )
    cantidad_clientes = models.ForeignKey(
        CantidadClientes,
        on_delete=models.PROTECT,
        verbose_name="¿Cuántos clientes tiene?",
    )
    lugar_comercializacion = models.ForeignKey(
        LugarComercializacion, on_delete=models.PROTECT, verbose_name="¿Dónde vende?"
    )
    modalidad_comercializacion = models.ForeignKey(
        ModalidadComercializacion,
        on_delete=models.PROTECT,
        verbose_name="¿Cómo realiza sus ventas o produccion?",
    )
    fijacion_precios = models.ForeignKey(
        FijacionPrecios,
        on_delete=models.PROTECT,
        verbose_name="¿Cómo fija los precios de venta?",
    )
    cantidad_competidores = models.ForeignKey(
        CantidadCompetidores,
        on_delete=models.PROTECT,
        verbose_name="Cuántos competidores tiene en su radio de venta?",
    )
    conocimiento_competidores = models.ForeignKey(
        ConocimientoCompetidores,
        on_delete=models.PROTECT,
        verbose_name="¿Conoce a sus competidores?",
    )
    interactua_compentidores = models.ForeignKey(
        InteractuaCompetidores,
        on_delete=models.PROTECT,
        verbose_name="¿Interactúa con sus competidores?",
    )
    modalidad_compras = models.ForeignKey(
        ModalidadCompras,
        on_delete=models.PROTECT,
        verbose_name="¿Cómo compra habitualmente?",
    )
    plazo_compra_credito = models.ForeignKey(
        PlazoCompraCredito,
        on_delete=models.PROTECT,
        verbose_name="Si compra a crédito, ¿qué plazo tiene para pagar?",
    )
    medio_planificacion = models.ForeignKey(
        MedioPlanificacion,
        on_delete=models.PROTECT,
        verbose_name="¿A través de qué medio planifica su administración?",
    )
    canales_ventas = models.ManyToManyField(
        CanalesVentas, verbose_name="Canales de venta"
    )
    ventas_destinadas_turismo = models.BooleanField(
        default=False, verbose_name="¿Sus ventas suelen estar destinadas al turismo?"
    )

    # Bloque 5
    recicladores_urbanos = models.BooleanField(
        default=False,
        verbose_name="¿El proyecto incluye activamente a recicladores urbanos organizados en cooperativas o asociaciones?",
    )
    recicladores_equipados = models.BooleanField(
        default=False,
        verbose_name=(
            "¿Los recicladores urbanos cuentan con elementos de protección personal "
            "adecuados, condiciones laborales adecuadas como salarios dignos y horarios "
            "razonables?"
        ),
    )
    clasificacion_residuos = models.BooleanField(
        default=False,
        verbose_name="¿Existe un sistema de separación y clasificación de residuos desde el origen, en el proyecto de referencia?",
    )
    destino_materiales_recuperados = models.ManyToManyField(
        DestinoMaterialesRecuperados,
        verbose_name="¿Cuál es el destino de los materiales recuperados?",
    )
    optimizacion_recursos = models.BooleanField(
        default=False,
        verbose_name="¿El proyecto optimiza el uso de los recursos, promoviendo la reducción del consumo de materiales?",
    )
    modalidad_ciclo_productivo = models.ForeignKey(
        ModalidadCicloProductivo,
        on_delete=models.PROTECT,
        verbose_name="¿El ciclo productivo es lineal o circular (se reintroducen los lateriales en la cadena productiva)?",
    )
    financiamiento_sostenible = models.BooleanField(
        default=False,
        verbose_name="¿El proyecto cuenta con fuentes de financiamiento sostenibles?",
    )
    estrategia_comercializacion = models.BooleanField(
        default=False, verbose_name="¿Poseen estrategias de comercialización?"
    )
    tecnologias_mejorar_eficiencia = models.BooleanField(
        default=False,
        verbose_name=(
            "¿Se utilizan tecnologías para mejorar la eficiencia en la recolección, "
            "clasificación y reciclaje de materiales y los recicladores tienen acceso a plataformas digitales?"
        ),
    )
    tecnologias_cuales = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="¿Cuáles tecnologias se utilizan?",
    )

    def clean(self) -> None:
        if self.internet and (
            not self.tipo_internet or not self.dispositivos_conectados
        ):
            raise ValidationError("Debe completar los datos relacionados al internet.")

        if self.banco and not self.banco_nombre:
            raise ValidationError("Debe completar el nombre del banco.")

        if self.financiamiento and not self.financiamiento_nombre:
            raise ValidationError("Debe completar el nombre del financiamiento.")

        if self.tecnologias_mejorar_eficiencia and not self.tecnologias_cuales:
            raise ValidationError("Debe completar las tecnologías utilizadas.")

        return super().clean()

    class Meta:
        abstract = True


class DiagnosticoJuridica(AbstractDiagnostico):
    # Bloque 1: Contexto general
    mision_vision = models.TextField(verbose_name="Misión y visión de la organización")
    tipo_comunidad = models.ManyToManyField(
        TipoComunidad, verbose_name="Tipo de comunidad donde opera la institucion"
    )
    cantidad_integrantes = models.ForeignKey(
        CantidadIntegrantes,
        on_delete=models.PROTECT,
        verbose_name="Cantidad de integrantes de su organizacion",
    )
    genero_mayoria = models.ForeignKey(
        Genero, on_delete=models.PROTECT, verbose_name="Géneros de la mayoria"
    )
    composicion_equipo = models.CharField(
        max_length=255, verbose_name="Composición de su equipo de trabajo"
    )

    class Meta:
        verbose_name = "Diagnóstico de Organización"
        verbose_name_plural = "Diagnósticos de Organizaciones"


class DiagnosticoFisica(AbstractDiagnostico):
    # Bloque 1: Contexto general
    estudios_alcanzados = models.ManyToManyField(
        EstudiosAlcanzados, verbose_name="Nivel de estudios alcanzados"
    )
    ocupacion = models.ForeignKey(
        TipoOcupacion, on_delete=models.PROTECT, verbose_name="Ocupación"
    )
    ocupacion_condicion = models.ForeignKey(
        CondicionOcupacion,
        on_delete=models.PROTECT,
        verbose_name="Condición de tu actividad",
    )
    ocupacion_sosten_hogar = models.BooleanField(
        default=False, verbose_name="¿Es esta actividad el principal sostén del hogar?"
    )
    ocupacion_horas_semanales = models.ForeignKey(
        OcupacionHorasSemanales,
        on_delete=models.PROTECT,
        verbose_name="Cuántas horas semanales le dedica a la actividad",
    )
    beneficiario_social = models.BooleanField(
        default=False,
        verbose_name="¿Es beneficiario de algún programa social nacional y/o provincial?",
    )
    beneficio_social = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="¿Cuál?"
    )
    familia_adultos = models.PositiveBigIntegerField(
        verbose_name="Cantidad de adultos en el grupo familiar"
    )
    familia_menores = models.PositiveBigIntegerField(
        verbose_name="Cantidad de menores en el grupo familiar"
    )
    familia_trabajadores = models.PositiveBigIntegerField(
        verbose_name="Cantidad de personas que trabajan en el grupo familiar"
    )
    familia_ingreso_promedio = models.ForeignKey(
        IngresoPromedioFamiliar,
        on_delete=models.PROTECT,
        verbose_name="Ingreso promedio familiar",
    )

    @property
    def familia_total(self):
        return self.familia_adultos + self.familia_menores

    class Meta:
        verbose_name = "Diagnóstico de Persona"
        verbose_name_plural = "Diagnósticos de Personas"


class Proyecto(models.Model):
    fecha_creacion = models.DateTimeField(auto_now=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    creador = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="creador", blank=True
    )
    modificador = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="modificador",
    )
    estado = models.CharField(max_length=255, blank=True, default="Pendiente")

    nombre = models.CharField(max_length=255, null=True)

    TIPO_ANEXO_CHOICES = (
        ("SOCIO_PRODUCTIVO", "Socio Productivo"),
        ("FORMACION", "Formación"),
    )
    tipo_anexo = models.CharField(max_length=255, choices=TIPO_ANEXO_CHOICES)

    provincia = models.ForeignKey(
        Provincia, on_delete=models.PROTECT, blank=True, null=True
    )

    @property
    def presupuesto_total(self):
        total = (
            Presupuesto.objects.filter(
                linea_de_accion__anexosocioproductivo__proyecto=self
            )
            .aggregate(total=models.Sum("costo_total"))
            .get("total", 0)
        )
        return total or 0

    def save(self, *args, **kwargs):
        self.update_modificador(kwargs)

        self.provincia = (
            Provincia.objects.get(nombre=self.creador.provincia)
            if self.creador.provincia
            else None
        )

        super().save(*args, **kwargs)

    def update_modificador(self, kwargs):
        self.fecha_ultima_modificacion = timezone.now()
        if "usuario" in kwargs:  # Define el modificador si es pasado como argumento
            self.modificador = kwargs.pop("usuario")

    def __str__(self) -> str:
        return str(self.nombre)


class Observacion(models.Model):
    proyecto = models.ForeignKey(
        Proyecto, on_delete=models.PROTECT, related_name="observaciones"
    )
    observacion = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.observacion)

    class Meta:
        verbose_name = "Observación"
        verbose_name_plural = "Observaciones"


class AnexoSocioProductivo(models.Model):
    # Proyecto y personeria
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.PROTECT,
        related_name="anexos_socioproductivos",
    )
    PERSONERIA_CHOICES = (
        ("JURIDICA", "Persona Juridica"),
        ("FISICA", "Persona Fisica"),
    )
    personeria = models.CharField(
        max_length=255,
        choices=PERSONERIA_CHOICES,
        verbose_name="¿Persona fisica o persona juridica?",
    )
    juridica = models.ForeignKey(
        PersonaJuridica, on_delete=models.PROTECT, blank=True, null=True
    )
    fisica = models.ForeignKey(
        PersonaFisica, on_delete=models.PROTECT, blank=True, null=True
    )

    linea_de_accion = models.ForeignKey(LineaDeAccion, on_delete=models.PROTECT)

    # Diagnostico
    diagnostico_juridica = models.ForeignKey(
        DiagnosticoJuridica, on_delete=models.PROTECT, blank=True, null=True
    )
    diagnostico_fisica = models.ForeignKey(
        DiagnosticoFisica, on_delete=models.PROTECT, blank=True, null=True
    )

    # Documentacion respecto de organizaciones no gubernamentales
    acta_constitutiva = models.FileField(
        upload_to="anexos/socioproductivos/actas_constitutivas/",
        verbose_name="Acta constitutiva",
    )
    estatuto = models.FileField(
        upload_to="anexos/socioproductivos/estatutos/", verbose_name="Estatuto"
    )
    personeria_juridica = models.FileField(
        upload_to="anexos/socioproductivos/personerias_juridicas/",
        verbose_name="Personería jurídica",
    )
    designacion_autoridades = models.FileField(
        upload_to="anexos/socioproductivos/designaciones_autoridades/",
        verbose_name="Designación de autoridades",
    )
    autorizacion_gestionar = models.FileField(
        upload_to="anexos/socioproductivos/autorizaciones_gestionar/",
        verbose_name="Autorización a gestionar",
    )

    # Documentacion respecto de organizaciones gubernamentales
    designacion_intendente = models.FileField(
        upload_to="anexos/socioproductivos/designaciones_indentendes/",
        verbose_name="Designación del intendente",
    )

    media = models.FileField(
        upload_to="anexos/socioproductivos/", verbose_name="Contenido multimedia"
    )

    def clean(self):
        if (self.personeria == "JURIDICA" and not self.juridica) or (
            self.personeria == "FISICA" and not self.fisica
        ):
            raise ValidationError(
                "Debe completar una organización o una persona segun corresponda."
            )

        if (self.personeria == "JURIDICA" and not self.diagnostico_juridica) or (
            self.personeria == "FISICA" and not self.diagnostico_fisica
        ):
            raise ValidationError("Debe completar una el diagnostico para el anexo.")

        return super().clean()

    def __str__(self) -> str:
        return str(f"{self.id} - {self.proyecto} - {self.juridica or self.fisica}")

    class Meta:
        verbose_name = "Anexo socio productivo"
        verbose_name_plural = "Anexos socio productivo"


class AnexoFormacion(models.Model):
    proyecto = models.ForeignKey(
        Proyecto, on_delete=models.PROTECT, related_name="anexos_formaciones"
    )
