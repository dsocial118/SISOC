from django.contrib import admin

from core.admin_import_export import BaseExportAdmin, BaseImportExportAdmin
from core.models import (
    Localidad,
    Provincia,
    Municipio,
    Sexo,
    Mes,
    Dia,
    Turno,
    Programa,
    Nacionalidad,
    MontoPrestacionPrograma,
)
from core.resources import (
    LocalidadResource,
    MontoPrestacionProgramaResource,
    MunicipioResource,
    ProgramaResource,
)


# Territorio: la fuente autoritativa es la bajada BAHRA
# (core/services/territorio_sync.py), por eso solo se expone exportación.
@admin.register(Provincia)
class ProvinciaAdmin(BaseExportAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)


@admin.register(Municipio)
class MunicipioAdmin(BaseExportAdmin):
    resource_classes = [MunicipioResource]
    list_display = ("id", "nombre", "provincia")
    list_filter = ("provincia",)
    search_fields = ("nombre",)


@admin.register(Localidad)
class LocalidadAdmin(BaseExportAdmin):
    resource_classes = [LocalidadResource]
    list_display = ("id", "nombre", "municipio")
    search_fields = ("nombre",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "municipio":
            provincia_id = request.GET.get("provincia")
            if provincia_id:
                kwargs["queryset"] = Municipio.objects.filter(provincia_id=provincia_id)
            else:
                kwargs["queryset"] = Municipio.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# Catálogos de sistema: sus valores están acoplados por nombre o por id en el
# código (ej. sexo__sexo="Masculino", Dia ordenado por id), así que no se
# habilita importación.
@admin.register(Sexo)
class SexoAdmin(BaseExportAdmin):
    list_display = ("id", "sexo")


@admin.register(Mes)
class MesAdmin(BaseExportAdmin):
    list_display = ("id", "nombre")


@admin.register(Dia)
class DiaAdmin(BaseExportAdmin):
    list_display = ("id", "nombre")


@admin.register(Turno)
class TurnoAdmin(BaseExportAdmin):
    list_display = ("id", "nombre")


# Los ids de Programa están referenciados desde settings (PROG_MILD, PROG_CDIF,
# etc.): alta y edición siguen siendo manuales.
@admin.register(Programa)
class ProgramaAdmin(BaseExportAdmin):
    resource_classes = [ProgramaResource]
    list_display = ("nombre", "estado", "organismo")
    list_filter = ("estado",)
    search_fields = ("nombre",)


@admin.register(Nacionalidad)
class NacionalidadAdmin(BaseImportExportAdmin):
    list_display = ("id", "nacionalidad")
    search_fields = ("nacionalidad",)


# Montos de prestación: impacto económico directo, solo exportación.
@admin.register(MontoPrestacionPrograma)
class MontoPrestacionProgramaAdmin(BaseExportAdmin):
    resource_classes = [MontoPrestacionProgramaResource]
    list_display = (
        "programa",
        "desayuno_valor",
        "almuerzo_valor",
        "merienda_valor",
        "cena_valor",
        "fecha_creacion",
    )
    list_filter = ("programa",)
    raw_id_fields = ("usuario_creador",)
    readonly_fields = ("fecha_creacion", "fecha_modificacion")
