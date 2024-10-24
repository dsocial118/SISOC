from django.db import models
from django.forms import ValidationError
from django.utils import timezone

from legajos.models import LegajoProvincias
from usuarios.models import Usuarios


class EstadoSolicitud(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Estado de Solicitud"
        verbose_name_plural = "Estados de Solicitud"


class Rubro(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Rubro"
        verbose_name_plural = "Rubros"


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


class Organizacion(models.Model):
    nombre = models.CharField(max_length=255)
    tipo = models.CharField(max_length=255)
    fecha_creacion = models.DateField()
    numero_personeria_juridica = models.CharField(max_length=255)
    fecha_otorgamiento = models.DateField()
    cuit = models.PositiveBigIntegerField()
    domicilio_legal = models.CharField(max_length=255)
    mail = models.EmailField()
    telefono = models.PositiveBigIntegerField()

    direccion = models.CharField(max_length=255)
    localidad = models.CharField(max_length=255)
    codigo_postal = models.PositiveBigIntegerField()
    provincia = models.ForeignKey(LegajoProvincias, on_delete=models.PROTECT)

    autoridad_nombre_completo = models.CharField(max_length=255)
    autoridad_dni = models.PositiveBigIntegerField()
    autoridad_cuit = models.PositiveBigIntegerField()
    autoridad_rol = models.CharField(max_length=255)

    proyecto_nombre = models.CharField(max_length=255)
    proyecto_tipo_actividad = models.ForeignKey(
        TipoActividad,
        on_delete=models.PROTECT,
        related_name="organizacion_tipo_actividad",
    )
    proyecto_rubro = models.ForeignKey(Rubro, on_delete=models.PROTECT)
    proyecto_objetivo = models.ForeignKey(Objetivo, on_delete=models.PROTECT)
    proyecto_costo = models.PositiveBigIntegerField()

    pertenece_comunidad_indigena = models.BooleanField(default=False)
    comunidad_indigena = models.CharField(max_length=255)

    practicas_regenerativas = models.BooleanField(default=False)

    def clean(self):
        if self.pertenece_comunidad_indigena and self.comunidad_indigena == "":
            raise ValidationError("Debe aclarar a que comunidad indigena pertenece.")
        return super().clean()

    class Meta:
        verbose_name = "Organización"
        verbose_name_plural = "Organizaciones"


class Persona(models.Model):
    nobre_completo = models.CharField(max_length=255)
    dni = models.PositiveBigIntegerField()
    fecha_nacimiento = models.DateField()
    cuil = models.PositiveBigIntegerField()
    domicilio_real = models.CharField(max_length=255)
    mail = models.EmailField()
    telefono = models.PositiveBigIntegerField()

    direccion = models.CharField(max_length=255)
    localidad = models.CharField(max_length=255)
    codigo_postal = models.PositiveBigIntegerField()
    provincia = models.ForeignKey(LegajoProvincias, on_delete=models.PROTECT)

    proyecto_nombre = models.CharField(max_length=255)
    proyecto_tipo_actividad = models.ForeignKey(
        TipoActividad, on_delete=models.PROTECT, related_name="persona_tipo_actividad"
    )
    proyecto_rubro = models.ForeignKey(Rubro, on_delete=models.PROTECT)
    proyecto_objetivo = models.ForeignKey(Objetivo, on_delete=models.PROTECT)
    proyecto_costo = models.PositiveBigIntegerField()

    pertenece_comunidad_indigena = models.BooleanField(default=False)
    comunidad_indigena = models.CharField(max_length=255)

    def clean(self):
        if self.pertenece_comunidad_indigena and self.comunidad_indigena == "":
            raise ValidationError("Debe aclarar a que comunidad indigena pertenece.")
        return super().clean()

    class Meta:
        verbose_name = "Persona"
        verbose_name_plural = "Personas"


class LineaDeAccion(models.Model):
    produccion_apoyo_tecnico = models.BooleanField(default=False)
    produccion_maquinaria = models.BooleanField(default=False)
    produccion_tecnologias = models.BooleanField(default=False)
    produccion_entrega = models.BooleanField(default=False)

    comercializacion_fortalecimiento_institucional = models.BooleanField(default=False)
    comercializacion_apoyo_tecnologico = models.BooleanField(default=False)
    comercializacion_habilidades_blandas = models.BooleanField(default=False)
    comercializacion_desarrollo_local = models.BooleanField(default=False)

    circular_fortalecimiento = models.BooleanField(default=False)
    circular_practicas_sostenibles = models.BooleanField(default=False)
    circular_materiales_reciclados = models.BooleanField(default=False)
    circular_reduccion_residuos = models.BooleanField(default=False)

    fundamentacion = models.TextField()

    @property
    def cantidad_destinatarios_directos(self):
        return self.destinatario_set.count()


class Presupuesto(models.Model):
    linea_de_accion = models.ForeignKey(LineaDeAccion, on_delete=models.PROTECT)
    tipo_actividad = models.CharField(max_length=255)
    tipo_producto = models.CharField(max_length=255)
    nombre_producto = models.CharField(max_length=255)
    cantidad_producto = models.PositiveBigIntegerField()
    costo_unitario = models.PositiveBigIntegerField()

    destinatarios_indirectos = models.PositiveBigIntegerField()

    @property
    def costo_total(self):
        return self.cantidad_producto * self.costo_unitario


class DestinatarioDirecto(models.Model):
    linea_de_accion = models.ForeignKey(
        LineaDeAccion, on_delete=models.CASCADE, related_name="destinatarios"
    )
    nombre = models.CharField(max_length=255)
    apellido = models.CharField(max_length=255)
    dni = models.PositiveBigIntegerField()


class DiagnosticoOrganizacion(models.Model):
    # Bloque 1: Contexto general
    mision_vision = models.TextField()
    tipo_comunidad = models.ManyToManyField(TipoComunidad)
    cantidad_integrantes = models.ForeignKey(
        CantidadIntegrantes, on_delete=models.PROTECT
    )
    genero_mayoria = models.ForeignKey(Genero, on_delete=models.PROTECT)
    composicion_equipo = models.CharField(max_length=255)
    directorio = models.BooleanField(default=False)
    personal_tecnico = models.BooleanField(default=False)
    personal_especializado = models.BooleanField(default=False)

    # Bloque 2: Estructura economica
    tipo_actividad = models.ManyToManyField(TipoActividad)
    rubro = models.ForeignKey(Rubro, on_delete=models.PROTECT)
    banco = models.BooleanField(default=False)
    banco_nombre = models.CharField(max_length=255, blank=True, null=True)
    cuenta_digital = models.BooleanField(default=False)
    financiamiento = models.BooleanField(default=False)
    financiamiento_nombre = models.CharField(max_length=255, blank=True, null=True)
    tipo_inmueble = models.ForeignKey(TipoInmueble, on_delete=models.PROTECT)
    ingresos_mensuales = models.PositiveBigIntegerField()
    egresos_mensuales = models.PositiveBigIntegerField()
    ganancias_mensuales = models.PositiveBigIntegerField()

    # Bloque 3: Conectividad
    internet = models.BooleanField(default=False)
    tipo_internet = models.ForeignKey(TipoInternet, on_delete=models.PROTECT)
    dispositivos_conectados = models.PositiveBigIntegerField()
    computadora = models.BooleanField(default=False)
    tipo_dispositivos_moviles = models.ManyToManyField(TipoDispositivosMoviles)
    plataforma_comunicacion = models.ManyToManyField(PlataformaComunicacion)
    redes_sociales = models.BooleanField(default=False)
    redes_sociales_cuales = models.ManyToManyField(RedSocial)

    # Bloque 4: Comercializacion
    comprador = models.ForeignKey(Comprador, on_delete=models.PROTECT)
    cantidad_clientes = models.ForeignKey(CantidadClientes, on_delete=models.PROTECT)
    lugar_comercializacion = models.ForeignKey(
        LugarComercializacion, on_delete=models.PROTECT
    )
    modalidad_comercializacion = models.ForeignKey(
        ModalidadComercializacion, on_delete=models.PROTECT
    )
    fijacion_precios = models.ForeignKey(FijacionPrecios, on_delete=models.PROTECT)
    cantidad_competidores = models.ForeignKey(
        CantidadCompetidores, on_delete=models.PROTECT
    )
    conocimiento_competidores = models.ForeignKey(
        ConocimientoCompetidores, on_delete=models.PROTECT
    )
    interactua_compentidores = models.ForeignKey(
        InteractuaCompetidores, on_delete=models.PROTECT
    )
    modalidad_compras = models.ForeignKey(ModalidadCompras, on_delete=models.PROTECT)
    plazo_compra_credito = models.ForeignKey(
        PlazoCompraCredito, on_delete=models.PROTECT
    )
    medio_planificacion = models.ForeignKey(
        MedioPlanificacion, on_delete=models.PROTECT
    )
    canales_ventas = models.ManyToManyField(CanalesVentas)


class DiagnosticoPersona(models.Model):
    # Bloque 1: Contexto general
    estudios_alcanzados = models.ManyToManyField(EstudiosAlcanzados)
    ocupacion = models.ForeignKey(TipoOcupacion, on_delete=models.PROTECT)
    ocupacion_condicion = models.ForeignKey(
        CondicionOcupacion, on_delete=models.PROTECT
    )
    ocupacion_sosten_hogar = models.BooleanField(default=False)
    ocupacion_horas_semanales = models.ForeignKey(
        OcupacionHorasSemanales, on_delete=models.PROTECT
    )
    beneficiario_social = models.BooleanField(default=False)
    beneficio_social = models.CharField(max_length=255)
    familia_adultos = models.PositiveBigIntegerField()
    familia_menores = models.PositiveBigIntegerField()
    familia_ingreso_promedio = models.ForeignKey(
        IngresoPromedioFamiliar, on_delete=models.PROTECT
    )

    @property
    def familia_total(self):
        return self.familia_adultos + self.familia_menores

    # Bloque 2: Estructura economica
    tipo_actividad = models.ManyToManyField(TipoActividad)
    rubro = models.ForeignKey(Rubro, on_delete=models.PROTECT)
    banco = models.BooleanField(default=False)
    banco_nombre = models.CharField(max_length=255, blank=True, null=True)
    cuenta_digital = models.BooleanField(default=False)
    financiamiento = models.BooleanField(default=False)
    financiamiento_nombre = models.CharField(max_length=255, blank=True, null=True)
    tipo_inmueble = models.ForeignKey(TipoInmueble, on_delete=models.PROTECT)
    ingresos_mensuales = models.PositiveBigIntegerField()
    egresos_mensuales = models.PositiveBigIntegerField()
    ganancias_mensuales = models.PositiveBigIntegerField()

    # Bloque 3: Conectividad
    internet = models.BooleanField(default=False)
    tipo_internet = models.ForeignKey(TipoInternet, on_delete=models.PROTECT)
    dispositivos_conectados = models.PositiveBigIntegerField()
    computadora = models.BooleanField(default=False)
    tipo_dispositivos_moviles = models.ManyToManyField(TipoDispositivosMoviles)
    plataforma_comunicacion = models.ManyToManyField(PlataformaComunicacion)
    redes_sociales = models.BooleanField(default=False)
    redes_sociales_cuales = models.ManyToManyField(RedSocial)

    # Bloque 4: Comercializacion
    comprador = models.ForeignKey(Comprador, on_delete=models.PROTECT)
    cantidad_clientes = models.ForeignKey(CantidadClientes, on_delete=models.PROTECT)
    lugar_comercializacion = models.ForeignKey(
        LugarComercializacion, on_delete=models.PROTECT
    )
    modalidad_comercializacion = models.ForeignKey(
        ModalidadComercializacion, on_delete=models.PROTECT
    )
    fijacion_precios = models.ForeignKey(FijacionPrecios, on_delete=models.PROTECT)
    cantidad_competidores = models.ForeignKey(
        CantidadCompetidores, on_delete=models.PROTECT
    )
    conocimiento_competidores = models.ForeignKey(
        ConocimientoCompetidores, on_delete=models.PROTECT
    )
    interactua_compentidores = models.ForeignKey(
        InteractuaCompetidores, on_delete=models.PROTECT
    )
    modalidad_compras = models.ForeignKey(ModalidadCompras, on_delete=models.PROTECT)
    plazo_compra_credito = models.ForeignKey(
        PlazoCompraCredito, on_delete=models.PROTECT
    )
    medio_planificacion = models.ForeignKey(
        MedioPlanificacion, on_delete=models.PROTECT
    )
    canales_ventas = models.ManyToManyField(CanalesVentas)

    # Bloque 5: Economia circular
    recicladores = models.BooleanField(default=False)
    recicladores_buena_condicion = models.BooleanField(default=False)
    clasificacion_residuos = models.BooleanField(default=False)
    destino_materiales_recuperados = models.ForeignKey(
        DestinoMaterialesRecuperados, on_delete=models.PROTECT
    )
    reduccion_residuos = models.BooleanField(default=False)
    modalidad_ciclo_productivo = models.ForeignKey(
        ModalidadCicloProductivo, on_delete=models.PROTECT
    )
    financiamiento_sostenible = models.BooleanField(default=False)
    estrategias_comercializacion = models.BooleanField(default=False)
    tecnologias_mejorar_eficiencia = models.BooleanField(default=False)
    tecnologias_mejorar_eficiencia_cuales = models.CharField(max_length=255)


class AnexoSocioProductivo(models.Model):
    fecha_creacion = models.DateTimeField(auto_now=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    creador = models.ForeignKey(
        Usuarios, on_delete=models.PROTECT, related_name="creador"
    )
    modificador = models.ForeignKey(
        Usuarios,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="modificador",
    )
    estado = models.ForeignKey(EstadoSolicitud, on_delete=models.PROTECT)

    PERSONERIA_CHOICES = (("ORGANIZACION", "Organización"), ("PERSONA", "Persona"))
    personeria = models.CharField(max_length=255, choices=PERSONERIA_CHOICES)
    organizacion = models.ForeignKey(Organizacion, on_delete=models.PROTECT)
    persona = models.ForeignKey(Persona, on_delete=models.PROTECT)

    linea_de_accion = models.ForeignKey(LineaDeAccion, on_delete=models.PROTECT)

    media = models.FileField(upload_to="anexos/socioproductivos/")

    diagnostico_organizacion = models.ForeignKey(
        DiagnosticoOrganizacion, on_delete=models.PROTECT
    )
    diagnostico_persona = models.ForeignKey(
        DiagnosticoPersona, on_delete=models.PROTECT
    )

    def clean(self):
        if (self.personeria == "ORGANIZACION" and not self.organizacion) or (
            self.personeria == "PERSONA" and not self.persona
        ):
            raise ValidationError(
                "Debe completar una organización o una persona para el anexo."
            )

        if (
            self.personeria == "ORGANIZACION" and not self.diagnostico_organizacion
        ) or (self.personeria == "PERSONA" and not self.diagnostico_persona):
            raise ValidationError("Debe completar una el diagnostico para el anexo.")

        return super().clean()

    def save(self, *args, **kwargs):
        self.fecha_ultima_modificacion = timezone.now()
        if "usuario" in kwargs:  # Define el modificador si es pasado como argumento
            self.modificador = kwargs.pop("usuario")
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Anexo socio productivo"
        verbose_name_plural = "Anexos socio productivo"
