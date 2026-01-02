"""Servicio para gestión de asignaciones de técnicos."""

from django.contrib.auth import get_user_model
from django.db import transaction

from celiaquia.models import Expediente, AsignacionTecnico

User = get_user_model()


class AsignacionService:
    """Servicio para gestionar asignaciones de técnicos a expedientes."""
    
    @staticmethod
    @transaction.atomic
    def asignar_tecnico(expediente: Expediente, tecnico: User, usuario_asignador: User = None):
        """
        Asigna un técnico a un expediente.
        Desactiva asignaciones anteriores si existen.
        """
        # Desactivar asignaciones anteriores
        AsignacionTecnico.objects.filter(
            expediente=expediente,
            activa=True
        ).update(activa=False)
        
        # Crear nueva asignación
        asignacion = AsignacionTecnico.objects.create(
            expediente=expediente,
            tecnico=tecnico,
            activa=True
        )
        
        # Registrar comentario si hay servicio disponible
        try:
            from .comentarios_service import ComentariosService
            for legajo in expediente.expediente_ciudadanos.all():
                ComentariosService.agregar_comentario(
                    legajo=legajo,
                    tipo_comentario='OBSERVACION_GENERAL',
                    comentario=f'Expediente asignado a técnico: {tecnico.username}',
                    usuario=usuario_asignador
                )
        except ImportError:
            pass
        
        return asignacion
    
    @staticmethod
    def obtener_tecnico_activo(expediente: Expediente):
        """Obtiene el técnico actualmente asignado al expediente."""
        try:
            asignacion = AsignacionTecnico.objects.get(
                expediente=expediente,
                activa=True
            )
            return asignacion.tecnico
        except AsignacionTecnico.DoesNotExist:
            return None
    
    @staticmethod
    def desasignar_tecnico(expediente: Expediente, usuario_desasignador: User = None):
        """Desasigna el técnico actual del expediente."""
        asignaciones_activas = AsignacionTecnico.objects.filter(
            expediente=expediente,
            activa=True
        )
        
        for asignacion in asignaciones_activas:
            asignacion.activa = False
            asignacion.save()
            
            # Registrar comentario
            try:
                from .comentarios_service import ComentariosService
                for legajo in expediente.expediente_ciudadanos.all():
                    ComentariosService.agregar_comentario(
                        legajo=legajo,
                        tipo_comentario='OBSERVACION_GENERAL',
                        comentario=f'Técnico {asignacion.tecnico.username} desasignado del expediente',
                        usuario=usuario_desasignador
                    )
            except ImportError:
                pass
        
        return asignaciones_activas.count()
    
    @staticmethod
    def obtener_expedientes_asignados(tecnico: User):
        """Obtiene todos los expedientes activamente asignados a un técnico."""
        asignaciones = AsignacionTecnico.objects.filter(
            tecnico=tecnico,
            activa=True
        ).select_related('expediente')
        
        return [asignacion.expediente for asignacion in asignaciones]
    
    @staticmethod
    def obtener_historial_asignaciones(expediente: Expediente):
        """Obtiene el historial completo de asignaciones de un expediente."""
        return AsignacionTecnico.objects.filter(
            expediente=expediente
        ).select_related('tecnico').order_by('-fecha_asignacion')