from django.contrib import admin

from ciudadanos.models import (
    Ciudadano,
    GrupoFamiliar,
    ProgramaTransferencia,
    HistorialTransferencia,
    Interaccion,
)


@admin.register(Ciudadano)
class CiudadanoAdmin(admin.ModelAdmin):
    list_display = ("apellido", "nombre", "tipo_documento", "documento", "activo")
    search_fields = ("apellido", "nombre", "documento")
    list_filter = ("activo", "tipo_documento", "sexo")
    readonly_fields = ("creado", "modificado")


@admin.register(GrupoFamiliar)
class GrupoFamiliarAdmin(admin.ModelAdmin):
    list_display = ("ciudadano_1", "ciudadano_2", "vinculo", "conviven")
    search_fields = (
        "ciudadano_1__apellido",
        "ciudadano_1__nombre",
        "ciudadano_2__apellido",
        "ciudadano_2__nombre",
    )
    list_filter = ("vinculo", "estado_relacion", "conviven", "cuidador_principal")
    autocomplete_fields = ("ciudadano_1", "ciudadano_2")


@admin.register(ProgramaTransferencia)
class ProgramaTransferenciaAdmin(admin.ModelAdmin):
    list_display = (
        "ciudadano",
        "tipo",
        "categoria",
        "monto",
        "cantidad_texto",
        "activo",
    )
    search_fields = ("ciudadano__apellido", "ciudadano__nombre", "ciudadano__documento")
    list_filter = ("tipo", "categoria", "activo")
    autocomplete_fields = ("ciudadano",)
    readonly_fields = ("creado", "modificado")


@admin.register(HistorialTransferencia)
class HistorialTransferenciaAdmin(admin.ModelAdmin):
    list_display = (
        "ciudadano",
        "mes",
        "anio",
        "monto_auh",
        "monto_prestacion_alimentar",
        "monto_centro_familia",
        "monto_comedor",
    )
    search_fields = ("ciudadano__apellido", "ciudadano__nombre", "ciudadano__documento")
    list_filter = ("anio", "mes")
    autocomplete_fields = ("ciudadano",)
    readonly_fields = ("creado", "modificado")


@admin.register(Interaccion)
class InteraccionAdmin(admin.ModelAdmin):
    list_display = ("ciudadano", "tipo", "fecha", "responsable", "estado")
    search_fields = ("ciudadano__apellido", "ciudadano__nombre", "tipo")
    list_filter = ("estado", "fecha")
    autocomplete_fields = ("ciudadano", "responsable")
    readonly_fields = ("creado", "modificado")
