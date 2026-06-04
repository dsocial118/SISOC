from django.contrib import admin

from ver_para_ser_libre.models import (
    CasoLaboratorioVPSL,
    ChecklistJornadaVPSL,
    CierreDiarioVPSL,
    HistorialChecklistSedeVPSL,
    HistorialCierreDiarioVPSL,
    HistorialEstadoVPSL,
    HistorialLaboratorioVPSL,
    ItinerarioVPSL,
    EvaluacionSedeItinerarioVPSL,
    JornadaVPSL,
    RegistroNominalVPSL,
    SedeVPSL,
)


@admin.register(ItinerarioVPSL)
class ItinerarioVPSLAdmin(admin.ModelAdmin):
    list_display = ("codigo", "provincia", "fecha_inicio", "fecha_fin", "estado")
    list_filter = ("estado", "provincia")
    search_fields = ("codigo", "referente_nombre", "localidades_tentativas")


@admin.register(JornadaVPSL)
class JornadaVPSLAdmin(admin.ModelAdmin):
    list_display = ("itinerario", "fecha", "sede", "localidad", "estado")
    list_filter = ("estado", "fecha")
    search_fields = ("sede", "referente_nombre", "itinerario__codigo")


admin.site.register(ChecklistJornadaVPSL)
admin.site.register(RegistroNominalVPSL)
admin.site.register(CasoLaboratorioVPSL)
admin.site.register(CierreDiarioVPSL)
admin.site.register(HistorialEstadoVPSL)
admin.site.register(EvaluacionSedeItinerarioVPSL)
admin.site.register(SedeVPSL)
admin.site.register(HistorialChecklistSedeVPSL)
admin.site.register(HistorialLaboratorioVPSL)
admin.site.register(HistorialCierreDiarioVPSL)
