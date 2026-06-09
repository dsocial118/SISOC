from django.contrib import admin

from ciudadanos.models import (
    Ciudadano,
    CiudadanosImportJob,
    CiudadanosImportJobRow,
    GrupoFamiliar,
    HistorialTransferencia,
    Interaccion,
    ProgramaTransferencia,
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


@admin.register(CiudadanosImportJob)
class CiudadanosImportJobAdmin(admin.ModelAdmin):
    list_display = ("id", "requested_by", "original_filename", "status", "total_rows", "processed_rows", "requested_at")
    list_filter = ("status",)
    search_fields = ("original_filename", "requested_by__username")
    readonly_fields = (
        "requested_by", "original_filename", "archivo", "status",
        "total_rows", "processed_rows", "created_rows", "existing_rows", "failed_rows",
        "pending_rows", "next_row_index", "last_successful_row", "last_successful_documento",
        "last_attempted_row", "last_attempted_documento", "last_error_message", "last_error_type",
        "last_error_at", "resume_count", "requested_at", "started_at", "finished_at", "last_activity_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(CiudadanosImportJobRow)
class CiudadanosImportJobRowAdmin(admin.ModelAdmin):
    list_display = ("job", "fila", "documento_raw", "status", "processed_at")
    list_filter = ("status",)
    search_fields = ("documento_raw", "dni", "cuil")
    raw_id_fields = ("job", "ciudadano")
    readonly_fields = (
        "job", "fila", "documento_raw", "dni", "cuil", "sexo", "sexos_intentados",
        "status", "ciudadano", "mensaje", "error_type", "attempts", "processed_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
