"""Servicio para gestión de documentos de legajos."""

from django.contrib.auth import get_user_model
from django.db import transaction

from celiaquia.models import ExpedienteCiudadano, TipoDocumento, DocumentoLegajo

User = get_user_model()


class DocumentosService:
    """Servicio para gestionar documentos de legajos."""

    @staticmethod
    @transaction.atomic
    def agregar_documento(
        legajo: ExpedienteCiudadano,
        tipo_documento_nombre: str,
        archivo,
        usuario: User = None,
        observaciones: str = "",
    ) -> DocumentoLegajo:
        """
        Agrega o reemplaza un documento en el legajo.

        Args:
            legajo: Legajo al que se agrega el documento
            tipo_documento_nombre: Nombre del tipo de documento
            archivo: Archivo a cargar
            usuario: Usuario que carga el documento
            observaciones: Observaciones opcionales

        Returns:
            DocumentoLegajo: Documento creado o actualizado
        """
        tipo_documento = TipoDocumento.objects.get(nombre=tipo_documento_nombre)

        # Si ya existe, actualizarlo
        documento, created = DocumentoLegajo.objects.update_or_create(
            legajo=legajo,
            tipo_documento=tipo_documento,
            defaults={
                "archivo": archivo,
                "usuario_carga": usuario,
                "observaciones": observaciones,
            },
        )

        # Actualizar archivos_ok
        legajo._recompute_archivos_ok()
        legajo.save(update_fields=["archivos_ok"])

        # Registrar en historial de comentarios
        try:
            from .comentarios_service import ComentariosService

            accion = "actualizado" if not created else "cargado"
            ComentariosService.agregar_comentario(
                legajo=legajo,
                tipo_comentario="OBSERVACION_GENERAL",
                comentario=f"Documento {tipo_documento.nombre} {accion}",
                usuario=usuario,
            )
        except ImportError:
            pass

        return documento

    @staticmethod
    def obtener_documentos_legajo(legajo: ExpedienteCiudadano):
        """Obtiene todos los documentos de un legajo."""
        return legajo.documentos.select_related("tipo_documento", "usuario_carga").all()

    @staticmethod
    def verificar_documentos_completos(
        legajo: ExpedienteCiudadano,
    ) -> tuple[bool, list]:
        """
        Verifica si el legajo tiene todos los documentos requeridos.

        Returns:
            tuple: (completo: bool, faltantes: list[TipoDocumento])
        """
        tipos_requeridos = TipoDocumento.objects.filter(requerido=True, activo=True)
        tipos_cargados = legajo.documentos.values_list("tipo_documento_id", flat=True)

        faltantes = tipos_requeridos.exclude(id__in=tipos_cargados)

        return not faltantes.exists(), list(faltantes)

    @staticmethod
    @transaction.atomic
    def eliminar_documento(
        legajo: ExpedienteCiudadano, tipo_documento_nombre: str, usuario: User = None
    ):
        """Elimina un documento del legajo."""
        try:
            documento = legajo.documentos.get(
                tipo_documento__nombre=tipo_documento_nombre
            )
            tipo_doc_nombre = documento.tipo_documento.nombre
            documento.delete()

            # Actualizar archivos_ok
            legajo._recompute_archivos_ok()
            legajo.save(update_fields=["archivos_ok"])

            # Registrar en historial
            try:
                from .comentarios_service import ComentariosService

                ComentariosService.agregar_comentario(
                    legajo=legajo,
                    tipo_comentario="OBSERVACION_GENERAL",
                    comentario=f"Documento {tipo_doc_nombre} eliminado",
                    usuario=usuario,
                )
            except ImportError:
                pass

            return True
        except DocumentoLegajo.DoesNotExist:
            return False

    @staticmethod
    def obtener_tipos_documento_activos():
        """Obtiene todos los tipos de documento activos."""
        return TipoDocumento.objects.filter(activo=True).order_by("orden", "nombre")

    @staticmethod
    def obtener_tipos_documento_requeridos():
        """Obtiene los tipos de documento requeridos."""
        return TipoDocumento.objects.filter(requerido=True, activo=True).order_by(
            "orden"
        )
