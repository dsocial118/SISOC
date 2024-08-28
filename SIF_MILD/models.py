from django.db import models
from Configuraciones.models import *
from Legajos.models import *
from django.core.validators import MinValueValidator, MaxValueValidator
from .choices import *
from django.urls import *
from SIF_CDIF.models import Criterios_IVI

# Create your models here.

# class legajo_MILD (models.Model):
#    fk_programa = models.ForeignKey(Programas, on_delete=models.CASCADE)
#    fk_legajo = models.ForeignKey(Legajos, on_delete=models.CASCADE)
#    nombre = models.CharField(max_length=100, unique=True)
#    estado = models.BooleanField(default=True)
#    observaciones = models.CharField(max_length=300, null=True, blank=True)
#    #creado_por = models.ForeignKey(Usuarios, related_name='MILD_creado_por', on_delete=models.CASCADE, blank=True, null=True)
#    #modificado_por = models.ForeignKey(Usuarios, related_name='MILD_modificado_por', on_delete=models.CASCADE, blank=True, null=True)
#    creado = models.DateField(auto_now_add=True)
#    modificado = models.DateField(auto_now=True)
#
#    def __str__(self):
#        return self.nombre
#
#    def clean(self):
#        self.nombre = self.nombre.capitalize()
#
#    class Meta:
#        ordering = ['nombre']
#        verbose_name = 'Programa'
#        verbose_name_plural = "Programas"
#
#    def get_absolute_url(self):
#        return reverse('programas_ver', kwargs={'pk': self.pk})

# class Centros (models.Model):
#    nombre = models.CharField(max_length=250, null=False, blank=False)
#    sala = models.CharField(max_length=250, null=False, blank=False)
#    disponibles = models.IntegerField(null=False, blank=False)
#
#    def __str__(self):
#        return self.nombre
#
#    def clean(self):
#        self.nombre = self.nombre.capitalize()
#
#    class Meta:
#        ordering = ['nombre']
#        verbose_name = 'Centro'
#        verbose_name_plural = "Centros"


class MILD_PreAdmision(models.Model):
    fk_derivacion = models.ForeignKey(LegajosDerivaciones, on_delete=models.CASCADE)
    fk_legajo = models.ForeignKey(
        Legajos,
        related_name="MILD_fk_legajo",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    fk_legajo_1 = models.ForeignKey(
        Legajos,
        related_name="MILD_fk_legajo_1",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    fk_legajo_2 = models.ForeignKey(
        Legajos,
        related_name="MILD_fk_legajo_2",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    menores_a_cargo_1 = models.CharField(
        max_length=50, choices=CHOICE_1A5, null=True, blank=True
    )
    control_gine_1 = models.CharField(
        max_length=50, choices=CHOICE_SINO, null=True, blank=True
    )
    hijos_1 = models.CharField(max_length=50, choices=CHOICE_1A5, null=True, blank=True)
    embarazos_1 = models.CharField(
        max_length=50, choices=CHOICE_1A5, null=True, blank=True
    )
    abortos_esp_1 = models.CharField(
        max_length=50, choices=CHOICE_1A5, null=True, blank=True
    )
    abortos_prov_1 = models.CharField(
        max_length=50, choices=CHOICE_1A5, null=True, blank=True
    )
    emb_no_control_1 = models.BooleanField(
        verbose_name="Embarazo NO controlado", null=True, blank=True
    )
    emb_adolescente_1 = models.BooleanField(
        verbose_name="Embarazo adolescente", null=True, blank=True
    )
    emb_riesgo_1 = models.BooleanField(
        verbose_name="Embarazo de riesgo", null=True, blank=True
    )
    cesareas_multip_1 = models.BooleanField(
        verbose_name="Cesáreas múltiples", null=True, blank=True
    )
    partos_multip_1 = models.BooleanField(
        verbose_name="Partos múltiples", null=True, blank=True
    )
    partos_premat_1 = models.BooleanField(
        verbose_name="Partos prematuros", null=True, blank=True
    )
    partos_menos18meses_1 = models.BooleanField(
        verbose_name="Partos con menos de 18 meses de intervalo", null=True, blank=True
    )
    emb_actualmente_1 = models.CharField(
        max_length=50, choices=CHOICE_SINO, null=True, blank=True
    )
    controles_1 = models.CharField(
        max_length=50, choices=CHOICE_SINO, null=True, blank=True
    )
    emb_actual_1 = models.CharField(
        max_length=150, choices=CHOICE_EMB_RIESGO, null=True, blank=True
    )
    educ_maximo_1 = models.CharField(
        max_length=150, choices=CHOICE_EDUCACION, null=True, blank=True
    )
    educ_estado_1 = models.CharField(
        max_length=150, choices=CHOICE_ESTADO, null=True, blank=True
    )
    leer_1 = models.BooleanField(verbose_name="Sabe leer", null=True, blank=True)
    escribir_1 = models.BooleanField(
        verbose_name="Sabe escribir", null=True, blank=True
    )
    retomar_estudios_1 = models.BooleanField(
        verbose_name="Quiere retomar estudios", null=True, blank=True
    )
    aprender_oficio_1 = models.BooleanField(
        verbose_name="Quiere aprender un oficio", null=True, blank=True
    )
    planes_sociales_1 = models.ForeignKey(
        PlanesSociales,
        related_name="MILD_planes_sociales_1",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    trabajo_actual_1 = models.CharField(
        max_length=50, choices=CHOICE_SINO, null=True, blank=True
    )
    ocupacion_1 = models.CharField(
        verbose_name="Ocupación", max_length=100, null=True, blank=True
    )
    modo_contrat_1 = models.CharField(
        max_length=150, choices=CHOICE_CONTRATACION, null=True, blank=True
    )
    educ_maximo_2 = models.CharField(
        max_length=150, choices=CHOICE_EDUCACION, null=True, blank=True
    )
    educ_estado_2 = models.CharField(
        max_length=150, choices=CHOICE_ESTADO, null=True, blank=True
    )
    leer_2 = models.BooleanField(verbose_name="Sabe leer", null=True, blank=True)
    escribir_2 = models.BooleanField(
        verbose_name="Sabe escribir", null=True, blank=True
    )
    retomar_estudios_2 = models.BooleanField(
        verbose_name="Quiere retomar estudios", null=True, blank=True
    )
    aprender_oficio_2 = models.BooleanField(
        verbose_name="Quiere aprender un oficio", null=True, blank=True
    )
    programa_Pilares_2 = models.BooleanField(
        verbose_name="Quiere participar del Programa Pilares", null=True, blank=True
    )
    planes_sociales_2 = models.ForeignKey(
        PlanesSociales,
        related_name="MILD_planes_sociales_2",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    trabajo_actual_2 = models.CharField(
        max_length=50, choices=CHOICE_SINO, null=True, blank=True
    )
    ocupacion_2 = models.CharField(
        verbose_name="Ocupación", max_length=100, null=True, blank=True
    )
    modo_contrat_2 = models.CharField(
        max_length=150, choices=CHOICE_CONTRATACION, null=True, blank=True
    )
    fk_legajo_3 = models.ForeignKey(
        Legajos,
        related_name="MILD_fk_legajo_3",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    educ_maximo_3 = models.CharField(
        max_length=150, choices=CHOICE_EDUCACION, null=True, blank=True
    )
    educ_estado_3 = models.CharField(
        max_length=150, choices=CHOICE_ESTADO, null=True, blank=True
    )
    leer_3 = models.BooleanField(verbose_name="Sabe leer", null=True, blank=True)
    escribir_3 = models.BooleanField(
        verbose_name="Sabe escribir", null=True, blank=True
    )
    retomar_estudios_3 = models.BooleanField(
        verbose_name="Quiere retomar estudios", null=True, blank=True
    )
    aprender_oficio_3 = models.BooleanField(
        verbose_name="Quiere aprender un oficio", null=True, blank=True
    )
    programa_Pilares_3 = models.BooleanField(
        verbose_name="Quiere participar del Programa Pilares", null=True, blank=True
    )
    fk_legajo_4 = models.ForeignKey(
        Legajos,
        related_name="MILD_fk_legajo_4",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    educ_maximo_4 = models.CharField(
        max_length=150, choices=CHOICE_EDUCACION, null=True, blank=True
    )
    educ_estado_4 = models.CharField(
        max_length=150, choices=CHOICE_ESTADO, null=True, blank=True
    )
    leer_4 = models.BooleanField(verbose_name="Sabe leer", null=True, blank=True)
    escribir_4 = models.BooleanField(
        verbose_name="Sabe escribir", null=True, blank=True
    )
    retomar_estudios_4 = models.BooleanField(
        verbose_name="Quiere retomar estudios", null=True, blank=True
    )
    aprender_oficio_4 = models.BooleanField(
        verbose_name="Quiere aprender un oficio", null=True, blank=True
    )
    programa_Pilares_4 = models.BooleanField(
        verbose_name="Quiere participar del Programa Pilares", null=True, blank=True
    )
    fk_legajo_5 = models.ForeignKey(
        Legajos,
        related_name="MILD_fk_legajo_5",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    educ_maximo_5 = models.CharField(
        max_length=150, choices=CHOICE_EDUCACION, null=True, blank=True
    )
    educ_estado_5 = models.CharField(
        max_length=150, choices=CHOICE_ESTADO, null=True, blank=True
    )
    leer_5 = models.BooleanField(verbose_name="Sabe leer", null=True, blank=True)
    escribir_5 = models.BooleanField(
        verbose_name="Sabe escribir", null=True, blank=True
    )
    retomar_estudios_5 = models.BooleanField(
        verbose_name="Quiere retomar estudios", null=True, blank=True
    )
    aprender_oficio_5 = models.BooleanField(
        verbose_name="Quiere aprender un oficio", null=True, blank=True
    )
    programa_Pilares_5 = models.BooleanField(
        verbose_name="Quiere participar del Programa Pilares", null=True, blank=True
    )

    cri_sanitarios = models.CharField(
        max_length=250,
        choices=CHOICE_CRI_SANITARIOS,
        null=True,
        blank=True,
        verbose_name="Criterios sanitarios",
    )
    cri_sociales = models.CharField(
        max_length=250,
        choices=CHOICE_CRI_SOCIALES,
        null=True,
        blank=True,
        verbose_name="Criterios sociales",
    )
    busca_embarazo = models.BooleanField(
        verbose_name="¿Está buscando quedarse embarazada?", null=True, blank=True
    )
    conoce_metodos_anticon = models.BooleanField(
        verbose_name="¿Conoces qué son los métodos anticonceptivos?",
        null=True,
        blank=True,
    )
    metodos_anticon = models.CharField(
        max_length=250,
        choices=CHOICE_METODOS_ANTICONCEPTIVOS,
        null=True,
        blank=True,
        verbose_name="¿Cuáles conoces?",
    )
    utilizo_alguno = models.BooleanField(
        verbose_name="¿Utilizás alguno actualmente?", null=True, blank=True
    )
    cual_utilizo = models.CharField(
        max_length=250,
        choices=CHOICE_METODOS_ANTICONCEPTIVOS,
        null=True,
        blank=True,
        verbose_name="¿Cuáles utilizó?",
    )
    amigos_cercanos = models.BooleanField(
        verbose_name="¿Tenés amigos, personas cercanas o alguien con quien hablar problema?",
        null=True,
        blank=True,
    )

    apellido_ninio = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="Apellido"
    )
    nombre_ninio = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="Nombre"
    )
    dni_num_ninio = models.IntegerField(
        null=True, blank=True, verbose_name="Número DNI"
    )
    dni_ninio = models.CharField(
        max_length=250,
        choices=CHOICE_DNI_NINIO,
        null=True,
        blank=True,
        verbose_name="DNI",
    )
    sexo_ninio = models.CharField(
        max_length=250,
        choices=CHOICE_SEXO_NINIO,
        null=True,
        blank=True,
        verbose_name="Sexo",
    )
    edad_ninio = models.IntegerField(null=True, blank=True, verbose_name="Edad")
    fecha_nacimiento = models.DateField(
        null=True, blank=True, verbose_name="Fecha de nacimiento"
    )
    lugar_nacimiento = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="Lugar de nacimiento"
    )
    peso_ninio = models.IntegerField(
        null=True, blank=True, verbose_name="Peso al nacer"
    )
    mismo_domicilio = models.BooleanField(
        verbose_name="Mismo domicilio y teléfono que el cuidador entrevistado?",
        null=True,
        blank=True,
    )
    domicilio_no = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="En caso de contestar no, especificar",
    )
    hermanos = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="¿Cuántos hermanos tiene el niño? (él NO cuenta)?",
    )

    obra_social = models.BooleanField(
        null=True, blank=True, verbose_name="Tiene Obra Social"
    )
    libreta_sanitaria = models.BooleanField(
        null=True, blank=True, verbose_name="Tiene Libreta Sanitaria"
    )
    sexo_ninio = models.CharField(
        max_length=250,
        choices=CHOICE_DONDE_ATIENDE,
        null=True,
        blank=True,
        verbose_name="¿Dónde se atiende?",
    )
    ultimo_control = models.DateField(
        null=True, blank=True, verbose_name="¿Cuándo fue su último control pediátrico?"
    )
    enf_recu_con_trata = models.BooleanField(
        verbose_name="Padece enfermedad recurrente EN tratamiento",
        null=True,
        blank=True,
    )
    enf_recu_sin_trata = models.BooleanField(
        verbose_name="Padece enfermedad recurrente SIN tratamiento",
        null=True,
        blank=True,
    )
    enf_conta_con_trata = models.BooleanField(
        verbose_name="Padece enfermedad infecto-contagiosa EN tratamiento",
        null=True,
        blank=True,
    )
    enf_conta_sin_trata = models.BooleanField(
        verbose_name="Padece enfermedad infecto-contagiosa SIN tratamiento",
        null=True,
        blank=True,
    )
    enf_mental_con_trata = models.BooleanField(
        verbose_name="Padece problemas de salud mental EN tratamiento",
        null=True,
        blank=True,
    )
    enf_mental_sin_trata = models.BooleanField(
        verbose_name="Padece problemas de salud mental SIN tratamiento",
        null=True,
        blank=True,
    )
    capa_reducidas = models.BooleanField(
        verbose_name="Capacidades reducidas o afectadas", null=True, blank=True
    )
    certif_discap = models.BooleanField(
        verbose_name="Tiene certificado único de discapacidad", null=True, blank=True
    )
    medicamento = models.BooleanField(
        verbose_name="Toma medicamento", null=True, blank=True
    )
    bajo_peso = models.BooleanField(
        verbose_name="Niño con bajo peso", null=True, blank=True
    )
    sobrepeso = models.BooleanField(
        verbose_name="Niño con sobrepeso", null=True, blank=True
    )
    prematuro = models.BooleanField(
        verbose_name="Prematuro que requiere seguimiento", null=True, blank=True
    )
    interv_quirurgicas = models.BooleanField(
        verbose_name="Intervenciones quirúrgicas", null=True, blank=True
    )
    accidentes_domesticos = models.BooleanField(
        verbose_name="Accidentes domésticos (lastimadura, quemadura, corte, golpe fuerte)",
        null=True,
        blank=True,
    )
    colecho = models.BooleanField(verbose_name="Colecho", null=True, blank=True)
    enfermedad = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Si padece enfermedad ¿cuál? ¿Dónde se trata?",
    )
    auditiva = models.BooleanField(
        verbose_name="Dificultad auditiva", null=True, blank=True
    )
    respiratoria = models.BooleanField(
        verbose_name="Dificultad respiratoria", null=True, blank=True
    )
    visual = models.BooleanField(
        verbose_name="Dificultad visual", null=True, blank=True
    )
    traumatologica = models.BooleanField(
        verbose_name="Dificultad traumatologica", null=True, blank=True
    )
    emocional = models.BooleanField(
        verbose_name="Dificultad emocional", null=True, blank=True
    )
    psiquica = models.BooleanField(
        verbose_name="Dificultad psiquica o psicologica", null=True, blank=True
    )
    digestiva = models.BooleanField(
        verbose_name="Dificultad digestiva", null=True, blank=True
    )
    alergias = models.BooleanField(verbose_name="Alergias", null=True, blank=True)
    observaciones_salud = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Observaciones/detalles de salud",
    )
    vacunas = models.BooleanField(
        verbose_name="¿Recibió todas las vacunas correspondientes a su edad?",
        null=True,
        blank=True,
    )

    acompaniante_entrevista = models.ForeignKey(
        Usuarios,
        verbose_name="Acompañante que realizo la entrevista",
        related_name="MILD_Acompaniante_entrevista",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    acompaniante_asignado = models.ForeignKey(
        Usuarios,
        verbose_name="Acompañante asignado",
        related_name="MILD_Acompaniante_asignado",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    observaciones_gral = models.CharField(
        max_length=350,
        null=True,
        blank=True,
        verbose_name="Aquí puede detallar información adicional de la familia, o temas que es importante resaltar acerca de la misma.",
    )

    vinculo1 = models.CharField(max_length=150, null=True, blank=True)
    vinculo2 = models.CharField(max_length=150, null=True, blank=True)
    vinculo3 = models.CharField(max_length=150, null=True, blank=True)
    vinculo4 = models.CharField(max_length=150, null=True, blank=True)
    vinculo5 = models.CharField(max_length=150, null=True, blank=True)
    ivi = models.CharField(max_length=150, null=True, blank=True)
    indice_ingreso = models.CharField(max_length=150, null=True, blank=True)
    admitido = models.CharField(max_length=150, null=True, blank=True)
    creado_por = models.ForeignKey(
        Usuarios,
        related_name="MILD_PreAdm_creado_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    modificado_por = models.ForeignKey(
        Usuarios,
        related_name="MILD_PreAdm_modificado_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    modificado = models.DateField(auto_now=True, null=True, blank=True)
    estado = models.CharField(max_length=100, null=True, blank=True)
    tipo = models.CharField(max_length=100, null=True, blank=True)


class MILD_IndiceIVI(models.Model):
    fk_criterios_ivi = models.ForeignKey(Criterios_IVI, on_delete=models.CASCADE)
    fk_legajo = models.ForeignKey(
        Legajos, on_delete=models.CASCADE, null=True, blank=True
    )
    fk_preadmi = models.ForeignKey(
        MILD_PreAdmision, on_delete=models.CASCADE, null=True, blank=True
    )
    presencia = models.BooleanField(default=False, null=True, blank=True)
    tipo = models.CharField(max_length=350, null=True, blank=True)
    programa = models.CharField(
        max_length=150, choices=CHOICE_NOSI, null=True, blank=True
    )
    clave = models.CharField(max_length=350, null=True, blank=True)
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    modificado = models.DateField(auto_now=True, null=True, blank=True)


class MILD_Foto_IVI(models.Model):
    fk_preadmi = models.ForeignKey(
        MILD_PreAdmision, on_delete=models.CASCADE, null=True, blank=True
    )
    fk_legajo = models.ForeignKey(
        Legajos, on_delete=models.CASCADE, null=True, blank=True
    )
    puntaje = models.SmallIntegerField(null=True, blank=True)
    puntaje_max = models.SmallIntegerField(null=True, blank=True)
    crit_modificables = models.SmallIntegerField(null=True, blank=True)
    crit_presentes = models.SmallIntegerField(null=True, blank=True)
    observaciones = models.CharField(max_length=350, null=True, blank=True)
    tipo = models.CharField(max_length=350, null=True, blank=True)
    clave = models.CharField(max_length=350, null=True, blank=True)
    creado_por = models.ForeignKey(
        Usuarios,
        related_name="MILD_IVI_creado_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    modificado_por = models.ForeignKey(
        Usuarios,
        related_name="MILD_IVI_modificado_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    modificado = models.DateField(auto_now=True, null=True, blank=True)


class Criterios_Ingreso(models.Model):
    criterio = models.CharField(max_length=250, null=False, blank=False)
    tipo = models.CharField(
        max_length=250, choices=CHOICE_TIPO_INGRESO_MILD, null=False, blank=False
    )
    puntaje = models.SmallIntegerField(null=False, blank=False)
    modificable = models.CharField(
        max_length=50, choices=CHOICE_NOSI, null=False, blank=False
    )

    def __str__(self):
        return self.criterio


class MILD_IndiceIngreso(models.Model):
    fk_criterios_ingreso = models.ForeignKey(
        Criterios_Ingreso, on_delete=models.CASCADE
    )
    fk_legajo = models.ForeignKey(
        Legajos, on_delete=models.CASCADE, null=True, blank=True
    )
    fk_preadmi = models.ForeignKey(
        MILD_PreAdmision, on_delete=models.CASCADE, null=True, blank=True
    )
    presencia = models.BooleanField(default=False, null=True, blank=True)
    tipo = models.CharField(max_length=350, null=True, blank=True)
    programa = models.CharField(
        max_length=150, choices=CHOICE_NOSI, null=True, blank=True
    )
    clave = models.CharField(max_length=350, null=True, blank=True)
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    modificado = models.DateField(auto_now=True, null=True, blank=True)


class MILD_Foto_Ingreso(models.Model):
    fk_preadmi = models.ForeignKey(
        MILD_PreAdmision, on_delete=models.CASCADE, null=True, blank=True
    )
    fk_legajo = models.ForeignKey(
        Legajos, on_delete=models.CASCADE, null=True, blank=True
    )
    puntaje = models.SmallIntegerField(null=True, blank=True)
    puntaje_max = models.SmallIntegerField(null=True, blank=True)
    crit_modificables = models.SmallIntegerField(null=True, blank=True)
    crit_presentes = models.SmallIntegerField(null=True, blank=True)
    observaciones = models.CharField(max_length=350, null=True, blank=True)
    tipo = models.CharField(max_length=350, null=True, blank=True)
    clave = models.CharField(max_length=350, null=True, blank=True)
    creado_por = models.ForeignKey(
        Usuarios,
        related_name="MILD_Ingreso_creado_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    modificado_por = models.ForeignKey(
        Usuarios,
        related_name="MILD_Ingreso_modificado_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    modificado = models.DateField(auto_now=True, null=True, blank=True)


class MILD_Admision(models.Model):
    fk_preadmi = models.ForeignKey(MILD_PreAdmision, on_delete=models.CASCADE)
    estado = models.CharField(max_length=150, null=True, blank=True, default="Activa")
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    modificado = models.DateField(auto_now=True, null=True, blank=True)
    creado_por = models.ForeignKey(
        Usuarios,
        related_name="MILD_Admision_creado_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    modificado_por = models.ForeignKey(
        Usuarios,
        related_name="MILD_Admision_modificada_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )


class OpcionesResponsables(models.Model):
    nombre = models.CharField(max_length=250, unique=True)

    def __str__(self):
        return self.nombre


class MILD_Intervenciones(models.Model):
    fk_admision = models.ForeignKey(
        MILD_Admision, on_delete=models.CASCADE, null=True, blank=True
    )
    criterio_modificable = models.ForeignKey(Criterios_IVI, on_delete=models.CASCADE)
    accion = models.CharField(
        max_length=250, choices=CHOICE_ACCION_DESARROLLADA, null=False, blank=False
    )
    responsable = models.ManyToManyField(OpcionesResponsables)
    impacto = models.CharField(
        max_length=250,
        choices=[("Trabajado", "Trabajado"), ("Revertido", "Revertido")],
        null=False,
        blank=False,
    )
    detalle = models.CharField(max_length=350, null=True, blank=True)
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    modificado = models.DateField(auto_now=True, null=True, blank=True)
    creado_por = models.ForeignKey(
        Usuarios,
        related_name="MILD_Intervenciones_creado_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    modificado_por = models.ForeignKey(
        Usuarios,
        related_name="MILD_Intervenciones_modificada_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )


class MILD_Historial(models.Model):
    fk_legajo = models.ForeignKey(
        Legajos, on_delete=models.CASCADE, null=True, blank=True
    )
    fk_legajo_derivacion = models.ForeignKey(
        LegajosDerivaciones, on_delete=models.CASCADE, null=True, blank=True
    )
    fk_preadmi = models.ForeignKey(
        MILD_PreAdmision, on_delete=models.CASCADE, null=True, blank=True
    )
    fk_admision = models.ForeignKey(
        MILD_Admision, on_delete=models.CASCADE, null=True, blank=True
    )
    movimiento = models.CharField(max_length=150, null=True, blank=True)
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    creado_por = models.ForeignKey(
        Usuarios, on_delete=models.CASCADE, null=True, blank=True
    )
