from rest_framework import serializers
from .models import (
    AnexoFormacion,
    AnexoSocioProductivo,
    Observacion,
    PersonaJuridica,
    PersonaFisica,
    LineaDeAccion,
    DiagnosticoJuridica,
    DiagnosticoFisica,
    Presupuesto,
    Proyecto,
)


class ObservacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Observacion
        fields = "__all__"


class PersonaJuridicaSerializer(serializers.ModelSerializer):
    provincia = serializers.StringRelatedField()
    proyecto_rubro = serializers.StringRelatedField()
    proyecto_objetivo = serializers.StringRelatedField()
    tipo = serializers.StringRelatedField()
    proyecto_tipo_actividad = serializers.StringRelatedField()

    class Meta:
        model = PersonaJuridica
        fields = "__all__"


class PersoneriaPersonaSerializer(serializers.ModelSerializer):
    provincia = serializers.StringRelatedField()
    proyecto_rubro = serializers.StringRelatedField()
    proyecto_objetivo = serializers.StringRelatedField()
    proyecto_tipo_actividad = serializers.StringRelatedField()

    class Meta:
        model = PersonaFisica
        fields = "__all__"


class PresupuestoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Presupuesto
        fields = "__all__"


class LineaDeAccionSerializer(serializers.ModelSerializer):
    presupuestos = PresupuestoSerializer(many=True, read_only=True)

    class Meta:
        model = LineaDeAccion
        fields = "__all__"


class DiagnosticoJuridicaSerializer(serializers.ModelSerializer):
    rubro = serializers.StringRelatedField()
    tipo_inmueble = serializers.StringRelatedField()
    comprador = serializers.StringRelatedField()
    cantidad_clientes = serializers.StringRelatedField()
    lugar_comercializacion = serializers.StringRelatedField()
    modalidad_comercializacion = serializers.StringRelatedField()
    fijacion_precios = serializers.StringRelatedField()
    cantidad_competidores = serializers.StringRelatedField()
    conocimiento_competidores = serializers.StringRelatedField()
    interactua_compentidores = serializers.StringRelatedField()
    modalidad_compras = serializers.StringRelatedField()
    plazo_compra_credito = serializers.StringRelatedField()
    medio_planificacion = serializers.StringRelatedField()
    modalidad_ciclo_productivo = serializers.StringRelatedField()
    cantidad_integrantes = serializers.StringRelatedField()
    genero_mayoria = serializers.StringRelatedField()
    tipo_actividad = serializers.StringRelatedField(many=True)
    tipo_dispositivos_moviles = serializers.StringRelatedField(many=True)
    plataforma_comunicacion = serializers.StringRelatedField(many=True)
    redes_sociales = serializers.StringRelatedField(many=True)
    canales_ventas = serializers.StringRelatedField(many=True)
    destino_materiales_recuperados = serializers.StringRelatedField(many=True)
    tipo_comunidad = serializers.StringRelatedField(many=True)

    class Meta:
        model = DiagnosticoJuridica
        fields = "__all__"


class DiagnosticoFisicaSerializer(serializers.ModelSerializer):
    rubro = serializers.StringRelatedField()
    tipo_inmueble = serializers.StringRelatedField()
    tipo_internet = serializers.StringRelatedField()
    comprador = serializers.StringRelatedField()
    cantidad_clientes = serializers.StringRelatedField()
    lugar_comercializacion = serializers.StringRelatedField()
    modalidad_comercializacion = serializers.StringRelatedField()
    fijacion_precios = serializers.StringRelatedField()
    cantidad_competidores = serializers.StringRelatedField()
    conocimiento_competidores = serializers.StringRelatedField()
    interactua_compentidores = serializers.StringRelatedField()
    modalidad_compras = serializers.StringRelatedField()
    plazo_compra_credito = serializers.StringRelatedField()
    medio_planificacion = serializers.StringRelatedField()
    modalidad_ciclo_productivo = serializers.StringRelatedField()
    ocupacion = serializers.StringRelatedField()
    ocupacion_condicion = serializers.StringRelatedField()
    ocupacion_horas_semanales = serializers.StringRelatedField()
    familia_ingreso_promedio = serializers.StringRelatedField()
    tipo_actividad = serializers.StringRelatedField(many=True)
    tipo_dispositivos_moviles = serializers.StringRelatedField(many=True)
    plataforma_comunicacion = serializers.StringRelatedField(many=True)
    redes_sociales = serializers.StringRelatedField(many=True)
    canales_ventas = serializers.StringRelatedField(many=True)
    destino_materiales_recuperados = serializers.StringRelatedField(many=True)
    estudios_alcanzados = serializers.StringRelatedField(many=True)

    class Meta:
        model = DiagnosticoFisica
        fields = "__all__"


class AnexoSocioProductivoSerializer(serializers.ModelSerializer):
    juridica = PersonaJuridicaSerializer()
    fisica = PersoneriaPersonaSerializer()
    linea_de_accion = LineaDeAccionSerializer()
    diagnostico_juridica = DiagnosticoJuridicaSerializer()
    diagnostico_fisica = DiagnosticoFisicaSerializer()

    class Meta:
        model = AnexoSocioProductivo
        fields = "__all__"


class AnexoFormacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnexoFormacion
        fields = "__all__"


class ProyectoSerializer(serializers.ModelSerializer):
    anexos_socioproductivos = AnexoSocioProductivoSerializer(many=True, read_only=True)
    anexos_formaciones = AnexoFormacionSerializer(many=True, read_only=True)
    observaciones = ObservacionSerializer(many=True, read_only=True)

    class Meta:
        model = Proyecto
        fields = "__all__"
