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
    list_display = (
        "iso_provincia",
        "abreviatura",
        "region_id",
        "number",
        "nombre",
        "region_id",
        "region_territorial_id",
        "uuid",
        "status",
    )
    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(LegajoMunicipio)
class LegajoMunicipioAdmin(admin.ModelAdmin):
    list_display = (
        "nombre_region",
        "codigo_ifam",
        "carta_organica",
        "categoria_id",
        "departamento_id",
        "iso_provincia",
    )
    search_fields = ["nombre_region"]
    ordering = ["nombre_region"]


@admin.register(LegajoLocalidad)
class LegajoLocalidadAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "cod_bahra",
        "bahra_gid",
        "cod_loc",
        "cod_sit",
        "cod_entidad",
        "lat_gd",
        "long_gd",
        "long_gms",
        "the_geom",
        "departamento_id",
        "fuente_ubicacion",
        "tipo_bahra",
        "cod_depto",
    )
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