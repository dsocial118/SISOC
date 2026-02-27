import logging
import json
from datetime import date, datetime, time
from decimal import Decimal
from django.contrib.contenttypes.models import ContentType
from rendicioncuentasfinal.models import DocumentoRendicionFinal
from config.middlewares.threadlocals import get_current_user
from historial.models import Historial


logger = logging.getLogger("django")


class HistorialService:
    @staticmethod
    def _json_safe(value):
        """Convert arbitrary Python values to JSON-serializable equivalents.

        - Decimal -> str (to avoid precision loss)
        - date/datetime/time -> ISO string
        - dict/list/tuple/set -> recursively processed
        - QuerySet/manager `.all()` -> list of stringified items
        - Django model instances and other non-serializables -> str(value)
        """

        # Primitive cases first
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, (datetime, date, time)):
            try:
                return value.isoformat()
            except Exception:
                return str(value)

        # Collections
        if isinstance(value, dict):
            return {str(k): HistorialService._json_safe(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [HistorialService._json_safe(v) for v in value]

        # Relations like QuerySet
        try:
            if hasattr(value, "all") and callable(getattr(value, "all")):
                return [HistorialService._json_safe(v) for v in value.all()]
        except Exception:
            pass

        # If already JSON serializable, return as-is
        try:
            json.dumps(value)
            return value
        except TypeError:
            # Fallback: stringify
            return str(value)

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
            # Ensure `diferencias` is JSON-serializable
            diferencias_safe = (
                HistorialService._json_safe(diferencias)
                if diferencias is not None
                else None
            )

            return Historial.objects.create(
                usuario=usuario,
                accion=accion,
                content_type=content_type,
                object_id=object_id,
                diferencias=diferencias_safe,
            )
        except Exception:
            logger.exception(
                f"Error en HistorialService.registrar_historial para instancia {instancia}",
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

        except Exception:
            logger.exception(
                "Error en HistorialService.get_historial_documentos_by_rendicion_cuentas_final",
                extra={
                    "rendicion_cuentas_final_pk": getattr(
                        rendicion_cuentas_final, "pk", None
                    )
                },
            )
            raise
