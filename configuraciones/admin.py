from django.contrib import admin

from configuraciones.models import (
    Localidad,
    Provincia,
    Municipio,
    Sexo,
    Mes,
    Dia,
    Turno,
)

admin.site.register(Sexo)
admin.site.register(Mes)
admin.site.register(Dia)
admin.site.register(Turno)


@admin.register(Localidad)
class LocalidadAdmin(admin.ModelAdmin):
    list_display = ["nombre", "id", "municipio"]
    search_fields = ["nombre", "id"]


@admin.register(Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ["nombre", "id", "provincia"]
    search_fields = ["nombre", "id"]


@admin.register(Provincia)
class ProvinciaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "id"]
    search_fields = ["nombre", "id"]
