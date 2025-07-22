# services/ciudadano_service.py

import logging
from django.core.exceptions import ValidationError
from ciudadanos.models import (
    Ciudadano,
    TipoDocumento,
    Sexo,
    DimensionEconomia,
    DimensionEducacion,
    DimensionFamilia,
    DimensionSalud,
    DimensionTrabajo,
    DimensionVivienda,
)

logger = logging.getLogger(__name__)

class CiudadanoService:
    @staticmethod
    def get_or_create_ciudadano(datos: dict) -> Ciudadano:
        """
        Busca o crea un Ciudadano usando datos de fila.
        Convierte tipo_documento y sexo a instancias de sus modelos.
        Inicializa dimensiones si es nuevo.
        """
        # 1) Resolver la FK de TipoDocumento
        raw_td = datos.get('tipo_documento')
        try:
            td = TipoDocumento.objects.get(pk=int(raw_td))
        except Exception:
            raise ValidationError(f"Tipo de documento inválido: {raw_td}")

        # 2) Resolver la FK de Sexo
        raw_sex = datos.get('sexo')
        try:
            sx = Sexo.objects.get(pk=int(raw_sex))
        except Exception:
            raise ValidationError(f"Sexo inválido: {raw_sex}")

        # 3) Filtro único basado en los campos clave
        filtro = {
            'tipo_documento': td,
            'documento': datos.get('documento'),
            'nombre': datos.get('nombre'),
            'apellido': datos.get('apellido'),
            'fecha_nacimiento': datos.get('fecha_nacimiento'),
        }
        # 4) get_or_create con default para sexo
        ciudadano, created = Ciudadano.objects.get_or_create(
            **filtro,
            defaults={'sexo': sx}
        )
        if created:
            logger.info(f"Ciudadano creado: {ciudadano.pk}")
            CiudadanoService._inicializar_dimensiones(ciudadano)
        else:
            logger.debug(f"Ciudadano existente: {ciudadano.pk}")
        return ciudadano

    @staticmethod
    def _inicializar_dimensiones(ciudadano: Ciudadano):
        """
        Crea los registros en todas las dimensiones para un ciudadano nuevo.
        """
        for Modelo in (
            DimensionEconomia,
            DimensionEducacion,
            DimensionFamilia,
            DimensionSalud,
            DimensionTrabajo,
            DimensionVivienda,
        ):
            Modelo.objects.create(ciudadano=ciudadano)
        logger.info(f"Dimensiones inicializadas para ciudadano {ciudadano.pk}")
