import logging
from django.contrib.contenttypes.models import ContentType
from rendicioncuentasfinal.models import DocumentoRendicionFinal
from config.middlewares.threadlocals import get_current_user
from historial.models import Historial


logger = logging.getLogger(__name__)


class HistorialService:
    @staticmethod
    def registrar_historial(
        accion: str,
        instancia: object,
        diferencias: dict = None,
    ):
        """
        Registra un evento en el historial.

        Parámetros:
          - accion: descripción de la acción.
          - instancia: objeto Django; se usará para content_type y object_id.
          - diferencias: dict con diferencias a registrar.
        """
        usuario = get_current_user()

        if instancia is None:
            raise ValueError("Debe especificar 'instancia'")

        try:
            usuario = get_current_user()
            content_type = ContentType.objects.get_for_model(instancia)
            object_id = str(instancia.pk)
            return Historial.objects.create(
                usuario=usuario,
                accion=accion,
                content_type=content_type,
                object_id=object_id,
                diferencias=diferencias,
            )
        except Exception as e:
            logger.exception(
                f"Error en HistorialService.registrar_historial para instancia {instancia}: {e}",
            )
            raise

    @staticmethod
    def get_historial_documentos_by_rendicion_cuentas_final(
        rendicion_cuentas_final,
    ):
        """
        Devuelve el historial asociado a los documentos de una instancia dada de RendicionCuentasFinal.
        Args:
            rendicion_cuentas_final: Una instancia de RendicionCuentasFinal
        """
        try:
            content_type = ContentType.objects.get_for_model(DocumentoRendicionFinal)
            documentos_ids = rendicion_cuentas_final.documentos.values_list(
                "pk", flat=True
            ).iterator()

            return Historial.objects.filter(
                content_type=content_type,
                object_id__in=map(str, documentos_ids),
            ).order_by("-fecha")

        except Exception as e:
            logger.error(
                f"Error en HistorialService.get_historial_documentos_by_rendicion_cuentas_final: {e}",
                exc_info=True,
            )
            raise
