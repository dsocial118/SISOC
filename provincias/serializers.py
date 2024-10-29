from rest_framework import serializers
from .models import (
    AnexoSocioProductivo,
    PersoneriaOrganizacion,
    PersoneriaPersona,
    LineaDeAccion,
    DiagnosticoOrganizacion,
    DiagnosticoPersona,
)


class PersoneriaOrganizacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersoneriaOrganizacion
        fields = "__all__"


class PersoneriaPersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersoneriaPersona
        fields = "__all__"


class LineaDeAccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineaDeAccion
        fields = "__all__"


class DiagnosticoOrganizacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticoOrganizacion
        fields = "__all__"


class DiagnosticoPersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticoPersona
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
