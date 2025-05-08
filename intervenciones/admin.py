
from django.contrib import admin

from intervenciones.models.intervenciones import (
    Intervencion,
    SubIntervencion,
    EstadosIntervencion,
    TipoIntervencion,
    TipoDestinatario,
    TipoContacto,
)

admin.site.register(Intervencion)
admin.site.register(SubIntervencion)
admin.site.register(TipoIntervencion)
admin.site.register(EstadosIntervencion)
admin.site.register(TipoDestinatario)
admin.site.register(TipoContacto)
