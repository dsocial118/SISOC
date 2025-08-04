from django.contrib import admin
from organizaciones.models import TipoOrganizacion, RolFirmante, Firmante, Organizacion

# Registrar todos los modelos
admin.site.register(TipoOrganizacion)
admin.site.register(RolFirmante)
admin.site.register(Firmante)
admin.site.register(Organizacion)
