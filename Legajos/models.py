from datetime import date
from datetime import timedelta
from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from Legajos.choices import *
from Usuarios.models import Usuarios
from Configuraciones.models import *
from multiselectfield import MultiSelectField


class Legajos(models.Model):
    '''

    Guardado de los perfiles de las personas con las que interviene el Municipio.
    '''

    apellido = models.CharField(max_length=250)
    nombre = models.CharField(max_length=250)
    fecha_nacimiento = models.DateField()
    tipo_doc = models.CharField(max_length=50, choices=CHOICE_TIPO_DOC,
                                verbose_name="Tipo documento", null=True, blank=True)
    documento = models.PositiveIntegerField(validators=[MinValueValidator(
        3000000), MaxValueValidator(100000000)], null=True, blank=True)
    sexo = models.CharField(max_length=50, choices=CHOICE_SEXO)
    nacionalidad = models.CharField(
        max_length=50, choices=CHOICE_NACIONALIDAD, null=True, blank=True)
    estado_civil = models.CharField(
        max_length=50, choices=CHOICE_ESTADO_CIVIL, null=True, blank=True)
    Provincia = models.CharField(
        verbose_name='Provincia', max_length=200, choices=PROVINCE_CHOICES, null=True, blank=True)
    calle = models.CharField(max_length=250, null=True, blank=True)
    altura = models.IntegerField(null=True, blank=True)
    latitud = models.CharField(max_length=250, null=True, blank=True)
    longitud = models.CharField(max_length=250, null=True, blank=True)
    pisodpto = models.CharField(
        max_length=100, null=True, blank=True, verbose_name='Piso/Dpto (optativo)')
    circuito = models.CharField(
        max_length=100, choices=CHOICE_CIRCUITOS, null=True, blank=True)
    barrio = models.CharField(
        max_length=100, choices=CHOICE_BARRIOS, null=True, blank=True)
    torrepasillo = models.CharField(
        max_length=100, null=True, blank=True, verbose_name='Torre / Pasillo (optativo)')
    escaleramanzana = models.CharField(
        max_length=100, null=True, blank=True, verbose_name='Escalera / Manzana (optativo)')
    localidad = models.CharField(
        max_length=250, choices=CHOICE_LOCALIDAD, null=True, blank=True)
    codigopostal = models.IntegerField(
        null=True, blank=True, verbose_name='Código Postal')
    telefono = models.IntegerField(null=True, blank=True)
    telefonoalt = models.IntegerField(
        null=True, blank=True, verbose_name='Telefono Alternativo')
    email = models.EmailField(null=True, blank=True)
    foto = models.ImageField(upload_to='legajos', blank=True, null=True)
    m2m_alertas = models.ManyToManyField(
        Alertas, through='LegajoAlertas', blank=True)
    m2m_familiares = models.ManyToManyField(
        'self', through='LegajoGrupoFamiliar', symmetrical=True, blank=True)
    observaciones = models.CharField(
        max_length=300, blank=True, null=True, verbose_name='Observaciones (optativo)')
    estado = models.BooleanField(default=True)
    creado_por = models.ForeignKey(
        Usuarios, related_name='creado_por', on_delete=models.CASCADE, blank=True, null=True)
    modificado_por = models.ForeignKey(
        Usuarios, related_name='modificado_por', on_delete=models.CASCADE, blank=True, null=True)
    creado = models.DateField(auto_now_add=True)
    modificado = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"

    def validate_unique(self, exclude=None):
        qs = Legajos.objects.filter(tipo_doc=self.tipo_doc, documento=self.documento,
                                    apellido=self.apellido, nombre=self.nombre, fecha_nacimiento=self.fecha_nacimiento)

        if self.pk:
            qs = qs.exclude(pk=self.pk)

        if qs.exists():
            raise ValidationError(
                'Ya existe un legajo con ese TIPO y NÚMERO de documento.')

    def clean(self):
        # Separar y capitalizar las palabras en el campo "apellido"
        self.apellido = ' '.join(word.title()
                                 for word in self.apellido.split())
        # Separar y capitalizar las palabras en el campo "nombre"
        self.nombre = ' '.join(word.title() for word in self.nombre.split())

        if self.calle:
            self.calle = self.calle.capitalize()

        if self.fecha_nacimiento and self.fecha_nacimiento > date.today():
            raise ValidationError(
                'La fecha de nacimiento debe ser menor o igual a la fecha actual.')

    def edad(self):
        today = date.today()

        if self.fecha_nacimiento:
            age = today.year - self.fecha_nacimiento.year
            if today.month < self.fecha_nacimiento.month or (today.month == self.fecha_nacimiento.month and today.day < self.fecha_nacimiento.day):
                age -= 1

            if age == 0:
                # Calcular la cantidad de meses entre las fechas
                months = (today.year - self.fecha_nacimiento.year) * \
                    12 + today.month - self.fecha_nacimiento.month
                if months == 0:
                    # Calcular la cantidad de días entre las fechas
                    days = (today - self.fecha_nacimiento).days
                    return f"{days} días"
                return f"{months} meses"
            return f"{age}"

        return '-'

    class Meta:
        unique_together = ['tipo_doc', 'documento']
        ordering = ['apellido']
        verbose_name = 'Legajo'
        verbose_name_plural = 'Legajos'

    def get_absolute_url(self):
        return reverse('legajos_ver', kwargs={'pk': self.pk})


# TODO realizar en las vistas una validación cuando haya una relación importante de aclarar (ej. perimetral, violencia) obligatorio el campo obs para describirla


class LegajoGrupoFamiliar(models.Model):
    '''

    Guardado de las relaciones familiares de los vecinos y vecinas registrados, con una valoración que permita conocer el estado

    del vínculo desde la consideración de cada parte involucrada.
    '''

    fk_legajo_1 = models.ForeignKey(
        Legajos, related_name='fk_legajo1', on_delete=models.CASCADE)
    fk_legajo_2 = models.ForeignKey(
        Legajos, related_name='fk_legajo2', on_delete=models.CASCADE)
    vinculo = models.CharField(max_length=50, choices=CHOICE_VINCULO_FAMILIAR)
    vinculo_inverso = models.CharField(max_length=50, null=True, blank=True)
    estado_relacion = models.CharField(
        max_length=50, choices=CHOICE_ESTADO_RELACION)
    conviven = models.CharField(max_length=50, choices=CHOICE_SINO)
    cuidador_principal = models.CharField(max_length=50, choices=CHOICE_SINO)
    observaciones = models.CharField(max_length=300, null=True, blank=True)

    def __str__(self):
        return f"Legajo: {self.fk_legajo_1} - Familiar: {self.fk_legajo_2} - Vínculo: {self.vinculo}"

    class Meta:
        ordering = ['fk_legajo_2']
        unique_together = ['fk_legajo_1', 'fk_legajo_2']
        verbose_name = 'LegajoGrupoFamiliar'
        verbose_name_plural = 'LegajosGrupoFamiliar'

    def get_absolute_url(self):
        return reverse('legajogrupofamiliar_ver', kwargs={'pk': self.pk})


# region------------- DIMENSIONES--------------------------------------------------------------------------------------------------


class DimensionFamilia(models.Model):
    '''

    Guardado de la informacion de salud asociada a un Legajo.
    '''

    fk_legajo = models.OneToOneField(Legajos, on_delete=models.CASCADE)
    estado_civil = models.CharField(
        max_length=50, choices=CHOICE_ESTADO_CIVIL, null=True, blank=True)
    cant_hijos = models.SmallIntegerField(
        verbose_name='Cantidad de hijos', null=True, blank=True)
    otro_responsable = models.BooleanField(
        verbose_name='¿Hay otro adulto responsable? (Padre o apoyo en la crianza)', null=True, blank=True)
    hay_embarazadas = models.BooleanField(
        verbose_name='Personas en el hogar embarazadas', null=True, blank=True)
    hay_prbl_smental = models.BooleanField(
        verbose_name='Personas en el hogar con problemas de salud mental', null=True, blank=True)
    hay_fam_discapacidad = models.BooleanField(
        verbose_name='Personas en el hogar con discapacidad', null=True, blank=True)
    hay_enf_cronica = models.BooleanField(
        verbose_name='Personas en el hogar con enfermedades crónicas', null=True, blank=True)
    hay_priv_libertad = models.BooleanField(
        verbose_name='Personas en el hogar privados de su libertad', null=True, blank=True)
    obs_familia = models.CharField(
        verbose_name='Observaciones', max_length=300, null=True, blank=True)
    creado = models.DateField(auto_now_add=True)
    modificado = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.fk_legajo}"

    class Meta:
        ordering = ['fk_legajo']
        verbose_name = 'DimensionFamilia'
        verbose_name_plural = 'DimensionesFamilia'

    def get_absolute_url(self):
        return reverse('legajos_ver', kwargs={'pk': self.fk_legajo.id})


class DimensionVivienda(models.Model):
    '''
    Guardado de los datos de vivienda asociados a un Legajo.
    '''
    fk_legajo = models.OneToOneField(Legajos, on_delete=models.CASCADE)
    tipo = models.CharField(verbose_name='Dirías que tu vivienda es…  ', max_length=50,
                            choices=CHOICE_TIPO_VIVIENDA, null=True, blank=True)
    material = models.CharField(verbose_name='Material principal de la vivienda',
                                max_length=50, choices=CHOICE_TIPO_CONSTRUCCION_VIVIENDA, null=True, blank=True)
    pisos = models.CharField(verbose_name='Material principal de los pisos',
                             max_length=50, choices=CHOICE_TIPO_PISOS_VIVIENDA, null=True, blank=True)
    posesion = models.CharField(verbose_name='Tipo de posesión',
                                max_length=50, choices=CHOICE_CondicionDe, null=True, blank=True)
    cant_ambientes = models.SmallIntegerField(
        verbose_name='¿Cuántos ambientes tiene la vivienda? (Sin contar baño ni cocina)',choices=CHOICE_CantidadAmbientes, null=True, blank=True)
    cant_convivientes = models.SmallIntegerField(
        verbose_name='¿Cuántas personas viven en la vivienda?', null=True, blank=True)
    cant_menores = models.SmallIntegerField(
        verbose_name='¿Cuántos de ellos son menores de 18 años?', null=True, blank=True)
    cant_camas = models.SmallIntegerField(
        verbose_name='¿Cuántas camas/ colchones posee?', null=True, blank=True)
    cant_hogares = models.SmallIntegerField(
        verbose_name='¿Cuantos hogares hay en la vivienda?', null=True, blank=True)
    hay_agua_caliente = models.CharField(
        verbose_name='¿Posee Agua caliente?',max_length=50, choices=CHOICE_SINO, null=True, blank=True)
    hay_banio = models.CharField(verbose_name='El baño tiene… ',
                           max_length=50, choices=CHOICE_INODORO, null=True, blank=True)
    hay_desmoronamiento = models.CharField(
        verbose_name='Existe riesgo de desmoronamiento?',max_length=50, choices=CHOICE_SINO, null=True, blank=True)
    obs_vivienda = models.CharField(
        verbose_name='Observaciones', max_length=300, null=True, blank=True)
    creado = models.DateField(auto_now_add=True)
    modificado = models.DateField(auto_now=True)
    # Nuevos campos
    PoseenCeludar = models.CharField(
        verbose_name='¿En tu hogar cuentan con Teléfonos celulares?', max_length=255, choices=CHOICE_SINO, null=True, blank=True)
    PoseenPC = models.CharField(
        verbose_name='¿En tu hogar cuentan con Computadoras? (de escritorio / laptop / tablet) ', max_length=255, choices=CHOICE_SINO, null=True, blank=True)
    Poseeninternet = models.CharField(
        verbose_name='En tu hogar cuentan con Internet (a través del celular o por conexión en la vivienda - wifi)', max_length=255,choices=CHOICE_SINO, null=True, blank=True)
    ContextoCasa = models.CharField(verbose_name='La vivienda está ubicada...',
                                    max_length=255, choices=CHOICE_ContextoCasa, null=True, blank=True)
    gas = models.CharField(verbose_name='¿Qué utilizan principalmente para cocinar?',
                           max_length=50, choices=CHOICE_GAS, null=True, blank=True)
    techos = models.CharField(verbose_name='¿Cuál es el material predominante de la cubierta exterior del techo de la vivienda?',
                           max_length=50, choices=CHOICE_TIPO_TECHO_VIVIENDA, null=True, blank=True)
    agua = models.CharField(verbose_name='El agua que usan para beber y cocinar proviene de…',
                           max_length=50, choices=CHOICE_AGUA, null=True, blank=True)
    desague = models.CharField(verbose_name='El desagüe del inodoro es…',
                           max_length=50, choices=CHOICE_DESAGUE, null=True, blank=True)

    def __str__(self):
        return f"{self.fk_legajo}"

    class Meta:
        ordering = ['fk_legajo']
        verbose_name = 'DimensionVivienda'
        verbose_name_plural = 'DimensionesVivienda'

    def get_absolute_url(self):
        return reverse('legajos_ver', kwargs={'pk': self.fk_legajo.id})


class DimensionSalud(models.Model):
    '''

    Guardado de la informacion de salud asociada a un Legajo.
    '''

    fk_legajo = models.OneToOneField(Legajos, on_delete=models.CASCADE)
    lugares_atencion = models.CharField(verbose_name='Centro de Salud en donde se atiende',
                                        max_length=50, choices=CHOICE_CENTROS_SALUD, null=True, blank=True)
    frec_controles = models.CharField(verbose_name='¿Con qué frecuencia realiza controles médicos?',
                                      max_length=50, choices=CHOICE_FRECUENCIA, null=True, blank=True)
    hay_obra_social = models.BooleanField(
        verbose_name='¿Posee cobertura de salud?', null=True, blank=True)
    hay_enfermedad = models.BooleanField(
        verbose_name='¿Posee alguna enfermedad recurrente o crónica?', null=True, blank=True)
    hay_discapacidad = models.BooleanField(
        verbose_name='¿Posee alguna discapacidad?', null=True, blank=True)
    hay_cud = models.BooleanField(
        verbose_name='¿Posee certificado de discapacidad?', null=True, blank=True)
    obs_salud = models.CharField(
        verbose_name='Observaciones', max_length=300, null=True, blank=True)
    creado = models.DateField(auto_now_add=True)
    modificado = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.fk_legajo}"

    class Meta:
        ordering = ['fk_legajo']
        verbose_name = 'DimensionSalud'
        verbose_name_plural = 'DimensionesSalud'

    def get_absolute_url(self):
        return reverse('legajos_ver', kwargs={'pk': self.fk_legajo.id})





# Assuming your model class name is DimensionEducacion
class DimensionEducacion(models.Model):
    fk_legajo = models.OneToOneField(Legajos, on_delete=models.CASCADE)
    max_nivel = models.CharField(verbose_name='Máximo nivel educativo alcanzado',
                                 max_length=50, choices=CHOICE_NIVEL_EDUCATIVO, null=True, blank=True)
    estado_nivel = models.CharField(verbose_name='Estado del nivel', max_length=50,
                                    choices=CHOICE_ESTADO_NIVEL_EDUCATIVO, null=True, blank=True)
    asiste_escuela = models.CharField(verbose_name='¿Asistís o asististe alguna vez a algún establecimiento educativo?', max_length=100, choices= CHOICE_ASISTE_ESCUELA, null=True, blank=True)
    interesEstudio = models.CharField(
        verbose_name='¿Le interesa estudiar?',max_length=100, choices=CHOICE_SINO, null=True, blank=True)
    interesCurso = models.CharField(
        verbose_name='¿le interesa algun curso?', max_length=100, choices=CHOICE_SINO, null=True, blank=True)
    institucion = models.CharField(verbose_name='Escuela', max_length=200,
                                   choices=CHOICE_INSTITUCIONES_EDUCATIVAS, null=True, blank=True)
    gestion = models.CharField(verbose_name='Gestión', max_length=50,
                               choices=CHOICE_TIPO_GESTION, null=True, blank=True)
    ciclo = models.CharField(
        max_length=20, choices=CHOICE_NIVEL_EDUCATIVO, null=True, blank=True)
    grado = models.CharField(
        max_length=20, choices=CHOICE_GRADO, null=True, blank=True)
    turno = models.CharField(
        max_length=20, choices=CHOICE_TURNO, null=True, blank=True)
    obs_educacion = models.CharField(
        max_length=300, verbose_name='Observaciones', null=True, blank=True)
    creado = models.DateField(auto_now_add=True)
    modificado = models.DateField(auto_now=True)
    acepta_terminos = models.BooleanField(
        verbose_name='Acepto los términos y condiciones', default=False)
    # Nuevos campos dimencion estudio
    provinciaInstitucion = models.CharField(
        verbose_name='Provincia', max_length=200, choices=PROVINCE_CHOICES, null=True, blank=True)
    localidadInstitucion = models.CharField(
        verbose_name='Localidad', max_length=100, null=True, blank=True)
    municipioInstitucion = models.CharField(
        verbose_name='Municipio', max_length=100, null=True, blank=True)
    barrioInstitucion = models.CharField(
        verbose_name='Barrio', max_length=100, null=True, blank=True)
    calleInstitucion = models.CharField(
        verbose_name='Calle', max_length=255, null=True, blank=True)
    numeroInstitucion = models.CharField(
        verbose_name='Número', max_length=10, null=True, blank=True)
    nivelIncompleto = models.CharField(verbose_name='¿Cuál fue el motivo principal por el que no terminaste tus estudios?',
                                       max_length=79, choices=CHOICE_MOTIVO_NIVEL_INCOMPLETO, null=True, blank=True)
    sinEduFormal = models.CharField(verbose_name='¿Cuál fue el motivo principal por el que nunca asististe a un establecimiento educativo?',
                                    max_length=79, choices=CHOICE_MOTIVO_NIVEL_INCOMPLETO, null=True, blank=True)
    realizandoCurso = models.CharField(verbose_name='¿Actualmente te encontrás haciendo algún curso de capacitación?',
                                       max_length=20, choices=CHOICE_SINO, null=True, blank=True)
    areaCurso = MultiSelectField(choices=CHOICE_AREA_CURSO, verbose_name='¿En qué áreas?', max_length=200, null=True, blank=True)
    interesCapLab = models.CharField(verbose_name='¿Tenés interés en realizar cursos de capacitación laboral?',
                                     max_length=20, choices=CHOICE_SINO, null=True, blank=True)
    oficio = models.CharField(verbose_name='¿Tenés conocimiento de algún oficio?',
                              max_length=20, choices=CHOICE_SINO, null=True, blank=True)
    areaOficio = MultiSelectField(choices=CHOICE_AREA_CURSO, verbose_name='¿En qué áreas?', max_length=200, null=True, blank=True)

    def __str__(self):
        return f"{self.fk_legajo}"

    class Meta:
        ordering = ['fk_legajo']
        verbose_name = 'DimensionEducacion'
        verbose_name_plural = 'DimensionesEducacion'

    def get_absolute_url(self):
        return reverse('legajos_ver', kwargs={'pk': self.fk_legajo.id})
    

class DimensionEconomia(models.Model):
    '''

    Guardado de los datos económicos asociados a un Legajo.
    '''

    fk_legajo = models.OneToOneField(Legajos, on_delete=models.CASCADE)
    ingresos = models.PositiveIntegerField(null=True, blank=True)
    recibe_plan = models.CharField(
        verbose_name='¿Recibe planes sociales?', max_length=100, choices=CHOICE_SINO, null=True, blank=True)
    m2m_planes = models.ManyToManyField(PlanesSociales, blank=True)
    cant_aportantes = models.SmallIntegerField(
        verbose_name='¿Cuántos miembros reciben ingresos por plan social o aportan al grupo familiar?', null=True, blank=True)
    obs_economia = models.CharField(
        max_length=300, verbose_name='Observaciones', null=True, blank=True)
    creado = models.DateField(auto_now_add=True)
    modificado = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.fk_legajo}"

    class Meta:
        ordering = ['fk_legajo']
        verbose_name = 'DimensionEconomica'
        verbose_name_plural = 'DimensionesEconomicas'

    def get_absolute_url(self):
        return reverse('legajos_ver', kwargs={'pk': self.fk_legajo.id})


class DimensionTrabajo(models.Model):
    fk_legajo = models.OneToOneField(Legajos, on_delete=models.CASCADE)
    tiene_trabajo = models.CharField(
        verbose_name='¿Actualmente realizás alguna actividad laboral, productiva o comunitaria?', max_length=100, choices=CHOICE_SINO, null=True, blank=True)
    modo_contratacion = models.CharField(
        max_length=50, choices=CHOICE_MODO_CONTRATACION, null=True, blank=True)
    ocupacion = models.CharField(max_length=50, null=True, blank=True)
    conviviente_trabaja = models.CharField(
        verbose_name='¿Conviviente trabaja?',max_length=100, choices=CHOICE_SINO, null=True, blank=True)
    obs_trabajo = models.CharField(
        max_length=300, verbose_name='Observaciones', null=True, blank=True)
    creado = models.DateField(auto_now_add=True)
    modificado = models.DateField(auto_now=True)
    # NUEVOS CAMPOS DIMENSION TRABAJO
    horasSemanales = models.CharField(
        verbose_name='Considerando todas las actividades que realizás en una semana, por las que recibís algún pago, sea en dinero o en especie, ¿cuántas horas por semana trabajas habitualmente?',
        max_length=100, null=True, blank=True)
    actividadRealizadaComo = models.CharField(verbose_name='Esa actividad la realizás como…', max_length=100, choices=CHOICE_ACTIVIDAD_REALIZADA, null=True, blank=True)
    duracionTrabajo = models.CharField(verbose_name='¿Este trabajo es…', max_length=79, choices=CHOICE_DURACION_TRABAJO, null=True, blank=True)
    aportesJubilacion = models.CharField(verbose_name='Por ese trabajo, ¿te descuentan jubilación o aportas vos mismo?', max_length=79, choices=CHOICE_APORTES_JUBILACION, null=True, blank=True)
    TiempoBusquedaLaboral = models.CharField(verbose_name='¿Cuánto hace que buscás trabajo?', max_length=79, choices=CHOICE_TIEMPO_BUSQUEDA_LABORAL, null=True, blank=True)
    busquedaLaboral =models.CharField(verbose_name='¿Buscaste trabajo en los últimos 30 días?', max_length=20, choices=CHOICE_SINO, null=True, blank=True)
    noBusquedaLaboral = models.CharField(verbose_name='¿Por qué motivo no buscaste trabajo? (Indicá el motivo principal)', max_length=79, choices=CHOICE_NO_BUSQUEDA_LABORAL, null=True, blank=True)


    def __str__(self):
        return f"{self.fk_legajo}"

    class Meta:
        ordering = ['fk_legajo']
        verbose_name = 'DimensionLaboral'
        verbose_name_plural = 'DimensionesLaborales'

    def get_absolute_url(self):
        return reverse('dimensionlaboral_ver', kwargs={'pk': self.pk})


# endregion-------------FIN DIMENSIONES-------------------------------------------------------------------------------------------------


# region--------------LEGAJO - ALERTAS-----------------------------------------------------------------------------------------


# TODO impedir que se pueda cambiar el tipo de alerta una vez creada, para impedir errores de interpretacion en el historial


class LegajoAlertas(models.Model):
    '''

    Registro de Alertas de vulnerabilidad asociadas a un Legajo determinado Tanto el alta como la baja se guardan en un historial del alertas.
    '''

    fk_alerta = models.ForeignKey(
        Alertas, related_name='alerta', on_delete=models.CASCADE)
    fk_legajo = models.ForeignKey(
        Legajos, related_name='legajo_alerta', on_delete=models.CASCADE)
    fecha_inicio = models.DateField(auto_now=True)
    creada_por = models.ForeignKey(
        Usuarios, related_name='creada_por', on_delete=models.CASCADE, blank=True, null=True)
    observaciones = models.CharField(max_length=140, null=True, blank=True)

    def __str__(self):
        return f"'fk_alerta': {self.fk_alerta}, 'fk_legajo': {self.fk_legajo},  'observaciones': {self.observaciones}, 'fecha_inicio': {self.fecha_inicio}, 'creada_por':{self.creada_por}"

    class Meta:
        ordering = ['-fecha_inicio']
        unique_together = ['fk_legajo', 'fk_alerta']
        verbose_name = 'LegajoAlertas'
        verbose_name_plural = 'LegajosAlertas'

    def get_absolute_url(self):
        return reverse('legajoalertas_ver', kwargs={'pk': self.pk})


class HistorialLegajoAlertas(models.Model):
    '''
    Guardado de historial de los distintos movimientos (CREACION/ELIMINACION)  de alertas de vulnerabilidad asociadas a un Legajo.
    Se graban a traves funciones detalladas en el archivo signals.py de esta app.
    '''
    fk_alerta = models.ForeignKey(
        Alertas, related_name='hist_alerta', on_delete=models.CASCADE)
    fk_legajo = models.ForeignKey(
        Legajos, related_name='hist_legajo_alerta', on_delete=models.CASCADE)
    observaciones = models.CharField(max_length=140, null=True, blank=True)
    creada_por = models.ForeignKey(
        Usuarios, related_name='hist_creada_por', on_delete=models.CASCADE, blank=True, null=True)
    eliminada_por = models.ForeignKey(
        Usuarios, related_name='hist_eliminada_por', on_delete=models.CASCADE, blank=True, null=True)
    fecha_inicio = models.DateField(auto_now=True)
    fecha_fin = models.DateField(null=True, blank=True)
    # Campo para almacenar los meses en los que estuvo activa
    meses_activa = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.fk_alerta.fk_categoria.dimension

    # Método para calcular el estado (Activa o Inactiva) basado en la existencia de fecha_fin
    @property
    def estado(self):
        return "Activa" if self.fecha_fin is None else "Inactiva"

    class Meta:
        ordering = ['-fecha_inicio']
        verbose_name = 'HistorialLegajoAlertas'
        verbose_name_plural = 'HistorialesLegajoAlertas'


# endregion---------FIN LEGAJO ALERTAS---------------------------------------------------------------------------------------------


# region--------------LEGAJOS/INDICES DE VULNERABILIDAD-----------------------------------------------------------------------------


# TODO realizar la logica una funcion que ejecute la valoración en las vistas.

# Tiene que mostrar todos los criterios del indice, permitiendo al usuario marcar aquellos que estan presentes en ese caso

# y en aquellos que permiten la mejora del puntaje [permite_mejora=True] permitir agregar un valor.


# class HistorialLegajoIndices(models.Model):
    '''

    Guardado de historial de cada instancia de ejecucion de un índices de vulnerabilidad asociado a un Legajo.

    Con una función en las vistas se cargaran los campos:

    - [puntos_mejora] en cada criterio que el índice lo permita .

    - [observaciones]

    Una vez ejecutada esa función, debe retornar un [puntaje_total] resultante del [puntaje base] +/- [total puntos mejora]

    y una valoración automática del mismo que va en el campo [riesgo] (escala a definir).
    '''

    # fecha = models.DateField(auto_now_add=True)
    # fk_indice = models.ForeignKey(Indices, on_delete=models.CASCADE)
    # fk_legajo = models.ForeignKey(Legajos, on_delete=models.CASCADE)
    # criterios_presentes = models.ManyToManyField(IndiceCriterios, through='LegajoIndiceCriterio')
    # puntaje_total = models.PositiveSmallIntegerField(null=True, blank=True)
    # riesgo = models.CharField(max_length=10, choices=CHOICE_NIVEL, null=True)
    # observaciones = models.CharField(max_length=300, null=True, blank=True)

    # def __str__(self):
    #     return self.fk_legajo

    # class Meta:
    #     verbose_name = 'HistorialLegajoIndice'
    #     verbose_name_plural = 'HistorialesLegajoIndices'

    # def get_absolute_url(self):
    #     return reverse('historiallegajoindice_ver', kwargs={'pk': self.pk})


# class LegajoIndiceCriterio(models.Model):
#     '''

#     Guardado de los valores cargados en cada instancia de ejecución de un índice para un legajo determinado.
#     '''

#     fk_HistLegIndice = models.ForeignKey(HistorialLegajoIndices, related_name='+', on_delete=models.CASCADE)
#     fk_IndiceCriterio = models.ForeignKey(IndiceCriterios, related_name='+', on_delete=models.CASCADE)
#     puntos_mejora = models.PositiveSmallIntegerField(null=True, blank=True)

#     def __str__(self):
#         return f"Historial: {self.fk_HistLegIndice} - Criterio: {self.fk_IndiceCriterio}"

#     class Meta:
#         ordering = ['fk_HistLegIndice']
#         verbose_name = 'LegajoIndiceCriterio'
#         verbose_name_plural = 'LegajoIndicesCriterios'

#     def get_absolute_url(self):
#         return reverse('legajoindicecriterio_ver', kwargs={'pk': self.pk})


# endregion-----------FIN LEGAJOS/ INDICES DE VULNERABILIDAD-------------------------------------------------------------------------


# region--------------LEGAJOS/DERIVACIONES---------------------------------------------------------------------------------------


class LegajosDerivaciones(models.Model):
    '''

    Registro de todas las derivaciones a programas que funcionen dentro del sistema.
    '''

    fk_legajo = models.ForeignKey(Legajos, on_delete=models.CASCADE)
    fk_programa_solicitante = models.ForeignKey(
        Programas, related_name='programa_solicitante', on_delete=models.CASCADE)
    fk_programa = models.ForeignKey(
        Programas, related_name='programa_derivado', on_delete=models.CASCADE)
    fk_organismo = models.ForeignKey(
        Organismos, on_delete=models.CASCADE, null=True, blank=True)
    detalles = models.CharField(max_length=500, null=True, blank=True)
    fk_usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    importancia = models.CharField(
        max_length=15, choices=CHOICE_IMPORTANCIA, default="Alta")
    estado = models.CharField(
        max_length=15, choices=CHOICE_ESTADO_DERIVACION, default="Pendiente")
    m2m_alertas = models.ManyToManyField(CategoriaAlertas, blank=True)
    archivos = models.FileField(
        upload_to='legajos/archivos', null=True, blank=True)
    motivo_rechazo = models.CharField(max_length=150, choices=CHOICE_RECHAZO)
    obs_rechazo = models.CharField(max_length=350, null=True, blank=True)
    fecha_rechazo = models.DateField(null=True, blank=True)
    fecha_creado = models.DateField(auto_now_add=True, null=True, blank=True)
    fecha_modificado = models.DateField(auto_now=True)

    def __str__(self):
        return self.fk_legajo.apellido + ', ' + self.fk_legajo.nombre

    class Meta:
        ordering = ['-fecha_creado']
        verbose_name = 'LegajoDerivacion'
        verbose_name_plural = 'LegajosDerivaciones'

    def get_absolute_url(self):
        return reverse('legajosderivaciones_ver', kwargs={'pk': self.pk})


# endregion


class LegajosArchivos(models.Model):

    """

    Archivos asociados a un legajo. En la view se separaran los archivos de imagen de los documentos (para mostrar los primeros enun carousel)

    """

    fk_legajo = models.ForeignKey(Legajos, on_delete=models.CASCADE)
    archivo = models.FileField(upload_to='legajos/archivos/')
    fecha = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=12)

    def __str__(self):
        return f"Archivo {self.id} del legajo {self.fk_legajo}"


##################### HOGAR###############################
class LegajoGrupoHogar(models.Model):
    '''
    Guardado de las relaciones familiares de los vecinos y vecinas registrados,
    con una valoración que permita conocer el estado del vínculo desde la
    consideración de cada parte involucrada.
    '''

    fk_legajo_1Hogar = models.ForeignKey(
        Legajos, on_delete=models.CASCADE, related_name='hogar_1')
    fk_legajo_2Hogar = models.ForeignKey(
        Legajos, on_delete=models.CASCADE, related_name='hogar_2')
    estado_relacion = models.CharField(
        max_length=50, choices=CHOICE_ESTADO_RELACION)

    def __str__(self):
        return f"Legajo: {self.fk_legajo_1Hogar} - Hogar: {self.fk_legajo_2Hogar}"

    class Meta:
        ordering = ['fk_legajo_2Hogar']
        verbose_name = 'LegajoGrupoHogarForm'
        verbose_name_plural = 'LegajoGrupoHogarForm'

    def get_absolute_url(self):
        return reverse('LegajoGrupoHogarForm_ver', kwargs={'pk': self.pk})

    ##########
