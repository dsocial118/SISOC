from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

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

        return documentos

    @staticmethod
    def filter_documentos_por_area(user, query):
        filtros_validador = Q()
        if user.is_superuser:
            filtros_validador = Q(tipo__validador__in=["Contable", "Legales"])
        else:
            if user.groups.filter(name="Area Contable").exists():
                filtros_validador |= Q(tipo__validador="Contable")
            if user.groups.filter(name="Area Legales").exists():
                filtros_validador |= Q(tipo__validador="Legales")

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
