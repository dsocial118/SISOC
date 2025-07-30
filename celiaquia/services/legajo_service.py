import logging
from django.db import transaction
from django.core.exceptions import ValidationError

from celiaquia.models import EstadoLegajo, ExpedienteCiudadano, EstadoExpediente

logger = logging.getLogger(__name__)

class LegajoService:
    @staticmethod
    def listar_legajos(expediente):
        """
        Devuelve un queryset de los legajos de un expediente,
        con datos de ciudadano y estado, ordenados por fecha de creación.
        """
        return (
            expediente.expediente_ciudadanos
            .select_related("ciudadano", "estado")
            .order_by("creado_en")
        )

    @staticmethod
    @transaction.atomic
    def subir_archivo_individual(exp_ciudadano: ExpedienteCiudadano, archivo):
        """
        Asigna un archivo a un legajo y cambia su estado a 'ARCHIVO_CARGADO'.
        Si es el primer archivo de este expediente, actualiza el estado del
        expediente a 'EN_ESPERA'.
        Valida que se proporcione un archivo y que los estados existan.
        """
        if not archivo:
            raise ValidationError("Debe proporcionar un archivo válido.")

        try:
            estado_cargado = EstadoLegajo.objects.get(nombre="ARCHIVO_CARGADO")
        except EstadoLegajo.DoesNotExist:
            raise ValidationError("El estado ARCHIVO_CARGADO no está definido en la base de datos.")

        # Guardar archivo y estado del legajo
        exp_ciudadano.archivo = archivo
        exp_ciudadano.estado = estado_cargado
        exp_ciudadano.save(update_fields=["archivo", "estado", "modificado_en"])
        logger.info("Legajo %s: archivo subido y estado actualizado a ARCHIVO_CARGADO.", exp_ciudadano.pk)

        # Si es el primer legajo con archivo, pasamos expediente a 'EN_ESPERA'
        expediente = exp_ciudadano.expediente
        if expediente.expediente_ciudadanos.filter(archivo__isnull=False).count() == 1:
            try:
                estado_espera, _ = EstadoExpediente.objects.get_or_create(nombre="EN_ESPERA")
                expediente.estado = estado_espera
                expediente.save(update_fields=["estado"])
                logger.info("Expediente %s: estado actualizado a EN_ESPERA.", expediente.pk)
            except Exception as e:
                logger.warning("No se pudo actualizar estado del expediente %s: %s", expediente.pk, e)

        return exp_ciudadano

    @staticmethod
    def all_legajos_loaded(expediente):
        """
        Verifica que todos los legajos de un expediente tengan un archivo asociado.
        Devuelve True si ninguno falta, False si al menos uno no tiene archivo.
        """
        faltantes = expediente.expediente_ciudadanos.filter(archivo__isnull=True).exists()
        return not faltantes
