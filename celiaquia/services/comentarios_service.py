"""Servicio para gestión de historial de comentarios."""

from django.contrib.auth import get_user_model
from django.db import transaction

from celiaquia.models import ExpedienteCiudadano, HistorialComentarios

User = get_user_model()


class ComentariosService:
    """Servicio para gestionar el historial de comentarios y subsanaciones."""

    @staticmethod
    def agregar_comentario(
        legajo: ExpedienteCiudadano,
        tipo_comentario: str,
        comentario: str,
        usuario: User = None,
        archivo_adjunto=None,
        estado_relacionado: str = None,
    ) -> HistorialComentarios:
        """
        Agrega un comentario al historial del legajo.

        Args:
            legajo: Legajo al que se agrega el comentario
            tipo_comentario: Tipo de comentario (usar constantes de HistorialComentarios)
            comentario: Texto del comentario
            usuario: Usuario que realiza el comentario
            archivo_adjunto: Archivo opcional adjunto
            estado_relacionado: Estado del legajo al momento del comentario

        Returns:
            HistorialComentarios: Registro creado
        """
        return HistorialComentarios.objects.create(
            legajo=legajo,
            tipo_comentario=tipo_comentario,
            comentario=comentario,
            usuario=usuario,
            archivo_adjunto=archivo_adjunto,
            estado_relacionado=estado_relacionado or legajo.revision_tecnico,
        )

    @staticmethod
    def agregar_validacion_tecnica(
        legajo: ExpedienteCiudadano, comentario: str, usuario: User = None
    ) -> HistorialComentarios:
        """Agrega comentario de validación técnica."""
        return ComentariosService.agregar_comentario(
            legajo=legajo,
            tipo_comentario=HistorialComentarios.TIPO_VALIDACION_TECNICA,
            comentario=comentario,
            usuario=usuario,
            estado_relacionado=legajo.revision_tecnico,
        )

    @staticmethod
    def agregar_subsanacion_motivo(
        legajo: ExpedienteCiudadano, motivo: str, usuario: User = None
    ) -> HistorialComentarios:
        """Agrega motivo de subsanación al historial."""
        return ComentariosService.agregar_comentario(
            legajo=legajo,
            tipo_comentario=HistorialComentarios.TIPO_SUBSANACION_MOTIVO,
            comentario=motivo,
            usuario=usuario,
            estado_relacionado="SUBSANAR",
        )

    @staticmethod
    def agregar_subsanacion_respuesta(
        legajo: ExpedienteCiudadano,
        respuesta: str,
        usuario: User = None,
        archivo_adjunto=None,
    ) -> HistorialComentarios:
        """Agrega respuesta de subsanación al historial."""
        return ComentariosService.agregar_comentario(
            legajo=legajo,
            tipo_comentario=HistorialComentarios.TIPO_SUBSANACION_RESPUESTA,
            comentario=respuesta,
            usuario=usuario,
            archivo_adjunto=archivo_adjunto,
            estado_relacionado="SUBSANADO",
        )

    @staticmethod
    def agregar_validacion_renaper(
        legajo: ExpedienteCiudadano, comentario: str, usuario: User = None
    ) -> HistorialComentarios:
        """Agrega comentario de validación RENAPER."""
        return ComentariosService.agregar_comentario(
            legajo=legajo,
            tipo_comentario=HistorialComentarios.TIPO_RENAPER_VALIDACION,
            comentario=comentario,
            usuario=usuario,
            estado_relacionado=str(legajo.estado_validacion_renaper),
        )

    @staticmethod
    def agregar_cruce_sintys(
        legajo: ExpedienteCiudadano, observacion: str, usuario: User = None
    ) -> HistorialComentarios:
        """Agrega observación de cruce SINTYS."""
        return ComentariosService.agregar_comentario(
            legajo=legajo,
            tipo_comentario=HistorialComentarios.TIPO_CRUCE_SINTYS,
            comentario=observacion,
            usuario=usuario,
            estado_relacionado=legajo.resultado_sintys,
        )

    @staticmethod
    def agregar_observacion_pago(
        legajo: ExpedienteCiudadano, observacion: str, usuario: User = None
    ) -> HistorialComentarios:
        """Agrega observación de pago."""
        return ComentariosService.agregar_comentario(
            legajo=legajo,
            tipo_comentario=HistorialComentarios.TIPO_PAGO_OBSERVACION,
            comentario=observacion,
            usuario=usuario,
        )

    @staticmethod
    def obtener_historial_legajo(legajo: ExpedienteCiudadano):
        """Obtiene todo el historial de comentarios de un legajo."""
        return legajo.historial_comentarios.select_related("usuario").all()

    @staticmethod
    def obtener_comentarios_por_tipo(legajo: ExpedienteCiudadano, tipo_comentario: str):
        """Obtiene comentarios de un tipo específico para un legajo."""
        return legajo.historial_comentarios.filter(
            tipo_comentario=tipo_comentario
        ).select_related("usuario")

    @staticmethod
    @transaction.atomic
    def migrar_comentarios_existentes():
        """
        Migra comentarios existentes desde los campos actuales al historial.
        Ejecutar una sola vez después de crear la tabla.
        """
        legajos_con_comentarios = ExpedienteCiudadano.objects.filter(
            models.Q(subsanacion_motivo__isnull=False)
            | models.Q(subsanacion_renaper_comentario__isnull=False)
            | models.Q(observacion_cruce__isnull=False)
        ).exclude(
            models.Q(subsanacion_motivo="")
            & models.Q(subsanacion_renaper_comentario="")
            & models.Q(observacion_cruce="")
        )

        migrados = 0
        for legajo in legajos_con_comentarios:
            # Migrar motivo de subsanación
            if legajo.subsanacion_motivo:
                ComentariosService.agregar_subsanacion_motivo(
                    legajo=legajo,
                    motivo=legajo.subsanacion_motivo,
                    usuario=legajo.subsanacion_usuario,
                )
                migrados += 1

            # Migrar comentario RENAPER
            if legajo.subsanacion_renaper_comentario:
                ComentariosService.agregar_validacion_renaper(
                    legajo=legajo, comentario=legajo.subsanacion_renaper_comentario
                )
                migrados += 1

            # Migrar observación de cruce
            if legajo.observacion_cruce:
                ComentariosService.agregar_cruce_sintys(
                    legajo=legajo, observacion=legajo.observacion_cruce
                )
                migrados += 1

        return migrados
