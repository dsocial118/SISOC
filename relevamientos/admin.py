from django.contrib import admin


from relevamientos.models import (
    CantidadColaboradores,
    FrecuenciaLimpieza,
    FrecuenciaRecepcionRecursos,
    FuenteCompras,
    FuenteRecursos,
    TipoAgua,
    TipoCombustible,
    TipoDesague,
    TipoEspacio,
    TipoGestionQuejas,
    TipoModalidadPrestacion,
    TipoRecurso,
    Excepcion,
    MotivoExcepcion,
    Prestacion,
    Relevamiento,
)

admin.site.register(TipoModalidadPrestacion)
admin.site.register(TipoEspacio)
admin.site.register(TipoCombustible)
admin.site.register(TipoAgua)
admin.site.register(TipoDesague)
admin.site.register(FrecuenciaLimpieza)
admin.site.register(CantidadColaboradores)
admin.site.register(FrecuenciaRecepcionRecursos)
admin.site.register(TipoGestionQuejas)
admin.site.register(TipoRecurso)
admin.site.register(FuenteRecursos)
admin.site.register(FuenteCompras)
admin.site.register(Prestacion)
admin.site.register(Relevamiento)
admin.site.register(MotivoExcepcion)
admin.site.register(Excepcion)
