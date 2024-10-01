from django.contrib import admin

from .models import LegajoLocalidad, LegajoMunicipio, LegajoProvincias


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
