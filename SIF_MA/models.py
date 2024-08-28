from django.db import models
from Configuraciones.models import *
from Legajos.models import *
from django.core.validators import MinValueValidator, MaxValueValidator
from .choices import *
from django.urls import *

# Create your models here.

# class legajo_MA (models.Model):
#    fk_programa = models.ForeignKey(Programas, on_delete=models.CASCADE)
#    fk_legajo = models.ForeignKey(Legajos, on_delete=models.CASCADE)
#    nombre = models.CharField(max_length=100, unique=True)
#    estado = models.BooleanField(default=True)
#    observaciones = models.CharField(max_length=300, null=True, blank=True)
#    #creado_por = models.ForeignKey(Usuarios, related_name='MA_creado_por', on_delete=models.CASCADE, blank=True, null=True)
#    #modificado_por = models.ForeignKey(Usuarios, related_name='MA_modificado_por', on_delete=models.CASCADE, blank=True, null=True)
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


class MA_PreAdmision(models.Model):
    fk_derivacion = models.ForeignKey(LegajosDerivaciones, on_delete=models.CASCADE)
    fk_legajo = models.ForeignKey(
        Legajos,
        related_name="MA_fk_legajo",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    fk_legajo_1 = models.ForeignKey(
        Legajos,
        related_name="MA_fk_legajo_1",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    fk_legajo_2 = models.ForeignKey(
        Legajos,
        related_name="MA_fk_legajo_2",
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
        related_name="MA_planes_sociales_1",
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
        related_name="MA_planes_sociales_2",
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
        related_name="MA_fk_legajo_3",
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
        related_name="MA_fk_legajo_4",
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
        related_name="MA_fk_legajo_5",
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

    test_embarazo = models.BooleanField(
        verbose_name="¿Te hiciste test de embarazo?", null=True, blank=True
    )
    fum = models.DateField(
        verbose_name="Fecha última mestruación", null=True, blank=True
    )
    sem_embarazo = models.IntegerField(
        choices=CHOICE_1to40, null=True, blank=True, verbose_name="Semanas de embarazo"
    )
    fpp = models.DateField(verbose_name="FPP", null=True, blank=True)
    centro_controla = models.CharField(
        max_length=250,
        verbose_name="Centro de salud que se controla o controlará",
        null=True,
        blank=True,
        choices=CHOICE_CENTRO_CONTROL,
    )
    primer_control = models.IntegerField(
        choices=CHOICE_4to40,
        null=True,
        blank=True,
        verbose_name="¿Semana del primer control?",
    )
    primer_embarazo = models.BooleanField(
        verbose_name="¿Es tu primer embarazo?", null=True, blank=True
    )
    libreta_sanitaria = models.BooleanField(
        verbose_name="¿Tiene libreta sanitaria?", null=True, blank=True
    )
    metodos_anticonceptivos = models.BooleanField(
        verbose_name="¿Conoces los métodos anticonceptivos?", null=True, blank=True
    )
    cuales_met_anticon_conoces = models.CharField(
        max_length=250,
        verbose_name="¿Cuáles conoces?",
        null=True,
        blank=True,
        choices=CHOICE_METODOS_ANTICONCEPTIVOS,
    )
    utilizabas_alguno = models.BooleanField(
        verbose_name="¿Utilizabas alguno cuando quedaste embarazada?",
        null=True,
        blank=True,
    )
    cual_usabas = models.CharField(
        max_length=250,
        verbose_name="¿Cual usabas?",
        null=True,
        blank=True,
        choices=CHOICE_METODOS_ANTICONCEPTIVOS,
    )
    sifilis_anterior = models.BooleanField(
        verbose_name="¿Tuviste sifilis en embarazos anteriores?", null=True, blank=True
    )
    sifilis_ahora = models.BooleanField(
        verbose_name="¿Tenes sifilis actualmente?", null=True, blank=True
    )
    sifilis_tratamiento_pareja = models.BooleanField(
        verbose_name="En caso de haber tenido o tener sifilis: ¿Tu pareja hizo el tratamiento?",
        null=True,
        blank=True,
    )
    consumio_drogas = models.BooleanField(
        verbose_name="¿Alguna vez consumió drogas?", null=True, blank=True
    )
    drogas_ahora = models.BooleanField(
        verbose_name="¿Consume drogas actualmente?", null=True, blank=True
    )
    alcohol_ahora = models.BooleanField(
        verbose_name="¿Consume alcohol actualmente?", null=True, blank=True
    )
    sospecha_consumo = models.BooleanField(
        verbose_name="Sospecha de consumo", null=True, blank=True
    )

    embarazo_controlado = models.CharField(
        max_length=250,
        verbose_name="Embarazo controlado",
        null=True,
        blank=True,
        choices=CHOICE_EMBARAZO_CONTROLADO,
    )
    comienza_control = models.BooleanField(
        verbose_name="¿Comienza control en operativo?", null=True, blank=True
    )
    prim_trim_control_obstetra = models.BooleanField(
        verbose_name="Al menos 1 control con la obstetra", null=True, blank=True
    )
    prim_trim_estudios_labo = models.BooleanField(
        verbose_name="Laboratorio- Rutina 1er trimestre", null=True, blank=True
    )
    prim_trim_estudios_eco = models.BooleanField(
        verbose_name="Ecografía", null=True, blank=True
    )
    prim_trim_estudios_pap = models.BooleanField(
        verbose_name="PAP", null=True, blank=True
    )
    prim_trim_estudios_grupo_factor = models.BooleanField(
        verbose_name="Grupo y Factor", null=True, blank=True
    )
    prim_trim_control_odonto = models.BooleanField(
        verbose_name="Control odontologico", null=True, blank=True
    )
    seg_trim_control_obsetra = models.BooleanField(
        verbose_name="Al menos 2 controles con la obstetra", null=True, blank=True
    )
    seg_trim_control_fetal = models.BooleanField(
        verbose_name="Scan fetal", null=True, blank=True
    )
    seg_trim_p75 = models.BooleanField(verbose_name="P75", null=True, blank=True)
    ter_trim_control_rutina = models.BooleanField(
        verbose_name="Ecografía, hisopado vaginal y laboratorio", null=True, blank=True
    )
    ter_trim_monitoreo_fetal = models.BooleanField(
        verbose_name="Monitoreo fetal", null=True, blank=True
    )
    ter_trim_electro_cardio = models.BooleanField(
        verbose_name="Electro cardiograma", null=True, blank=True
    )
    acompaniante = models.ForeignKey(
        Usuarios,
        related_name="MA_Acompaniante",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    madrina = models.ForeignKey(
        AgentesExternos,
        related_name="MA_Madrina",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
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
        related_name="MA_PreAdm_creado_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    modificado_por = models.ForeignKey(
        Usuarios,
        related_name="MA_PreAdm_modificado_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    modificado = models.DateField(auto_now=True, null=True, blank=True)
    estado = models.CharField(max_length=100, null=True, blank=True)
    tipo = models.CharField(max_length=100, null=True, blank=True)


class Criterios_IVI(models.Model):
    criterio = models.CharField(max_length=250, null=False, blank=False)
    tipo = models.CharField(
        max_length=250, choices=CHOICE_TIPO_IVI, null=False, blank=False
    )
    puntaje = models.SmallIntegerField(null=False, blank=False)
    modificable = models.CharField(
        max_length=50, choices=CHOICE_NOSI, null=False, blank=False
    )

    def __str__(self):
        return self.criterio


class MA_IndiceIVI(models.Model):
    fk_criterios_ivi = models.ForeignKey(Criterios_IVI, on_delete=models.CASCADE)
    fk_legajo = models.ForeignKey(
        Legajos, on_delete=models.CASCADE, null=True, blank=True
    )
    fk_preadmi = models.ForeignKey(
        MA_PreAdmision, on_delete=models.CASCADE, null=True, blank=True
    )
    presencia = models.BooleanField(default=False, null=True, blank=True)
    tipo = models.CharField(max_length=350, null=True, blank=True)
    programa = models.CharField(
        max_length=150, choices=CHOICE_NOSI, null=True, blank=True
    )
    clave = models.CharField(max_length=350, null=True, blank=True)
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    modificado = models.DateField(auto_now=True, null=True, blank=True)


class MA_Foto_IVI(models.Model):
    fk_preadmi = models.ForeignKey(
        MA_PreAdmision, on_delete=models.CASCADE, null=True, blank=True
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
        related_name="MA_IVI_creado_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    modificado_por = models.ForeignKey(
        Usuarios,
        related_name="MA_IVI_modificado_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    modificado = models.DateField(auto_now=True, null=True, blank=True)


class Criterios_Ingreso(models.Model):
    criterio = models.CharField(max_length=250, null=False, blank=False)
    tipo = models.CharField(
        max_length=250, choices=CHOICE_TIPO_INGRESO, null=False, blank=False
    )
    puntaje = models.SmallIntegerField(null=False, blank=False)
    modificable = models.CharField(
        max_length=50, choices=CHOICE_NOSI, null=False, blank=False
    )

    def __str__(self):
        return self.criterio


class MA_IndiceIngreso(models.Model):
    fk_criterios_ingreso = models.ForeignKey(
        Criterios_Ingreso, on_delete=models.CASCADE
    )
    fk_legajo = models.ForeignKey(
        Legajos, on_delete=models.CASCADE, null=True, blank=True
    )
    fk_preadmi = models.ForeignKey(
        MA_PreAdmision, on_delete=models.CASCADE, null=True, blank=True
    )
    presencia = models.BooleanField(default=False, null=True, blank=True)
    tipo = models.CharField(max_length=350, null=True, blank=True)
    programa = models.CharField(
        max_length=150, choices=CHOICE_NOSI, null=True, blank=True
    )
    clave = models.CharField(max_length=350, null=True, blank=True)
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    modificado = models.DateField(auto_now=True, null=True, blank=True)


class MA_Foto_Ingreso(models.Model):
    fk_preadmi = models.ForeignKey(
        MA_PreAdmision, on_delete=models.CASCADE, null=True, blank=True
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
        related_name="MA_Ingreso_creado_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    modificado_por = models.ForeignKey(
        Usuarios,
        related_name="MA_Ingreso_modificado_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    modificado = models.DateField(auto_now=True, null=True, blank=True)


class MA_Admision(models.Model):
    fk_preadmi = models.ForeignKey(MA_PreAdmision, on_delete=models.CASCADE)
    estado = models.CharField(max_length=150, null=True, blank=True, default="Activa")
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    modificado = models.DateField(auto_now=True, null=True, blank=True)
    creado_por = models.ForeignKey(
        Usuarios,
        related_name="MA_Admision_creado_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    modificado_por = models.ForeignKey(
        Usuarios,
        related_name="MA_Admision_modificada_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )


class OpcionesResponsables(models.Model):
    nombre = models.CharField(max_length=250, unique=True)

    def __str__(self):
        return self.nombre


class MA_Intervenciones(models.Model):
    fk_admision = models.ForeignKey(
        MA_Admision, on_delete=models.CASCADE, null=True, blank=True
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
        related_name="MA_Intervenciones_creado_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    modificado_por = models.ForeignKey(
        Usuarios,
        related_name="MA_Intervenciones_modificada_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )


class MA_Historial(models.Model):
    fk_legajo = models.ForeignKey(
        Legajos, on_delete=models.CASCADE, null=True, blank=True
    )
    fk_legajo_derivacion = models.ForeignKey(
        LegajosDerivaciones, on_delete=models.CASCADE, null=True, blank=True
    )
    fk_preadmi = models.ForeignKey(
        MA_PreAdmision, on_delete=models.CASCADE, null=True, blank=True
    )
    fk_admision = models.ForeignKey(
        MA_Admision, on_delete=models.CASCADE, null=True, blank=True
    )
    movimiento = models.CharField(max_length=150, null=True, blank=True)
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    creado_por = models.ForeignKey(
        Usuarios, on_delete=models.CASCADE, null=True, blank=True
    )
