# services/expediente_service.py
import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from celiaquia.models import EstadoExpediente, Expediente
from celiaquia.services.importacion_service import ImportacionService

logger = logging.getLogger(__name__)
User = get_user_model()

class ExpedienteService:
    @staticmethod
    @transaction.atomic
    def create_expediente(usuario_provincia, datos_metadatos, excel_masivo):
        """
        Crea un nuevo Expediente en estado 'CREADO' con metadatos y archivo.
        Valida que el código sea obligatorio y único.
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
    def procesar_expediente(expediente):
        """
        Crea o enlaza todos los legajos desde el Excel y cambia el estado a 'PROCESADO'.
        Devuelve dict con conteo: {'creados', 'errores'}.
        """
        if not expediente.excel_masivo:
            raise ValidationError('No hay archivo Excel cargado para procesar.')

        # Importar legajos y capturar conteo
        result = ImportacionService.importar_legajos_desde_excel(
            expediente,
            expediente.excel_masivo
        )

        # Cambiar estado a PROCESADO
        estado, _ = EstadoExpediente.objects.get_or_create(nombre='PROCESADO')
        expediente.estado = estado
        expediente.save(update_fields=['estado'])
        logger.info(
            "Expediente %s procesado: %s legajos creados, %s errores",
            expediente.codigo, result['validos'], result['errores']
        )
        return {
            'creados': result['validos'],
            'errores': result['errores']
        }

    @staticmethod
    @transaction.atomic
    def confirmar_envio(expediente):
        """
        Importa legajos si no se procesaron y cambia estado a 'ENVIADO'.
        Devuelve dict con conteo de legajos.
        """
        if not expediente.excel_masivo:
            raise ValidationError('No hay archivo Excel cargado para confirmar.')

        # Reutilizar importación masiva
        result = ImportacionService.importar_legajos_desde_excel(
            expediente,
            expediente.excel_masivo
        )
        logger.info("ImportService returned: %r", result)

        # Actualizar estado
        estado, _ = EstadoExpediente.objects.get_or_create(nombre='ENVIADO')
        expediente.estado = estado
        expediente.save(update_fields=['estado'])
        logger.info(
            "Expediente %s enviado: %s legajos creados, %s errores",
            expediente.codigo, result['validos'], result['errores']
        )
        return result


