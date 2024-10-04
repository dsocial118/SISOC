from django.contrib import admin
from .models import (
    LegajoProvincias,
    LegajoMunicipio,
    LegajoLocalidad,
    NivelEducativo,
    EstadoNivelEducativo,
    AsisteEscuela,
    EstadoEducativo,
    MotivoNivelIncompleto,
    AreaCurso,
    TipoGestion,
    Grado,
    Turno,
)


@admin.register(LegajoProvincias)
class LegajoProvinciasAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(LegajoMunicipio)
class LegajoMunicipioAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(LegajoLocalidad)
class LegajoLocalidadAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ["nombre"]
    ordering = ["nombre"]


admin.site.register(NivelEducativo)
admin.site.register(EstadoNivelEducativo)
admin.site.register(AsisteEscuela)
admin.site.register(EstadoEducativo)
admin.site.register(MotivoNivelIncompleto)
admin.site.register(AreaCurso)
admin.site.register(TipoGestion)
admin.site.register(Grado)
admin.site.register(Turno)