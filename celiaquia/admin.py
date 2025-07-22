from django.contrib import admin
from .models import (
    EstadoExpediente, EstadoLegajo, Organismo, TipoCruce,
    Expediente, ExpedienteCiudadano, AsignacionTecnico,
    ArchivoCruce, ResultadoCruce, InformePago
)

@admin.register(EstadoExpediente)
class EstadoExpedienteAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(EstadoLegajo)
class EstadoLegajoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Organismo)
class OrganismoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(TipoCruce)
class TipoCruceAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Expediente)
class ExpedienteAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'usuario_provincia', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('codigo',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion', 'fecha_cierre')

@admin.register(ExpedienteCiudadano)
class ExpedienteCiudadanoAdmin(admin.ModelAdmin):
    list_display = ('ciudadano', 'expediente', 'estado', 'creado_en')
    list_filter = ('estado',)
    search_fields = ('ciudadano__documento', 'ciudadano__nombre', 'ciudadano__apellido')

@admin.register(AsignacionTecnico)
class AsignacionTecnicoAdmin(admin.ModelAdmin):
    list_display = ('expediente', 'tecnico', 'fecha_asignacion')
    search_fields = ('expediente__codigo', 'tecnico__username')

@admin.register(ArchivoCruce)
class ArchivoCruceAdmin(admin.ModelAdmin):
    list_display = ('expediente', 'organismo', 'tipo', 'fecha_subida')
    list_filter = ('organismo', 'tipo')
    search_fields = ('expediente__codigo',)

@admin.register(ResultadoCruce)
class ResultadoCruceAdmin(admin.ModelAdmin):
    list_display = ('expediente_ciudadano', 'organismo', 'estado')
    list_filter = ('organismo', 'estado')
    search_fields = ('expediente_ciudadano__ciudadano__documento',)

@admin.register(InformePago)
class InformePagoAdmin(admin.ModelAdmin):
    list_display = ('expediente', 'tecnico', 'fecha_pago', 'monto')
    list_filter = ('fecha_pago',)
    search_fields = ('expediente__codigo', 'tecnico__username')
