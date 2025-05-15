from django.shortcuts import get_object_or_404
from django.utils import timezone

from comedores.models.comedor import (
    DocumentoRendicionFinal,
    EstadoDocumentoRendicionFinal,
)


class RendicionCuentasFinalService:
    @staticmethod
    def actualizar_documento_con_archivo(documento, archivo):
        documento.documento = archivo
        documento.estado = EstadoDocumentoRendicionFinal.objects.get(
            nombre="En análisis"
        )
        documento.fecha_modificacion = timezone.now()
        documento.save()

    @staticmethod
    def adjuntar_archivo_a_documento(documento_id, archivo):
        documento = get_object_or_404(DocumentoRendicionFinal, id=documento_id)

        if not archivo:
            return False, documento

        RendicionCuentasFinalService.actualizar_documento_con_archivo(
            documento, archivo
        )
        return True, documento
