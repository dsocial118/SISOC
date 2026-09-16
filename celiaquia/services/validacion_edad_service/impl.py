"""
Servicio de validación de edad para menores y responsables en celiaquía.
Implementa los requerimientos:
- Responsable menor de 18 años: BLOQUEO
- Beneficiario menor sin responsable: BLOQUEO
"""

from datetime import date
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger("django")


class ValidacionEdadService:
    """Validaciones de edad para beneficiarios y responsables."""

    @staticmethod
    def calcular_edad(fecha_nacimiento):
        """Calcula la edad en años a partir de una fecha de nacimiento."""
        if not fecha_nacimiento:
            return None
        try:
            hoy = date.today()
            edad = (hoy - fecha_nacimiento).days // 365
            return edad
        except Exception as e:
            logger.warning("Error calculando edad: %s", e)
            return None

    @staticmethod
    def validar_responsable_mayor_edad(fecha_nacimiento_responsable):
        """
        Requerimiento 1: Responsable menor de 18 años (BLOQUEO)

        Si una persona tiene el rol de Responsable y su edad es menor a 18 años,
        se rechaza la fila y se marca como error.

        Args:
            fecha_nacimiento_responsable: fecha de nacimiento del responsable

        Raises:
            ValidationError: si el responsable es menor de 18 años
        """
        if not fecha_nacimiento_responsable:
            return True

        edad = ValidacionEdadService.calcular_edad(fecha_nacimiento_responsable)

        if edad is None:
            return True

        if edad < 18:
            raise ValidationError(
                f"El responsable no puede ser menor de 18 años (edad: {edad})"
            )

        return True

    @staticmethod
    def validar_beneficiario_menor_con_responsable(
        fecha_nacimiento_beneficiario, tiene_responsable
    ):
        """
        Requerimiento 2: Beneficiario menor sin responsable (BLOQUEO)

        Si el beneficiario es menor de 18 años, debe existir un responsable asociado.
        Si no hay responsable, se rechaza la fila.

        Args:
            fecha_nacimiento_beneficiario: fecha de nacimiento del beneficiario
            tiene_responsable: bool indicando si hay responsable asociado

        Raises:
            ValidationError: si el beneficiario es menor y no tiene responsable
        """
        if not fecha_nacimiento_beneficiario:
            return True

        edad = ValidacionEdadService.calcular_edad(fecha_nacimiento_beneficiario)

        if edad is None:
            return True

        if edad < 18 and not tiene_responsable:
            raise ValidationError(
                "El beneficiario menor de 18 años debe tener un responsable"
            )

        return True

    @staticmethod
    def validar_relacion_responsable_beneficiario(
        fecha_nacimiento_responsable, fecha_nacimiento_beneficiario
    ):
        """
        Validación adicional: responsable no puede ser más joven que beneficiario.

        Args:
            fecha_nacimiento_responsable: fecha de nacimiento del responsable
            fecha_nacimiento_beneficiario: fecha de nacimiento del beneficiario

        Raises:
            ValidationError: si el responsable es más joven que el beneficiario
        """
        if not fecha_nacimiento_responsable or not fecha_nacimiento_beneficiario:
            return True

        edad_responsable = ValidacionEdadService.calcular_edad(
            fecha_nacimiento_responsable
        )
        edad_beneficiario = ValidacionEdadService.calcular_edad(
            fecha_nacimiento_beneficiario
        )

        if edad_responsable is None or edad_beneficiario is None:
            return True

        if edad_responsable < edad_beneficiario:
            raise ValidationError(
                f"El responsable ({edad_responsable} años) no puede ser más joven "
                f"que el beneficiario ({edad_beneficiario} años)"
            )

        return True
