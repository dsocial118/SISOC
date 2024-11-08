from rest_framework import serializers
from .models import (
    AnexoSocioProductivo,
    PersonaJuridica,
    PersonaFisica,
    LineaDeAccion,
    DiagnosticoJuridica,
    DiagnosticoFisica,
)


class PersoneriaOrganizacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonaJuridica
        fields = "__all__"


class PersoneriaPersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonaFisica
        fields = "__all__"


class LineaDeAccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineaDeAccion
        fields = "__all__"


class DiagnosticoOrganizacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticoJuridica
        fields = "__all__"


class DiagnosticoPersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticoFisica
        fields = "__all__"


class AnexoSocioProductivoSerializer(serializers.ModelSerializer):
    organizacion = PersoneriaOrganizacionSerializer()
    persona = PersoneriaPersonaSerializer()
    linea_de_accion = LineaDeAccionSerializer()
    diagnostico_organizacion = DiagnosticoOrganizacionSerializer()
    diagnostico_persona = DiagnosticoPersonaSerializer()

    class Meta:
        model = AnexoSocioProductivo
        fields = "__all__"
