from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404

from comedores.models import Comedor, HistorialValidacion


class ValidacionService:

    @staticmethod
    def puede_validar(user, comedor):
        """Verifica si el usuario puede validar el comedor"""
        return user.is_superuser or (
            comedor.dupla and user in comedor.dupla.tecnico.all()
        )

    @staticmethod
    def validar_comedor(comedor_id, user, accion, opciones=None, comentario=""):
        """Procesa la validación del comedor"""
        comedor = get_object_or_404(Comedor, pk=comedor_id)

        if not ValidacionService.puede_validar(user, comedor):
            return False, "No tiene permisos para validar este comedor."

        if accion == "validar":
            estado = "Validado"
            mensaje = "Comedor validado correctamente."
            opciones_guardadas = None
        elif accion == "no_validar":
            estado = "No Validado"
            mensaje = "Comedor marcado como no validado."

            # Validar que se seleccionó al menos una opción
            if not opciones or len(opciones) == 0:
                return False, "Debe seleccionar al menos una opción."

            # Si seleccionó "otro", el comentario es obligatorio
            if "otro" in opciones and not comentario.strip():
                return False, "El comentario es obligatorio cuando selecciona 'Otro'."

            opciones_guardadas = opciones
        else:
            return False, "Acción no válida."

        with transaction.atomic():
            # Actualizar comedor
            comedor.estado_validacion = estado
            comedor.fecha_validado = timezone.now()
            comedor.save(update_fields=["estado_validacion", "fecha_validado"])

            # Crear registro en historial
            HistorialValidacion.objects.create(
                comedor=comedor,
                usuario=user,
                estado_validacion=estado,
                opciones_no_validar=opciones_guardadas,
                comentario=comentario,
            )

        return True, mensaje

    @staticmethod
    def resetear_validaciones():
        """Resetea el estado de validación de todos los comedores a Pendiente."""

        return Comedor.objects.filter(
            estado_validacion__in=["Validado", "No Validado"]
        ).update(estado_validacion="Pendiente", fecha_validado=None)
