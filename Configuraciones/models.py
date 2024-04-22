from django.db import models
from .choices import *
from django.urls import *
from Usuarios.models import User, Usuarios
from django.core.validators import MinValueValidator, MaxValueValidator

# -------------------------------CONFIGURACIONES GENERALES (se usan en todo el proyecto)--------------------------------------


class Secretarias(models.Model):
    nombre = models.CharField(max_length=40, unique=True)
    observaciones = models.CharField(max_length=300, null=True, blank=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    def clean(self):
        self.nombre = self.nombre.capitalize()

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Secretaría'
        verbose_name_plural = "Secretarías"

    def get_absolute_url(self):
        return reverse('secretarias_ver', kwargs={'pk': self.pk})


class Subsecretarias(models.Model):
    fk_secretaria = models.ForeignKey(Secretarias, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=40, unique=True)
    observaciones = models.CharField(
        max_length=300,
        null=True,
        blank=True,
    )
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    def clean(self):
        self.nombre = self.nombre.capitalize()

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Subsecretaría'
        verbose_name_plural = "Subecretarías"

    def get_absolute_url(self):
        return reverse('subsecretarias_ver', kwargs={'pk': self.pk})


class Programas(models.Model):
    fk_subsecretaria = models.ForeignKey(Subsecretarias, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100, unique=True)
    estado = models.BooleanField(default=True)
    observaciones = models.CharField(max_length=300, null=True, blank=True)

    def __str__(self):
        return self.nombre

    def clean(self):
        self.nombre = self.nombre.capitalize()

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Programa'
        verbose_name_plural = "Programas"

    def get_absolute_url(self):
        return reverse('programas_ver', kwargs={'pk': self.pk})


class Organismos(models.Model):
    nombre = models.CharField(max_length=250, unique=True)
    tipo = models.CharField(max_length=50, choices=CHOICE_TIPO_ORGANISMO)
    calle = models.CharField(max_length=250, null=True, blank=True)
    altura = models.IntegerField(null=True, blank=True)
    piso = models.CharField(max_length=100, null=True, blank=True)
    barrio = models.CharField(max_length=250, choices=CHOICE_BARRIOS, null=True, blank=True)
    localidad = models.CharField(max_length=250, choices=CHOICE_LOCALIDAD, null=True, blank=True)
    telefono = models.IntegerField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    estado = models.BooleanField(default=True)
    observaciones = models.CharField(max_length=300, null=True, blank=True)

    def __str__(self):
        return self.nombre

    def clean(self):
        self.nombre = self.nombre.capitalize()

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Organismo'
        verbose_name_plural = "Organismos"

    def get_absolute_url(self):
        return reverse('organismos_ver', kwargs={'pk': self.pk})


class PlanesSociales(models.Model):
    nombre = models.CharField(max_length=250, unique=True)
    jurisdiccion = models.CharField(max_length=50, choices=CHOICE_JURISDICCION)
    estado = models.BooleanField(default=True)
    observaciones = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.nombre

    def clean(self):
        self.nombre = self.nombre.capitalize()

    class Meta:
        ordering = ['nombre']
        verbose_name = 'PlanSocial'
        verbose_name_plural = "PlanesSociales"

    def get_absolute_url(self):
        return reverse('planes_sociales_ver', kwargs={'pk': self.pk})


class AgentesExternos(models.Model):
    '''
    Agentes Externos para posteriores uso en envio de mails, alertas, etc.
    '''

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    fk_organismo = models.ForeignKey(Organismos, on_delete=models.CASCADE, null=True, blank=True)
    rol = models.CharField(
        max_length=30,
        null=True,
        blank=True,
    )
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f" {self.nombre} {self.apellido}"

    def clean(self):
        self.nombre = self.nombre.capitalize()
        self.apellido = self.apellido.capitalize()

    class Meta:
        ordering = ['apellido']
        verbose_name = 'Agente Externo'
        verbose_name_plural = "Agentes Externos"

    def get_absolute_url(self):
        return reverse('agentesexternos_ver', kwargs={'pk': self.pk})


# TODO En la vista o en el form, validar que no se pueda guardar el grupo vacío: o tiene al menos un destinatario o usuario
class GruposDestinatarios(models.Model):
    '''
    Grupos de Destinatarios, que puede contener tanto destinatarios externos (mail) como User del sistema.
    La finalidad es su uso en envio de mails, alertas, etc.
    '''

    nombre = models.CharField(max_length=250)
    m2m_agentes_externos = models.ManyToManyField(
        AgentesExternos,
        blank=True,
    )
    m2m_usuarios = models.ManyToManyField(Usuarios, blank=True)
    observaciones = models.CharField(max_length=500, null=True, blank=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    def clean(self):
        self.nombre = self.nombre.capitalize()

    class Meta:
        ordering = ['nombre']
        verbose_name = 'GrupoDestinatarios'
        verbose_name_plural = "GruposDestinatarios"

    def get_absolute_url(self):
        return reverse('gruposdestinatarios_ver', kwargs={'pk': self.pk})


class Equipos(models.Model):
    '''
    Equipos de trabajo, compuesto de User del sistema.
    La finalidad es su uso en cada programa.
    '''

    fk_programa = models.ForeignKey(Programas, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=250)
    fk_coordinador = models.ForeignKey(
        Usuarios,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="fkcoordinador",
    )
    m2m_usuarios = models.ManyToManyField(Usuarios)
    observaciones = models.CharField(max_length=500, null=True, blank=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    def clean(self):
        self.nombre = self.nombre.capitalize()

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Equipo'
        verbose_name_plural = "Equipos"

    def get_absolute_url(self):
        return reverse('equipos_ver', kwargs={'pk': self.pk})


class CategoriaAlertas(models.Model):
    '''
    Descripciones cortas que agrupan distintos tipos de alertas de vulnerabilidad.
    '''

    nombre = models.CharField(max_length=100, unique=True)
    dimension = models.CharField(max_length=20, choices=CHOICE_DIMENSIONES, null=True, blank=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    def clean(self):
        self.nombre = self.nombre.capitalize()

    class Meta:
        ordering = ['nombre']
        verbose_name = 'CategoriaAlertas'
        verbose_name_plural = 'CategoriasAlertas'

    def get_absolute_url(self):
        return reverse('categoriaalertas_ver', kwargs={'pk': self.pk})


class Alertas(models.Model):
    '''
    Indicadores de vulnerabilidad, relacionados a una categoría específica a traves de una FK.
    '''

    nombre = models.CharField(max_length=100, unique=True)
    fk_categoria = models.ForeignKey(CategoriaAlertas, on_delete=models.CASCADE)
    estado = models.BooleanField(default=True)
    gravedad = models.CharField(max_length=500, null=False, blank=False)

    def __str__(self):
        return self.nombre

    def clean(self):
        self.nombre = self.nombre.capitalize()

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Alerta'
        verbose_name_plural = 'Alertas'

    def get_absolute_url(self):
        return reverse('alertas_ver', kwargs={'pk': self.pk})


class Sujetos(models.Model):
    '''
    Sujetos hacia quienes se aplicara, posteriormente, un criterio de vulnerabilidad. Por ejemplo: Embarazadas, Madres
    o Cuidadores principales, bebés, adolescentes, etc.
    '''

    nombre = models.CharField(max_length=70, unique=True)

    def __str__(self):
        return self.nombre

    def clean(self):
        self.nombre = self.nombre.capitalize()

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Sujetos'
        verbose_name_plural = "Sujetos"

    def get_absolute_url(self):
        return reverse('sujetos_ver', kwargs={'pk': self.pk})


# region ------- INDICES DE VULNERABILIDAD (para crear indices como el IVI/IVIJ/RAIJ y otros)----------------------
class Acciones(models.Model):
    '''
    Acciones a desarrollar apuntando a revertir un determinado criterio.
    '''

    nombre = models.CharField(max_length=70, unique=True)
    dimension = models.CharField(max_length=12, choices=CHOICE_DIMENSIONES, default='Desconocida')
    observaciones = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.nombre

    def clean(self):
        self.nombre = self.nombre.capitalize()

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Acciones'
        verbose_name_plural = "Acciones"

    def get_absolute_url(self):
        return reverse('acciones_ver', kwargs={'pk': self.pk})


class Criterios(models.Model):
    '''
    Criterios de vulnerabilidad que seran posteriormente utilizados en la conformacion de INDICES (Ej. IVI).
    '''

    nombre = models.CharField(max_length=250, unique=True)
    dimension = models.CharField(max_length=12, choices=CHOICE_DIMENSIONES, default='Desconocida')
    fk_sujeto = models.ForeignKey(Sujetos, on_delete=models.CASCADE)
    permite_potencial = models.BooleanField(default=False)
    m2m_acciones = models.ManyToManyField(Acciones, blank=True)
    m2m_alertas = models.ManyToManyField(CategoriaAlertas, blank=True)
    estado = models.BooleanField(default=True)
    observaciones = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.nombre

    def clean(self):
        self.nombre = self.nombre.capitalize()

    class Meta:
        ordering = ['fk_sujeto']
        verbose_name = 'Criterio'
        verbose_name_plural = "Criterios"

    def get_absolute_url(self):
        return reverse('criterios_ver', kwargs={'pk': self.pk})


class Indices(models.Model):
    '''
    **INDICES DE VULNERABILIDAD**
    Agrupan determinados criterios y les asigna a cada uno un puntaje válido para la instancia de Indice que se está generando.
    '''

    nombre = models.CharField(max_length=250, unique=True)
    m2m_criterios = models.ManyToManyField(Criterios, through='IndiceCriterios')
    m2m_programas = models.ManyToManyField(Programas)
    observaciones = models.CharField(max_length=500, null=True, blank=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Indice'
        verbose_name_plural = 'Indices'

    def get_absolute_url(self):
        return reverse('indices_ver', kwargs={'pk': self.pk})


class IndiceCriterios(models.Model):
    '''
    Tabla puente 'IndiceCriterios' que agrega un puntaje base a cada criterio para la instancia de índice actual,
    acorde a las necesidades que cada servicio/programa requiera.
    '''

    fk_criterio = models.ForeignKey(Criterios, on_delete=models.CASCADE, related_name='fkcriterio')
    fk_indice = models.ForeignKey(Indices, on_delete=models.CASCADE, related_name='fkindice')
    puntaje_base = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text='Permite valores entre 0 y 10.',
    )

    def __str__(self):
        return f'{self.puntaje_base}'

    class Meta:
        verbose_name = 'IndiceCriterios'
        verbose_name_plural = 'IndicesCriterios'

    def get_absolute_url(self):
        return reverse('indicecriterios_ver', kwargs={'pk': self.pk})
    
class Vacantes(models.Model):
    nombre = models.CharField(max_length=100)
    observaciones = models.CharField(max_length=300, null=True, blank=True)
    fk_programa = models.ForeignKey(Programas, on_delete=models.CASCADE)
    fk_organismo = models.ForeignKey(Organismos, on_delete=models.CASCADE, null=True, blank=True)
    manianabb = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=0, verbose_name = 'Turno Mañana', 
    )
    tardebb = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=0,verbose_name = 'Turno Tarde',
    )
    maniana2 = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=0,verbose_name = 'Turno Mañana',
    )
    tarde2 = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=0,verbose_name = 'Turno Tarde',
    )
    maniana3 = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=0, verbose_name = 'Turno Mañana',
    )
    tarde3 = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=0,verbose_name = 'Turno Tarde',
    )
    maniana4 = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=0, verbose_name = 'Turno Mañana',
    )
    tarde4 = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=0,verbose_name = 'Turno Tarde',
    )
    estado = models.BooleanField(default=True)


    def __str__(self):
        return self.nombre

    def clean(self):
        self.nombre = self.nombre.capitalize()

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Vacante'
        verbose_name_plural = "Vacantes"

    def get_absolute_url(self):
        return reverse('vacantes_ver', kwargs={'pk': self.pk})


# endregion ---------------------FIN INDICES DE VULNERABILIDAD---------------------------------------------------


# region ----------------------------- FORMULARIOS---------------------------------------------------------------
# Esta funcionalidad de crear formularios para nuevos programas quedo postergada, dejo el codigo comentado, que estaba a medio desarrollar


# class Opciones(models.Model):
#     '''
#     Permite conjunto de opciones persistidas para ser usadas en distintos modelos.
#     '''

#     opcion = models.CharField(max_length=50, unique=True)

#     def __str__(self):
#         return self.opcion

#     class Meta:
#         verbose_name = 'Opción'
#         verbose_name_plural = "Opciones"

#     def get_absolute_url(self):
#         return reverse('opciones_ver', kwargs={'pk': self.pk})


# class TipoOpciones(models.Model):
#     '''
#     Permite conjunto de opciones persistidas para ser usadas en distintos modelos.
#     '''

#     nombre = models.CharField(max_length=50, unique=True)
#     opcion = models.ManyToManyField(Opciones)

#     def __str__(self):
#         return self.nombre

#     class Meta:
#         ordering = ['nombre']
#         verbose_name = 'TipoOpciones'
#         verbose_name_plural = "TipoOpciones"

#     def get_absolute_url(self):
#         return reverse('tipoopciones_ver', kwargs={'pk': self.pk})


# class Items(models.Model):
#     '''
#     Preguntas persistidas para ser usadas en distintos formularios.
#     '''

#     descripcion = models.CharField(max_length=200)
#     dimension = models.CharField(max_length=70, choices=CHOICE_DIMENSIONES)
#     tipo_dato = models.CharField(max_length=50, choices=CHOICE_TIPO_DE_DATOS)
#     visible_en_legajo = models.BooleanField(default=False)
#     opciones = models.ForeignKey(TipoOpciones, on_delete=models.CASCADE, blank=True, null=True)
#     fk_sujeto = models.ForeignKey(Sujetos, on_delete=models.CASCADE)

#     def __str__(self):
#         return self.descripcion

#     class Meta:
#         ordering = ['dimension']
#         verbose_name = 'Item'
#         verbose_name_plural = "Items"

#     def get_absolute_url(self):
#         return reverse('items_ver', kwargs={'pk': self.pk})


# class Formularios(models.Model):
#     '''
#     Permite Formularios persistidos para ser usados en distintos instancias.
#     '''

#     programa = models.ForeignKey(Programas, on_delete=models.CASCADE)
#     tipo = models.CharField(max_length=50, choices=CHOICE_TIPO_DE_FORMULARIO)
#     m2m_items = models.ManyToManyField(Items)

#     def __str__(self):
#         return f'{self.programa} - {self.tipo}'

#     class Meta:
#         ordering = ['programa']
#         verbose_name = 'Formulario'
#         verbose_name_plural = "Formularios"

#     def get_absolute_url(self):
#         return reverse('formularios_ver', kwargs={'pk': self.pk})


# # endregion ---------------------FIN INDICES DE VULNERABILIDAD---------------------------------------------------
