from django.contrib import admin

from centrodeinfancia.models import (
    CentroDeInfancia,
    FormularioCDI,
    FormularioCDIArticulationFrequency,
    FormularioCDIRoomDistribution,
    FormularioCDIWaitlistByAgeGroup,
    IntervencionCentroInfancia,
    NominaCentroInfancia,
    ObservacionCentroInfancia,
    Trabajador,
)


@admin.register(CentroDeInfancia)
class CentroDeInfanciaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "organizacion", "fecha_creacion")
    search_fields = ("nombre", "organizacion__nombre")


@admin.register(NominaCentroInfancia)
class NominaCentroInfanciaAdmin(admin.ModelAdmin):
    list_display = ("id", "centro", "ciudadano", "estado", "fecha")
    list_filter = ("estado",)
    search_fields = ("centro__nombre", "ciudadano__apellido", "ciudadano__nombre")


@admin.register(Trabajador)
class TrabajadorAdmin(admin.ModelAdmin):
    list_display = ("id", "centro", "apellido", "nombre", "rol", "telefono")
    list_filter = ("rol",)
    search_fields = ("centro__nombre", "apellido", "nombre", "telefono")


@admin.register(IntervencionCentroInfancia)
class IntervencionCentroInfanciaAdmin(admin.ModelAdmin):
    list_display = ("id", "centro", "tipo_intervencion", "fecha")
    list_filter = ("tipo_intervencion", "destinatario")
    search_fields = ("centro__nombre", "observaciones")


@admin.register(ObservacionCentroInfancia)
class ObservacionCentroInfanciaAdmin(admin.ModelAdmin):
    list_display = ("id", "centro", "observador", "fecha_visita")
    list_filter = ("fecha_visita",)
    search_fields = ("centro__nombre", "observador", "observacion")


@admin.register(FormularioCDI)
class FormularioCDIAdmin(admin.ModelAdmin):
    list_display = ("id", "centro", "fecha_relevamiento", "nombre_completo_respondente", "created_at")
    list_filter = ("fecha_relevamiento", "created_at")
    search_fields = ("centro__nombre", "nombre_completo_respondente", "codigo_cdi")


@admin.register(FormularioCDIRoomDistribution)
class FormularioCDIRoomDistributionAdmin(admin.ModelAdmin):
    list_display = ("id", "formulario", "grupo_etario", "cantidad_salas", "cantidad_ninos")
    list_filter = ("grupo_etario",)


@admin.register(FormularioCDIWaitlistByAgeGroup)
class FormularioCDIWaitlistByAgeGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "formulario", "grupo_etario", "cantidad_demanda_insatisfecha")
    list_filter = ("grupo_etario",)


@admin.register(FormularioCDIArticulationFrequency)
class FormularioCDIArticulationFrequencyAdmin(admin.ModelAdmin):
    list_display = ("id", "formulario", "tipo_institucion", "frecuencia")
    list_filter = ("frecuencia",)

