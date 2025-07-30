# services/expediente_service.py
import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from celiaquia.models import EstadoExpediente, Expediente
from celiaquia.services.importacion_service import ImportacionService
from celiaquia.services.legajo_service import LegajoService

logger = logging.getLogger(__name__)
User = get_user_model()

class ExpedienteService:
    @staticmethod
    @transaction.atomic
    def create_expediente(usuario_provincia, datos_metadatos, excel_masivo):
        """
        Crea un nuevo Expediente en estado 'CREADO' con metadatos y archivo.
        """
        codigo = datos_metadatos.get("codigo")
        if not codigo:
            raise ValidationError("El código del expediente es obligatorio.")
        if Expediente.objects.filter(codigo=codigo).exists():
            raise ValidationError(f"Ya existe un expediente con código {codigo}.")

        estado, _ = EstadoExpediente.objects.get_or_create(nombre="CREADO")
        expediente = Expediente.objects.create(
            codigo=codigo,
            usuario_provincia=usuario_provincia,
            estado=estado,
            observaciones=datos_metadatos.get("observaciones", ""),
            excel_masivo=excel_masivo,
        )
        logger.info("Expediente %s creado por %s", expediente.codigo, usuario_provincia.username)
        return expediente

    @staticmethod
    @transaction.atomic
    def procesar_expediente(expediente, usuario):
        """
        Crea o enlaza todos los legajos desde el Excel y cambia el estado a 'PROCESADO'.
        """
        if not expediente.excel_masivo:
            raise ValidationError("No hay archivo Excel cargado para procesar.")

        result = ImportacionService.importar_legajos_desde_excel(
            expediente, expediente.excel_masivo, usuario
        )

        # Estado PROCESADO
        estado, _ = EstadoExpediente.objects.get_or_create(nombre="PROCESADO")
        expediente.estado = estado
        expediente.save(update_fields=["estado"])
        logger.info(
            "Expediente %s procesado: %s legajos creados, %s errores",
            expediente.codigo, result["validos"], result["errores"]
        )
        return {"creados": result["validos"], "errores": result["errores"]}

    @staticmethod
    @transaction.atomic
    def confirmar_envio(expediente):
        """
        Verifica que todos los legajos tengan archivo (EN_ESPERA),
        y luego cambia el estado a 'CONFIRMACION_DE_ENVIO'.
        """
        # Asegurar que todos los legajos tienen archivo
        if not LegajoService.all_legajos_loaded(expediente):
            raise ValidationError("Debes subir un archivo para cada legajo antes de confirmar.")

        # Cambiar estado a CONFIRMACION_DE_ENVIO
        estado, _ = EstadoExpediente.objects.get_or_create(nombre="CONFIRMACION_DE_ENVIO")
        expediente.estado = estado
        expediente.save(update_fields=["estado"])
        logger.info("Expediente %s confirmado (ENVÍO) con %d legajos.", expediente.codigo, expediente.expediente_ciudadanos.count())
        return {"validos": expediente.expediente_ciudadanos.count(), "errores": 0}

    @staticmethod
    @transaction.atomic
    def asignar_tecnico(expediente, tecnico):
        """
        Asigna un técnico y cambia el estado a 'ASIGNADO'.
        """
        if isinstance(tecnico, int):
            tecnico = User.objects.get(pk=tecnico)
        expediente.asignacion_tecnico.tecnico = tecnico
        expediente.asignacion_tecnico.save(update_fields=["tecnico"])
        estado, _ = EstadoExpediente.objects.get_or_create(nombre="ASIGNADO")
        expediente.estado = estado
        expediente.save(update_fields=["estado"])
        logger.info("Técnico %s asignado al expediente %s", tecnico.username, expediente.codigo)
        return expediente
