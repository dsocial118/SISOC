from django.contrib import admin
from .models import (
    EstadoExpediente,
    EstadoLegajo,
    Organismo,
    TipoCruce,
    Expediente,
    ExpedienteCiudadano,
    AsignacionTecnico,
    ExpedienteEstadoHistorial,
    HistorialComentarios,
    TipoDocumento,
    DocumentoLegajo,
)


@admin.register(EstadoExpediente)
class EstadoExpedienteAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


@admin.register(EstadoLegajo)
class EstadoLegajoAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


@admin.register(Organismo)
class OrganismoAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


@admin.register(TipoCruce)
class TipoCruceAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


@admin.register(Expediente)
class ExpedienteAdmin(admin.ModelAdmin):
    list_display = ("usuario_provincia", "estado", "fecha_creacion")
    list_filter = ("estado", "fecha_creacion")
    search_fields = ("usuario_provincia",)
    readonly_fields = ("fecha_creacion", "fecha_modificacion", "fecha_cierre")


@admin.register(ExpedienteCiudadano)
class ExpedienteCiudadanoAdmin(admin.ModelAdmin):
    list_display = ("ciudadano", "expediente", "estado", "rol", "creado_en")
    list_filter = ("estado", "rol", "revision_tecnico", "resultado_sintys")
    search_fields = ("ciudadano__documento", "ciudadano__nombre", "ciudadano__apellido")


@admin.register(AsignacionTecnico)
class AsignacionTecnicoAdmin(admin.ModelAdmin):
    list_display = ("expediente", "tecnico", "fecha_asignacion")
    list_filter = ("fecha_asignacion",)
    search_fields = ("expediente__id", "tecnico__username")


@admin.register(ExpedienteEstadoHistorial)
class ExpedienteEstadoHistorialAdmin(admin.ModelAdmin):
    list_display = (
        "expediente",
        "estado_anterior",
        "estado_nuevo",
        "usuario",
        "fecha",
    )
    list_filter = ("expediente", "estado_nuevo")


@admin.register(HistorialComentarios)
class HistorialComentariosAdmin(admin.ModelAdmin):
    list_display = (
        "legajo",
        "tipo_comentario",
        "comentario_truncado",
        "usuario",
        "fecha_creacion",
    )
    list_filter = ("tipo_comentario", "fecha_creacion", "usuario")
    search_fields = ("legajo__ciudadano__documento", "comentario")
    readonly_fields = ("fecha_creacion",)
    
    def comentario_truncado(self, obj):
        return obj.comentario[:50] + "..." if len(obj.comentario) > 50 else obj.comentario
    comentario_truncado.short_description = "Comentario"


@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "requerido", "orden", "activo")
    list_filter = ("requerido", "activo")
    search_fields = ("nombre", "descripcion")
    ordering = ("orden", "nombre")


class DocumentoLegajoInline(admin.TabularInline):
    model = DocumentoLegajo
    extra = 0
    readonly_fields = ("fecha_carga",)


@admin.register(DocumentoLegajo)
class DocumentoLegajoAdmin(admin.ModelAdmin):
    list_display = ("legajo", "tipo_documento", "fecha_carga", "usuario_carga")
    list_filter = ("tipo_documento", "fecha_carga")
    search_fields = ("legajo__ciudadano__documento", "tipo_documento__nombre")
    readonly_fields = ("fecha_carga",)
