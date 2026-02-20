from django.contrib import admin

from centrodeinfancia.models import (
    CentroDeInfancia,
    IntervencionCentroInfancia,
    NominaCentroInfancia,
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
