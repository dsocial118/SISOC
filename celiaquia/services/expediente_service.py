# services/expediente_service.py
import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from celiaquia.models import (
    Expediente,
    AsignacionTecnico,
    InformePago,
    EstadoExpediente
)

logger = logging.getLogger(__name__)
User = get_user_model()

class ExpedienteService:
    @staticmethod
    @transaction.atomic
    def create_expediente(usuario_provincia, datos_metadatos, excel_masivo):
        """
        Crea un nuevo Expediente en estado 'CREADO' con metadatos y archivo.
        Valida que el código exista y sea único.
        """
        codigo = datos_metadatos.get('codigo')
        if not codigo:
            raise ValidationError('El código del expediente es obligatorio.')
        if Expediente.objects.filter(codigo=codigo).exists():
            raise ValidationError(f'Ya existe un expediente con código {codigo}.')

        estado, _ = EstadoExpediente.objects.get_or_create(nombre='CREADO')
        expediente = Expediente.objects.create(
            codigo=codigo,
            usuario_provincia=usuario_provincia,
            estado=estado,
            observaciones=datos_metadatos.get('observaciones', ''),
            excel_masivo=excel_masivo
        )
        logger.info("Expediente %s creado por %s", expediente.codigo, usuario_provincia.username)
        return expediente

    @staticmethod
    @transaction.atomic
    def confirmar_envio(expediente):
        """
        Verifica que todos los legajos tengan archivo y cambia estado a 'ENVIADO'.
        """
        pendiente = expediente.expediente_ciudadanos.filter(archivo__isnull=True).exists()
        if pendiente:
            raise ValidationError('Todos los legajos deben tener archivo cargado antes de confirmar.')

        estado, _ = EstadoExpediente.objects.get_or_create(nombre='ENVIADO')
        expediente.estado = estado
        expediente.save(update_fields=['estado'])
        logger.info("Expediente %s confirmado para envío", expediente.codigo)
        return expediente

    @staticmethod
    @transaction.atomic
    def asignar_tecnico(expediente, tecnico):
        """
        Asigna o actualiza el técnico responsable y cambia estado a 'ASIGNADO'.
        """
        if isinstance(tecnico, int):
            tecnico = User.objects.get(pk=tecnico)
        AsignacionTecnico.objects.update_or_create(
            expediente=expediente,
            defaults={'tecnico': tecnico}
        )
        estado, _ = EstadoExpediente.objects.get_or_create(nombre='ASIGNADO')
        expediente.estado = estado
        expediente.save(update_fields=['estado'])
        logger.info("Técnico %s asignado al expediente %s", tecnico.username, expediente.codigo)
        return expediente

    @staticmethod
    @transaction.atomic
    def abrir_pago(expediente):
        """
        Cambia el estado del expediente a 'PAGO_ABIERTO'.
        """
        estado, _ = EstadoExpediente.objects.get_or_create(nombre='PAGO_ABIERTO')
        expediente.estado = estado
        expediente.save(update_fields=['estado'])
        logger.info("Pago abierto para expediente %s", expediente.codigo)
        return expediente

    @staticmethod
    @transaction.atomic
    def cerrar_pago(expediente, tecnico, fecha_pago, monto, observaciones=''):
        """
        Cierra el pago creando un InformePago y cambiando estado a 'PAGO_CERRADO'.
        Requiere que exista asignación de técnico.
        """
        if not hasattr(expediente, 'asignacion_tecnico'):
            raise ValidationError('Debe asignarse un técnico antes de cerrar el pago.')

        informe = InformePago.objects.create(
            expediente=expediente,
            tecnico=tecnico,
            fecha_pago=fecha_pago,
            monto=monto,
            observaciones=observaciones
        )
        estado, _ = EstadoExpediente.objects.get_or_create(nombre='PAGO_CERRADO')
        expediente.estado = estado
        expediente.fecha_cierre = fecha_pago
        expediente.save(update_fields=['estado', 'fecha_cierre'])
        logger.info("Pago cerrado para expediente %s, informe %s", expediente.codigo, informe.id)
        return informe
