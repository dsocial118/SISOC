from django.contrib import admin

from ..configuraciones.models import Localidad, Municipio, Provincia

from .models import (
    Accion,
    ActividadRealizada,
    Agua,
    AportesJubilacion,
    AreaCurso,
    AsisteEscuela,
    CantidadAmbientes,
    CentrosSalud,
    CondicionDe,
    ContextoCasa,
    Desague,
    DuracionTrabajo,
    EstadoCivil,
    EstadoDerivacion,
    EstadoEducativo,
    EstadoIntervencion,
    EstadoLlamado,
    EstadoNivelEducativo,
    EstadoRelacion,
    Frecuencia,
    Gas,
    Genero,
    GeneroPronombre,
    Grado,
    Importancia,
    Inodoro,
    ModoContratacion,
    MotivoNivelIncompleto,
    Nacionalidad,
    Nivel,
    NivelEducativo,
    NoBusquedaLaboral,
    Rechazo,
    Sexo,
    TiempoBusquedaLaboral,
    TipoAyudaHogar,
    TipoConstruccionVivienda,
    TipoDiscapacidad,
    TipoDoc,
    TipoEnfermedad,
    TipoEstadoVivienda,
    TipoGestion,
    TipoPisosVivienda,
    TipoPosesionVivienda,
    TipoTechoVivienda,
    TipoVivienda,
    Turno,
    VinculoFamiliar,
)


@admin.register(Provincia)
class LegajoProvinciasAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(Municipio)
class LegajoMunicipioAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(Localidad)
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
