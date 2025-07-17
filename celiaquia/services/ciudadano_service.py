from datetime import date
from django.core.exceptions import ValidationError
from ciudadanos.models import DimensionEconomia, DimensionEducacion, DimensionFamilia, DimensionSalud, DimensionTrabajo, DimensionVivienda
from ciudadanos.models import Ciudadano

class CiudadanoService:
    @staticmethod
    def get_or_create_ciudadano(datos):
        filtro = {
            'tipo_documento': datos.get('tipo_documento'),
            'documento': datos.get('documento'),
            'nombre': datos.get('nombre'),
            'apellido': datos.get('apellido'),
            'fecha_nacimiento': datos.get('fecha_nacimiento'),
        }
        ciudadano, created = Ciudadano.objects.get_or_create(**filtro)
        if created:
            CiudadanoService.crear_ciudadano_con_dimensiones(datos)
        return ciudadano

    @staticmethod
    def crear_ciudadano_con_dimensiones(datos):
        ciudadano = Ciudadano.objects.create(
            nombre=datos.get('nombre'),
            apellido=datos.get('apellido'),
            documento=datos.get('documento'),
            fecha_nacimiento=datos.get('fecha_nacimiento'),
            tipo_documento=datos.get('tipo_documento'),
            sexo=datos.get('sexo'),
        )
        for Modelo in (
            DimensionEconomia,
            DimensionEducacion,
            DimensionFamilia,
            DimensionSalud,
            DimensionTrabajo,
            DimensionVivienda,
        ):
            Modelo.objects.create(ciudadano=ciudadano)
        return ciudadano
