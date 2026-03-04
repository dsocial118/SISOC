"""
Serializers para la API de core.
"""

from rest_framework import serializers

SEXO_CHOICES = ("M", "F", "X")


class RenaperConsultaSerializer(serializers.Serializer):
    """
    Serializer para validar entrada en consulta a RENAPER.
    No es un ModelSerializer (no persiste a BD).
    """

    dni = serializers.CharField(
        required=True,
        min_length=1,
        help_text="DNI del ciudadano (ej: 12345678)",
    )
    sexo = serializers.CharField(
        required=True,
        help_text="Sexo: M, F o X (case-insensitive)",
    )

    def validate_dni(self, value):
        """Valida que el DNI no sea vacío y sea alfanumérico."""
        if not value or not value.strip():
            raise serializers.ValidationError("DNI no puede estar vacío.")
        return value.strip()

    def validate_sexo(self, value):
        """Normaliza sexo a mayúscula y valida que sea M, F o X."""
        if not value:
            raise serializers.ValidationError("Sexo no puede estar vacío.")
        sexo_normalized = value.upper()
        if sexo_normalized not in SEXO_CHOICES:
            raise serializers.ValidationError(
                f"Sexo debe ser uno de: {', '.join(SEXO_CHOICES)}"
            )
        return sexo_normalized

    def create(self, validated_data):
        """No se usa (serializer solo valida, no persiste)."""
        raise NotImplementedError("Este serializer no persiste datos.")

    def update(self, instance, validated_data):
        """No se usa (serializer solo valida, no persiste)."""
        raise NotImplementedError("Este serializer no persiste datos.")
