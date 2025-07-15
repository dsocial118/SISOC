from django.contrib import admin

from comedores.models import (
    Comedor,
    Observacion,
    TipoDeComedor,
    ValorComida,
    Programas,
    Nomina,
    Referente,
    ImagenComedor,
)

admin.site.register(Comedor)
admin.site.register(Observacion)
admin.site.register(TipoDeComedor)
admin.site.register(ValorComida)
admin.site.register(Programas)
admin.site.register(Nomina)
admin.site.register(Referente)
admin.site.register(ImagenComedor)
