from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse
from Usuarios.models import Usuarios

class Provincias(models.Model):
    nombre = models.CharField(max_length=100)
   
    def __str__(self):
        return self.nombre

class Provincias_Datos(models.Model):
    provincia = models.ForeignKey(Provincias, on_delete=models.PROTECT)
    poblacion = models.IntegerField(blank=True, null=True)
    pobreza  = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)

    #--- EMPLEO-----
    PEA = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)
    ocupada = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)
    subocupada = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)
    desocupada = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)

    #--- EDUCACION----
    educ_incompleta_obligatoria = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)
    primara_incompleta_PAS = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)
    secundaria_incompleta_PAS = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)

    #--- PAS-----
    beneficiarios_PAS = models.IntegerField(blank=True, null=True)
    porcentaje_PAS = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)
    q_expedientes = models.IntegerField(blank=True, null=True)

    #--- AGROINDUSTRIA-----
    alimentos = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)
    ganaderia = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)
    agricultura_familiar = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)
    pesca = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)
    forestal = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)
    manufacturera = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)
    textil = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)

    #--- OFICIOS-----
    carpinteria = models.BooleanField(default=False)
    herreria = models.BooleanField(default=False)
    mecanica = models.BooleanField(default=False)
    matriceria = models.BooleanField(default=False)
    otras_matriceria = models.BooleanField(default=False)
    artesania_manufactureria = models.BooleanField(default=False)
    albanileria = models.BooleanField(default=False)
    otras_actividades_construccion = models.BooleanField(default=False)

    #--- ECONOMIA CIRCULAR----
    reciclaje = models.BooleanField(default=False)
    energia_renovable = models.BooleanField(default=False)

    #--- TECNOLOGIA Y SOFTWARE----
    soporte_tecnico = models.BooleanField(default=False)
    infraestructura_tecnologica = models.BooleanField(default=False)
    desarrollo_software = models.BooleanField(default=False)

    #--- SERVICIOS----
    estetica_pedicuria_etc = models.BooleanField(default=False)
    limpieza = models.BooleanField(default=False)
    jardineria = models.BooleanField(default=False)
    gastronomico = models.BooleanField(default=False)
    logistica = models.BooleanField(default=False)
    turismo = models.BooleanField(default=False)
    comercializacion = models.BooleanField(default=False)
    cuidados = models.BooleanField(default=False)
    salud = models.BooleanField(default=False)

    #--- OTROS----
    energia = models.BooleanField(default=False)
    mineria = models.BooleanField(default=False)
    petroquimica = models.BooleanField(default=False)

    #--- Creado, modificado, usuario----
    creado_por = models.ForeignKey(
        Usuarios, related_name='datos_prov_creado_por', on_delete=models.PROTECT, blank=True, null=True)
    modificado_por = models.ForeignKey(
        Usuarios, related_name='datos_prov_modificado_por', on_delete=models.PROTECT, blank=True, null=True)
    creado = models.DateField(auto_now_add=True)
    modificado = models.DateField(auto_now=True)
    
    
    def __str__(self):
        return self.provincia