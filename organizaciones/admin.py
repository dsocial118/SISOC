from django.contrib import admin
from organizaciones.models import (
    ArchivoOrganizacion,
    DocumentacionOrganizacion,
    Firmante,
    Organizacion,
    RolFirmante,
    TipoOrganizacion,
)

# Registrar todos los modelos
admin.site.register(TipoOrganizacion)
admin.site.register(RolFirmante)
admin.site.register(Firmante)
admin.site.register(Organizacion)
admin.site.register(DocumentacionOrganizacion)
admin.site.register(ArchivoOrganizacion)
