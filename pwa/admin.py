from django.contrib import admin

from pwa.models import (
    ActividadEspacioPWA,
    AuditoriaOperacionPWA,
    AuditoriaSesionPWA,
    CatalogoActividadPWA,
    ColaboradorEspacioPWA,
    InscriptoActividadEspacioPWA,
    LecturaMensajePWA,
    NominaEspacioPWA,
)


@admin.register(AuditoriaSesionPWA)
class AuditoriaSesionPWAAdmin(admin.ModelAdmin):
    list_display = (
        "fecha_evento",
        "evento",
        "resultado",
        "user",
        "username_intentado",
        "codigo_respuesta",
        "ip",
        "platform",
    )
    list_filter = ("evento", "resultado", "platform", "is_standalone")
    search_fields = ("username_intentado", "user__username", "path", "motivo_error")
    readonly_fields = (
        "fecha_evento",
        "user",
        "username_intentado",
        "evento",
        "resultado",
        "ip",
        "user_agent",
        "path",
        "metodo_http",
        "codigo_respuesta",
        "motivo_error",
        "session_id",
        "rol_pwa_snapshot",
        "comedor_ids_snapshot",
        "app_version",
        "platform",
        "is_standalone",
    )


@admin.register(AuditoriaOperacionPWA)
class AuditoriaOperacionPWAAdmin(admin.ModelAdmin):
    list_display = (
        "fecha_evento",
        "accion",
        "entidad",
        "entidad_id",
        "comedor",
        "user",
    )
    list_filter = ("accion", "entidad", "comedor")
    search_fields = ("entidad", "entidad_id", "user__username", "comedor__nombre")
    readonly_fields = (
        "fecha_evento",
        "accion",
        "entidad",
        "entidad_id",
        "comedor",
        "user",
        "snapshot_antes",
        "snapshot_despues",
        "metadata",
    )


@admin.register(LecturaMensajePWA)
class LecturaMensajePWAAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "comunicado",
        "comedor",
        "user",
        "visto",
        "fecha_visto",
        "fecha_creacion",
    )
    list_filter = ("visto", "comedor")
    search_fields = (
        "comunicado__titulo",
        "comedor__nombre",
        "user__username",
    )
    readonly_fields = ("fecha_creacion", "fecha_actualizacion")


@admin.register(ColaboradorEspacioPWA)
class ColaboradorEspacioPWAAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "comedor",
        "apellido",
        "nombre",
        "dni",
        "telefono",
        "email",
        "rol_funcion",
        "activo",
        "fecha_creacion",
    )
    list_filter = ("activo", "comedor")
    search_fields = (
        "nombre",
        "apellido",
        "dni",
        "email",
        "telefono",
        "rol_funcion",
    )
    readonly_fields = (
        "fecha_creacion",
        "fecha_actualizacion",
        "fecha_baja",
        "creado_por",
        "actualizado_por",
    )


@admin.register(CatalogoActividadPWA)
class CatalogoActividadPWAAdmin(admin.ModelAdmin):
    list_display = ("id", "categoria", "actividad", "activo")
    list_filter = ("categoria", "activo")
    search_fields = ("categoria", "actividad")
    readonly_fields = ("fecha_creacion", "fecha_actualizacion")


@admin.register(ActividadEspacioPWA)
class ActividadEspacioPWAAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "comedor",
        "catalogo_actividad",
        "dia_actividad",
        "horario_actividad",
        "activo",
        "fecha_alta",
    )
    list_filter = ("activo", "dia_actividad", "catalogo_actividad__categoria")
    search_fields = (
        "comedor__nombre",
        "catalogo_actividad__categoria",
        "catalogo_actividad__actividad",
    )
    readonly_fields = (
        "fecha_alta",
        "fecha_actualizacion",
        "fecha_baja",
        "creado_por",
        "actualizado_por",
    )


@admin.register(InscriptoActividadEspacioPWA)
class InscriptoActividadEspacioPWAAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "actividad_espacio",
        "nomina",
        "activo",
        "fecha_alta",
    )
    list_filter = ("activo", "actividad_espacio__comedor")
    search_fields = (
        "actividad_espacio__comedor__nombre",
        "nomina__ciudadano__apellido",
        "nomina__ciudadano__nombre",
        "nomina__ciudadano__documento",
    )
    readonly_fields = (
        "fecha_alta",
        "fecha_actualizacion",
        "fecha_baja",
        "creado_por",
        "actualizado_por",
    )


@admin.register(NominaEspacioPWA)
class NominaEspacioPWAAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nomina",
        "asistencia_alimentaria",
        "asistencia_actividades",
        "es_indocumentado",
        "identificador_interno",
        "activo",
        "fecha_alta",
    )
    list_filter = (
        "activo",
        "es_indocumentado",
        "asistencia_alimentaria",
        "asistencia_actividades",
    )
    search_fields = (
        "nomina__ciudadano__apellido",
        "nomina__ciudadano__nombre",
        "nomina__ciudadano__documento",
        "identificador_interno",
    )
    readonly_fields = (
        "fecha_alta",
        "fecha_actualizacion",
        "fecha_baja",
        "creado_por",
        "actualizado_por",
    )
