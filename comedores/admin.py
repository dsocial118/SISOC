from django.contrib import admin

from comedores.models import (
    Comedor,
    Observacion,
    TipoDeComedor,
    ValorComida,
    Programas,
    Nomina,
    Referente,
    ImagenComedor,
    HistorialValidacion,
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
    list_filter = ["estado_validacion", "provincia", "estado_general"]
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
