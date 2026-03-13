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
    list_display = ("id", "centro", "survey_date", "respondent_full_name", "created_at")
    list_filter = ("survey_date", "created_at")
    search_fields = ("centro__nombre", "respondent_full_name", "cdi_code")


@admin.register(FormularioCDIRoomDistribution)
class FormularioCDIRoomDistributionAdmin(admin.ModelAdmin):
    list_display = ("id", "formulario", "age_group", "room_count", "children_count")
    list_filter = ("age_group",)


@admin.register(FormularioCDIWaitlistByAgeGroup)
class FormularioCDIWaitlistByAgeGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "formulario", "age_group", "waitlist_count")
    list_filter = ("age_group",)


@admin.register(FormularioCDIArticulationFrequency)
class FormularioCDIArticulationFrequencyAdmin(admin.ModelAdmin):
    list_display = ("id", "formulario", "institution_type", "frequency")
    list_filter = ("frequency",)
