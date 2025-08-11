import logging
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from rendicioncuentasfinal.models import (
    EstadoDocumentoRendicionFinal,
    DocumentoRendicionFinal,
)
from historial.services.historial_service import HistorialService

logger = logging.getLogger("django")


class RendicionCuentasFinalService:
    @staticmethod
    def actualizar_documento_con_archivo(documento, archivo):
        try:
            with transaction.atomic():
                documento.documento = archivo
                documento.estado = EstadoDocumentoRendicionFinal.objects.get(
                    nombre="En análisis"
                )
                documento.fecha_modificacion = timezone.now()
                documento.save()
                HistorialService.registrar_historial(
                    accion="Adjuntar documento",
                    instancia=documento,
                )
        except Exception as e:
            logger.error(
                f"Ocurrió un error inesperado en RendicionCuentasFinalService.actualizar_documento_con_archivo para el documento: {documento} {e}",
                exc_info=True,
            )
            raise

    @staticmethod
    def adjuntar_archivo_a_documento(documento_id, archivo):
        try:
            documento = get_object_or_404(DocumentoRendicionFinal, id=documento_id)

            if not archivo:
                return False, documento

            RendicionCuentasFinalService.actualizar_documento_con_archivo(
                documento, archivo
            )

            return True, documento
        except Exception as e:
            logger.error(
                f"Ocurrió un error inesperado en RendicionCuentasFinalService.adjuntar_archivo_a_documento para el documento: {documento_id} {e}",
                exc_info=True,
            )
            raise

    @staticmethod
    def get_documentos_rendicion_cuentas_final(rendicion_cuentas_final):
        try:
            documentos = (
                rendicion_cuentas_final.documentos.select_related("tipo", "estado")
                .only(
                    "id",
                    "documento",
                    "observaciones",
                    "fecha_modificacion",
                    "tipo__nombre",
                    "tipo__validador",
                    "tipo__personalizado",
                    "estado__nombre",
                )
                .order_by("id")
            )

            return documentos
        except Exception as e:
            logger.error(
                f"Ocurrió un error inesperado en RendicionCuentasFinalService.get_documentos_rendicion_cuentas_final para la rendicion: {rendicion_cuentas_final} {e}",
                exc_info=True,
            )
            raise

    @staticmethod
    def filter_documentos_por_area(user, query):
        try:
            filtros_validador = Q()
            if user.is_superuser:
                filtros_validador = Q(
                    tipo__validador__in=["Contable", "Legales", "Dupla"]
                )
            else:
                if user.groups.filter(name="Area Contable").exists():
                    filtros_validador |= Q(tipo__validador="Contable")
                if user.groups.filter(name="Area Legales").exists():
                    filtros_validador |= Q(tipo__validador="Legales")
                if user.groups.filter(name="Tecnico Comedor").exists():
                    filtros_validador |= Q(tipo__validador="Dupla")

            qs = DocumentoRendicionFinal.objects.filter(filtros_validador)

            if query:
                qs = qs.filter(
                    Q(rendicion_final__comedor__nombre__icontains=query)
                    | Q(tipo__nombre__icontains=query)
                )

            qs = (
                qs.filter(estado__nombre__in=["En análisis", "Subsanar", "Validado"])
                .select_related("tipo", "estado", "rendicion_final__comedor")
                .order_by("-fecha_modificacion")
            )

            return qs
        except Exception as e:
            logger.error(
                f"Ocurrió un error inesperado en RendicionCuentasFinalService.filter_documentos_por_area para el usuario: {user} {e}",
                exc_info=True,
            )
            raise
