from django.contrib import admin

from core.admin_import_export import BaseImportExportAdmin
from intervenciones.models.intervenciones import (
    Intervencion,
    SubIntervencion,
    TipoIntervencion,
    TipoDestinatario,
    TipoContacto,
)
from intervenciones.resources import SubIntervencionResource, TipoIntervencionResource

# Intervencion registra actividad de negocio con soft delete y signals que crean
# hitos: no se habilita import/export desde admin.
admin.site.register(Intervencion)


@admin.register(TipoIntervencion)
class TipoIntervencionAdmin(BaseImportExportAdmin):
    resource_classes = [TipoIntervencionResource]
    list_display = ("id", "nombre", "programa")
    list_filter = ("programa",)
    search_fields = ("nombre",)


@admin.register(SubIntervencion)
class SubIntervencionAdmin(BaseImportExportAdmin):
    resource_classes = [SubIntervencionResource]
    list_display = ("id", "nombre", "tipo_intervencion")
    list_filter = ("tipo_intervencion",)
    search_fields = ("nombre",)


@admin.register(TipoDestinatario)
class TipoDestinatarioAdmin(BaseImportExportAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)


@admin.register(TipoContacto)
class TipoContactoAdmin(BaseImportExportAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)
