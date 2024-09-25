from django.contrib import admin

from comedores.models import (
    Comedor,
    Observacion,
    Relevamiento,
    TipoModalidadPrestacion,
    TipoEspacio,
    TipoCombustible,
    TipoAgua,
    TipoDesague,
    FrecuenciaLimpieza,
    CantidadColaboradores,
    FrecuenciaRecepcionRecursos,
    TipoRecurso,
    FuenteRecursos,
    FuenteCompras,
    Prestacion,
)


@admin.register(TipoModalidadPrestacion)
class TipoModalidadPrestacionAdmin(admin.ModelAdmin):
    list_display = ("nombre",)

    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(TipoEspacio)
class TipoEspacioAdmin(admin.ModelAdmin):
    list_display = ("nombre",)

    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(TipoCombustible)
class TipoCombustibleAdmin(admin.ModelAdmin):
    list_display = ("nombre",)

    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(TipoAgua)
class TipoAguaAdmin(admin.ModelAdmin):
    list_display = ("nombre",)

    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(TipoDesague)
class TipoDesagueAdmin(admin.ModelAdmin):
    list_display = ("nombre",)

    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(FrecuenciaLimpieza)
class FrecuenciaLimpiezaAdmin(admin.ModelAdmin):
    list_display = ("nombre",)

    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(CantidadColaboradores)
class CantidadColaboradoresAdmin(admin.ModelAdmin):
    list_display = ("nombre",)

    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(FrecuenciaRecepcionRecursos)
class FrecuenciaRecepcionRecursosAdmin(admin.ModelAdmin):
    list_display = ("nombre",)

    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(TipoRecurso)
class TipoRecursoAdmin(admin.ModelAdmin):
    list_display = ("nombre",)

    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(FuenteRecursos)
class FuenteRecursosAdmin(admin.ModelAdmin):
    list_display = (
        "recibe_donaciones_particulares",
        "recibe_estado_nacional",
        "recibe_estado_provincial",
        "recibe_estado_municipal",
        "recibe_otros",
    )


@admin.register(FuenteCompras)
class FuenteComprasAdmin(admin.ModelAdmin):
    list_display = (
        "almacen_cercano",
        "verduleria",
        "granja",
        "carniceria",
        "pescaderia",
        "supermercado",
        "mercado_central",
        "ferias_comunales",
        "mayoristas",
        "otro",
    )


@admin.register(Prestacion)
class PrestacionAdmin(admin.ModelAdmin):
    list_display = ["relevamiento"]
    search_fields = ["relevamiento"]
    ordering = ["relevamiento"]


@admin.register(Comedor)
class ComedorAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "calle",
        "numero",
        "provincia",
        "municipio",
        "localidad",
    )

    search_fields = ["nombre", "provincia", "municipio", "localidad"]
    ordering = ["nombre"]


@admin.register(Relevamiento)
class RelevamientoAdmin(admin.ModelAdmin):
    list_display = (
        "comedor",
        "fecha_visita",
    )
    search_fields = [
        "comedor",
        "fecha_visita",
    ]
    ordering = ["comedor"]


@admin.register(Observacion)
class ObservacionAdmin(admin.ModelAdmin):
    list_display = (
        "comedor",
        "fecha",
    )
    search_fields = [
        "comedor",
        "fecha",
    ]
    ordering = ["comedor"]
