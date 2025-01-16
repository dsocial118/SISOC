from django.contrib import admin

from configuraciones.models import (
    Localidad,
    Provincia,
    Municipio,
    Asentamiento,
    Sexo,
)

admin.site.register(Provincia)
admin.site.register(Municipio)
admin.site.register(Localidad)
admin.site.register(Asentamiento)
admin.site.register(Sexo)
