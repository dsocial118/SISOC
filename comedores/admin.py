from django.contrib import admin

from comedores.models.relevamiento import Excepcion, MotivoExcepcion, Relevamiento

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
    
)

from comedores.models.comedor import (
    Comedor,
    Observacion,
    TipoDeComedor,
    ValorComida,
    Programas,
    Nomina,
    Referente,
    ImagenComedor,
    RendicionCuentasFinal,
    EstadoDocumentoRendicionFinal,
    TipoDocumentoRendicionFinal,
    DocumentoRendicionFinal,
)

#relevamiento
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

#Comedor
admin.site.register(Comedor)
admin.site.register(Observacion)
admin.site.register(TipoDeComedor)
admin.site.register(ValorComida)
admin.site.register(Programas)
admin.site.register(Nomina)
admin.site.register(Referente)
admin.site.register(ImagenComedor)
admin.site.register(RendicionCuentasFinal)
admin.site.register(EstadoDocumentoRendicionFinal)
admin.site.register(TipoDocumentoRendicionFinal)
admin.site.register(DocumentoRendicionFinal)