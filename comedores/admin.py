from django.contrib import admin

from comedores.models.relevamiento import Excepcion, MotivoExcepcion, Relevamiento
from comedores.models.comedor import (
    Comedor,
    Observacion,
    TipoDeComedor,
    ValorComida,
    Intervencion,
    SubIntervencion,
    TipoIntervencion,
    EstadosIntervencion,
    Programas,
    Nomina,
)
from comedores.models.relevamiento import (
    CantidadColaboradores,
    FrecuenciaLimpieza,
    FrecuenciaRecepcionRecursos,
    FuenteCompras,
    FuenteRecursos,
    Prestacion,
    TipoAgua,
    TipoCombustible,
    TipoDesague,
    TipoEspacio,
    TipoGestionQuejas,
    TipoModalidadPrestacion,
    TipoRecurso,
    TipoInsumos,
    TipoFrecuenciaInsumos,
    TipoTecnologia,
    TipoAccesoComedor,
    TipoDistanciaTransporte,
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
admin.site.register(Comedor)
admin.site.register(Relevamiento)
admin.site.register(Observacion)
admin.site.register(ValorComida)
admin.site.register(Intervencion)
admin.site.register(SubIntervencion)
admin.site.register(TipoIntervencion)
admin.site.register(EstadosIntervencion)
admin.site.register(Nomina)
admin.site.register(TipoDeComedor)
admin.site.register(TipoInsumos)
admin.site.register(TipoFrecuenciaInsumos)
admin.site.register(TipoTecnologia)
admin.site.register(TipoAccesoComedor)
admin.site.register(TipoDistanciaTransporte)
admin.site.register(MotivoExcepcion)
admin.site.register(Excepcion)
admin.site.register(Programas)
