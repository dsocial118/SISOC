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
    list_display = ("ciudadano", "expediente", "estado", "creado_en")
    list_filter = ("estado",)
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
