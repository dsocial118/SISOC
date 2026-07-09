from django.contrib import admin

from comedores.models import (
    CapacitacionComedorCertificado,
    ComedorDatosConvenioPnud,
    ColaboradorEspacio,
    Comedor,
    HistorialValidacion,
    ImagenComedor,
    Nomina,
    NominaDerivacion,
    Observacion,
    Programas,
    Referente,
    TipoDeComedor,
    ValorComida,
)


@admin.register(Comedor)
class ComedorAdmin(admin.ModelAdmin):
    list_display = [
        "nombre",
        "estado_validacion",
        "fecha_validado",
        "provincia",
        "municipio",
    ]
    list_filter = [
        "estado_validacion",
        "provincia",
        "ultimo_estado__estado_general__estado_actividad",
    ]
    search_fields = ["nombre", "codigo_de_proyecto"]
    readonly_fields = ["fecha_validado"]


@admin.register(HistorialValidacion)
class HistorialValidacionAdmin(admin.ModelAdmin):
    list_display = ["comedor", "estado_validacion", "usuario", "fecha_validacion"]
    list_filter = ["estado_validacion", "fecha_validacion"]
    search_fields = ["comedor__nombre", "usuario__username", "comentario"]
    readonly_fields = ["fecha_validacion"]


admin.site.register(Observacion)
admin.site.register(TipoDeComedor)
admin.site.register(ValorComida)
admin.site.register(Programas)
admin.site.register(Nomina)
admin.site.register(Referente)
admin.site.register(ImagenComedor)


@admin.register(ComedorDatosConvenioPnud)
class ComedorDatosConvenioPnudAdmin(admin.ModelAdmin):
    list_display = (
        "comedor",
        "nro_convenio",
        "monto_total_conveniado",
        "prestaciones_financiadas_mensuales",
        "personas_conveniadas",
        "actualizado_en",
    )
    search_fields = ("comedor__nombre", "nro_convenio")
    raw_id_fields = ("comedor",)
    readonly_fields = ("actualizado_en",)


@admin.register(ColaboradorEspacio)
class ColaboradorEspacioAdmin(admin.ModelAdmin):
    list_display = ("ciudadano", "comedor", "genero", "fecha_alta", "fecha_baja")
    list_filter = ("genero",)
    search_fields = (
        "ciudadano__apellido",
        "ciudadano__nombre",
        "ciudadano__documento",
        "comedor__nombre",
    )
    raw_id_fields = ("comedor", "ciudadano", "creado_por", "modificado_por")
    readonly_fields = ("fecha_creado", "fecha_modificado")


@admin.register(NominaDerivacion)
class NominaDerivacionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nomina_origen",
        "nomina_destino",
        "comedor_origen",
        "comedor_destino",
        "usuario",
        "fecha",
    )
    list_filter = ("fecha",)
    search_fields = (
        "usuario__username",
        "comedor_origen__nombre",
        "comedor_destino__nombre",
    )
    readonly_fields = (
        "nomina_origen",
        "nomina_destino",
        "comedor_origen",
        "comedor_destino",
        "usuario",
        "fecha",
        "motivo",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(CapacitacionComedorCertificado)
class CapacitacionComedorCertificadoAdmin(admin.ModelAdmin):
    list_display = (
        "comedor",
        "capacitacion",
        "estado",
        "fecha_presentacion",
        "fecha_revision",
    )
    list_filter = ("estado", "capacitacion")
    search_fields = ("comedor__nombre",)
    raw_id_fields = ("comedor", "presentado_por", "revisado_por")
    readonly_fields = ("observacion", "creado", "modificado")
