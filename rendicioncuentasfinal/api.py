"""Capacidades públicas del dominio Rendición de Cuentas Final."""

from django.contrib.contenttypes.models import ContentType

from rendicioncuentasfinal.models import DocumentoRendicionFinal


def obtener_content_type_id_documento() -> int:
    """Devuelve el identificador del tipo de contenido de sus documentos."""

    return ContentType.objects.get_for_model(DocumentoRendicionFinal).pk
