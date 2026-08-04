from django.contrib import admin

from core.admin_import_export import BaseImportExportAdmin
from organizaciones.models import (
    ArchivoOrganizacion,
    DocumentacionOrganizacion,
    Firmante,
    Organizacion,
    RolFirmante,
    TipoOrganizacion,
)

# Organizacion y sus documentos manejan soft delete, archivos y firmantes con
# reglas propias: quedan sin import/export por ahora.
admin.site.register(Firmante)
admin.site.register(Organizacion)
admin.site.register(DocumentacionOrganizacion)
admin.site.register(ArchivoOrganizacion)


@admin.register(TipoOrganizacion)
class TipoOrganizacionAdmin(BaseImportExportAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)


@admin.register(RolFirmante)
class RolFirmanteAdmin(BaseImportExportAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)
