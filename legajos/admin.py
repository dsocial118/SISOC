from django.contrib import admin
from .models import (
    LegajoProvincias,
    LegajoMunicipio,
    LegajoLocalidad,
    NivelEducativo,
    EstadoNivelEducativo,
    AsisteEscuela,
    EstadoEducativo,
    MotivoNivelIncompleto,
    AreaCurso,
    TipoGestion,
    Grado,
    Turno,
    CantidadAmbientes,
    CondicionDe,
    ContextoCasa,
    TipoAyudaHogar,
    TipoVivienda,
    TipoPosesionVivienda,
    TipoPisosVivienda,
    TipoTechoVivienda,
    Agua,
    Desague,
    Inodoro,
    Gas,
    TipoConstruccionVivienda,
    TipoEstadoVivienda,
    EstadoCivil,
    Sexo,
    Genero,
    GeneroPronombre,
    TipoDoc,
    Nacionalidad,
    TipoDiscapacidad,
    TipoEnfermedad,
    CentrosSalud,
    Frecuencia,
    ModoContratacion,
    ActividadRealizada,
    DuracionTrabajo,
    AportesJubilacion,
    TiempoBusquedaLaboral,
    NoBusquedaLaboral,
    Nivel,
    Accion,
    EstadoRelacion,
    EstadoDerivacion,
    VinculoFamiliar,
    Rechazo,
    EstadoIntervencion,
    EstadoLlamado,
    Importancia,
)


@admin.register(LegajoProvincias)
class LegajoProvinciasAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(LegajoMunicipio)
class LegajoMunicipioAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(LegajoLocalidad)
class LegajoLocalidadAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ["nombre"]
    ordering = ["nombre"]


admin.site.register(NivelEducativo)
admin.site.register(EstadoNivelEducativo)
admin.site.register(AsisteEscuela)
admin.site.register(EstadoEducativo)
admin.site.register(MotivoNivelIncompleto)
admin.site.register(AreaCurso)
admin.site.register(TipoGestion)
admin.site.register(Grado)
admin.site.register(Turno)
admin.site.register(CantidadAmbientes)
admin.site.register(CondicionDe)
admin.site.register(ContextoCasa)
admin.site.register(TipoAyudaHogar)
admin.site.register(TipoVivienda)
admin.site.register(TipoPosesionVivienda)
admin.site.register(TipoPisosVivienda)
admin.site.register(TipoTechoVivienda)
admin.site.register(Agua)
admin.site.register(Desague)
admin.site.register(Inodoro)
admin.site.register(Gas)
admin.site.register(TipoConstruccionVivienda)
admin.site.register(TipoEstadoVivienda)
admin.site.register(EstadoCivil)
admin.site.register(Sexo)
admin.site.register(Genero)
admin.site.register(GeneroPronombre)
admin.site.register(TipoDoc)
admin.site.register(Nacionalidad)
admin.site.register(TipoDiscapacidad)
admin.site.register(TipoEnfermedad)
admin.site.register(CentrosSalud)
admin.site.register(Frecuencia)
admin.site.register(ModoContratacion)
admin.site.register(ActividadRealizada)
admin.site.register(DuracionTrabajo)
admin.site.register(AportesJubilacion)
admin.site.register(TiempoBusquedaLaboral)
admin.site.register(NoBusquedaLaboral)
admin.site.register(Nivel)
admin.site.register(Accion)
admin.site.register(EstadoRelacion)
admin.site.register(EstadoDerivacion)
admin.site.register(VinculoFamiliar)
admin.site.register(Rechazo)
admin.site.register(EstadoIntervencion)
admin.site.register(EstadoLlamado)
admin.site.register(Importancia)
