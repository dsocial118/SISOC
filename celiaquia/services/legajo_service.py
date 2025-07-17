# services/legajo_service.py
import logging
from django.db import transaction
from django.core.exceptions import ValidationError

from celiaquia.models import EstadoLegajo, ExpedienteCiudadano

logger = logging.getLogger(__name__)

class LegajoService:
    @staticmethod
    def listar_legajos(expediente):
        """
        Devuelve queryset de legajos de un expediente, con datos de ciudadano y estado.
        """
        return (
            expediente.expediente_ciudadanos
            .select_related('ciudadano', 'estado')
            .order_by('creado_en')
        )

    @staticmethod
    @transaction.atomic
    def subir_archivo_individual(exp_ciudadano, archivo):
        """
        Asigna un archivo a un legajo y cambia su estado a 'DOCUMENTO_CARGADO'.
        Valida existencia de archivo y estado inicial.
        """
        if not archivo:
            raise ValidationError('Debe proporcionar un archivo válido.')
        try:
            estado_cargado = EstadoLegajo.objects.get(nombre='DOCUMENTO_CARGADO')
        except EstadoLegajo.DoesNotExist:
            raise ValidationError('El estado DOCUMENTO_CARGADO no está definido.')

        exp_ciudadano.archivo = archivo
        exp_ciudadano.estado = estado_cargado
        exp_ciudadano.save(update_fields=['archivo', 'estado', 'modificado_en'])
        logger.info(
            "Legajo %s: archivo subido y estado actualizado.",
            exp_ciudadano.id
        )
        return exp_ciudadano

    @staticmethod
    def all_legajos_loaded(expediente):
        """
        Verifica que todos los legajos de un expediente tengan archivo.
        """
        faltantes = (
            expediente.expediente_ciudadanos
            .filter(archivo__isnull=True)
            .exists()
        )
        return not faltantes
