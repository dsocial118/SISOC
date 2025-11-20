from django.contrib import admin

from ciudadanos.models import Ciudadano, GrupoFamiliar


@admin.register(Ciudadano)
class CiudadanoAdmin(admin.ModelAdmin):
    list_display = ("apellido", "nombre", "tipo_documento", "documento", "activo")
    search_fields = ("apellido", "nombre", "documento")
    list_filter = ("activo", "tipo_documento", "sexo")
    readonly_fields = ("creado", "modificado")


@admin.register(GrupoFamiliar)
class GrupoFamiliarAdmin(admin.ModelAdmin):
    list_display = ("ciudadano_1", "ciudadano_2", "vinculo", "conviven")
    search_fields = (
        "ciudadano_1__apellido",
        "ciudadano_1__nombre",
        "ciudadano_2__apellido",
        "ciudadano_2__nombre",
    )
    list_filter = ("vinculo", "estado_relacion", "conviven", "cuidador_principal")
    autocomplete_fields = ("ciudadano_1", "ciudadano_2")
