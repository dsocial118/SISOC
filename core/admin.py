from django.contrib import admin

from core.models import (
    Localidad,
    Provincia,
    Municipio,
    Sexo,
    Mes,
    Dia,
    Turno,
)

admin.site.register(Provincia)
admin.site.register(Municipio)
admin.site.register(Localidad)
admin.site.register(Sexo)
admin.site.register(Mes)
admin.site.register(Dia)
admin.site.register(Turno)
