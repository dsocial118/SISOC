from django.contrib import admin
from acompanamientos.models.acompanamiento import InformacionRelevante, Prestacion
from acompanamientos.models.hitos import Hitos, HitosIntervenciones

#acompañamientos
admin.site.register(InformacionRelevante)
admin.site.register(Prestacion)

#hitos
admin.site.register(Hitos)
admin.site.register(HitosIntervenciones)