from django.db import models
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

#class LegajosComedo (models.Model):
    
    # pk = models.CharField(max_length=250, verbose_name='Nombre del Comedor')
    # nombreComedor = models.CharField(max_length=250, verbose_name='Nombre del Comedor')
    # Nombre del merendero o comedor
    # Tipo Espacio Comunitario (*)
    # Fecha Inicio(*)
    # Cantidad de Asistentes (*)
    # Cantidad de Colaboradores (*)   
    # Cuit =models.DecimalField()
    # longitud = models.CharField(max_length=250, verbose_name='Nombre del Comedor')
    # latitud = models.CharField(max_length=250, verbose_name='Nombre del Comedor')
    # Tipo de Org. de la sociedad civil (*)
    # nombre Organización
    # IDPRovencia 
    # calle 
    
    # buscar tablas y setear las pk 
    # ir a legajos agregar id =autofik primerykr = true