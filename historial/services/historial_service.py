from django.contrib.contenttypes.models import ContentType

from rendicioncuentasfinal.models import DocumentoRendicionFinal
from config.middlewares.threadlocals import get_current_user
from historial.models import Historial


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

        if instancia is not None:
            content_type = ContentType.objects.get_for_model(instancia)
            object_id = str(instancia.pk)

            return Historial.objects.create(
                usuario=usuario,
                accion=accion,
                content_type=content_type,
                object_id=object_id,
                diferencias=diferencias,
            )
        else:
            raise ValueError("Debe especificar 'instancia'")

    @staticmethod
    def get_historial_documentos_by_rendicion_cuentas_final(
        rendicion_cuentas_final,
    ):
        """
        Devuelve el historial asociado a los documentos de una instancia dada de RendicionCuentasFinal.
        Args:
            rendicion_cuentas_final: Una instancia de RendicionCuentasFinal
        """

        content_type = ContentType.objects.get_for_model(DocumentoRendicionFinal)
        documentos_ids = rendicion_cuentas_final.documentos.values_list("pk", flat=True)

        return Historial.objects.filter(
            content_type=content_type, object_id__in=[str(pk) for pk in documentos_ids]
        ).order_by("-fecha")
