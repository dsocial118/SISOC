from django.contrib import admin

from configuraciones.models import (
    Alertas,
    CategoriaAlertas,
    Equipos,
    Organismos,
    PlanesSociales,
    Programas,
    Secretarias,
    Subsecretarias,
)


@admin.register(Secretarias)
class SecretariasAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "observaciones",
        "estado",
    )
    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(Subsecretarias)
class SubsecretariasAdmin(admin.ModelAdmin):
    list_display = (
        "fk_secretaria",
        "nombre",
        "observaciones",
        "estado",
    )
    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(Programas)
class ProgramasAdmin(admin.ModelAdmin):
    list_display = (
        "fk_subsecretaria",
        "nombre",
        "observaciones",
        "estado",
    )
    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(Organismos)
class OrganismosAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "tipo",
        "calle",
        "altura",
        "piso",
        "barrio",
        "localidad",
        "telefono",
        "email",
        "estado",
        "observaciones",
    )
    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(PlanesSociales)
class PlanesSocialesAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "jurisdiccion",
        "estado",
        "observaciones",
    )
    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(Equipos)
class EquiposAdmin(admin.ModelAdmin):
    list_display = (
        "fk_programa",
        "nombre",
        "fk_coordinador",
        "observaciones",
        "estado",
    )
    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(CategoriaAlertas)
class CategoriaAlertasAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "dimension",
        "estado",
    )
    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(Alertas)
class AlertasAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "fk_categoria",
        "estado",
        "gravedad",
    )
    search_fields = ["nombre"]
    ordering = ["nombre"]
