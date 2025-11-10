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
        except Exception:
            logger.exception(
                "Error en RendicionCuentasFinalService.actualizar_documento_con_archivo",
                extra={"documento_pk": getattr(documento, "pk", None)},
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
        except Exception:
            logger.exception(
                "Error en RendicionCuentasFinalService.adjuntar_archivo_a_documento",
                extra={"documento_id": documento_id},
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
        except Exception:
            logger.exception(
                "Error en RendicionCuentasFinalService.get_documentos_rendicion_cuentas_final",
                extra={
                    "rendicion_cuentas_final_pk": getattr(
                        rendicion_cuentas_final, "pk", None
                    )
                },
            )

            raise

    @staticmethod
    def filter_documentos_por_area(user, query):
        try:
            from users.services import (
                UserPermissionService,
            )  # pylint: disable=import-outside-toplevel

            filtros_validador = Q()
            is_coordinador = False
            duplas_ids = []

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

                # Coordinador de Gestión: ver documentos de duplas asignadas
                is_coordinador, duplas_ids = (
                    UserPermissionService.get_coordinador_duplas(user)
                )
                if is_coordinador:
                    filtros_validador |= Q(tipo__validador="Dupla")

            qs = DocumentoRendicionFinal.objects.filter(filtros_validador)

            # Filtrar por duplas asignadas si es coordinador
            if is_coordinador and duplas_ids and not user.is_superuser:
                qs = qs.filter(rendicion_final__comedor__dupla_id__in=duplas_ids)

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
        except Exception:
            logger.exception(
                "Error en RendicionCuentasFinalService.filter_documentos_por_area",
                extra={"user_pk": getattr(user, "pk", None), "query": query},
            )
            raise
