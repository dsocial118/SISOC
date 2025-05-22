from django.shortcuts import get_object_or_404
from django.utils import timezone

from comedores.models.comedor import (
    DocumentoRendicionFinal,
    EstadoDocumentoRendicionFinal,
)
from historial.services.historial_service import HistorialService


class RendicionCuentasFinalService:
    @staticmethod
    def actualizar_documento_con_archivo(documento, archivo):
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

    @staticmethod
    def adjuntar_archivo_a_documento(documento_id, archivo):
        documento = get_object_or_404(DocumentoRendicionFinal, id=documento_id)

        if not archivo:
            return False, documento

        RendicionCuentasFinalService.actualizar_documento_con_archivo(
            documento, archivo
        )

        return True, documento

    @staticmethod
    def get_documentos_rendicion_cuentas_final(rendicion_cuentas_final):
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
        for documento in documentos:
            documento.editable = documento.estado.nombre in {
                "No presentado",
                "Subsanar",
            }
            documento.validable = (
                documento.tipo.validador == "Dupla"
                and documento.estado.nombre == "En análisis"
            )
            documento.eliminable = (
                documento.tipo.personalizado
                and documento.estado.nombre == "En análisis"
            )

        return documentos
