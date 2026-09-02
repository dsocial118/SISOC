from django.contrib import admin

from .models import (
    CumplimientoRonda,
    Encuesta,
    OpcionPregunta,
    Pregunta,
    RecordatorioUsuario,
    RespuestaPregunta,
    RespuestaRonda,
    RondaEncuesta,
    SegmentacionDestinatario,
    SegmentacionEncuesta,
)


class OpcionPreguntaInline(admin.TabularInline):
    model = OpcionPregunta
    extra = 1


class PreguntaInline(admin.TabularInline):
    model = Pregunta
    extra = 1
    fk_name = "encuesta"
    fields = ("texto", "tipo", "obligatoria", "orden")


@admin.register(Encuesta)
class EncuestaAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "version",
        "estado",
        "es_anonima",
        "es_obligatoria",
        "es_recurrente",
        "usuario_creador",
        "fecha_creacion",
    )
    list_filter = ("estado", "es_anonima", "es_obligatoria", "es_recurrente")
    search_fields = ("titulo",)
    readonly_fields = ("usuario_creador", "usuario_ultima_modificacion")
    inlines = [PreguntaInline]


@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ("texto", "encuesta", "tipo", "obligatoria", "orden")
    list_filter = ("tipo", "obligatoria")
    search_fields = ("texto",)
    inlines = [OpcionPreguntaInline]


@admin.register(SegmentacionEncuesta)
class SegmentacionEncuestaAdmin(admin.ModelAdmin):
    list_display = ("encuesta", "tipo")
    list_filter = ("tipo",)


@admin.register(SegmentacionDestinatario)
class SegmentacionDestinatarioAdmin(admin.ModelAdmin):
    list_display = ("segmentacion", "tipo_documento", "numero_documento")
    list_filter = ("tipo_documento",)
    search_fields = ("numero_documento",)


@admin.register(RondaEncuesta)
class RondaEncuestaAdmin(admin.ModelAdmin):
    list_display = (
        "encuesta",
        "numero_ronda",
        "estado",
        "fecha_apertura",
        "fecha_cierre_programada",
        "fecha_cierre_real",
    )
    list_filter = ("estado", "cerrada_manualmente")


@admin.register(RespuestaRonda)
class RespuestaRondaAdmin(admin.ModelAdmin):
    list_display = ("ronda", "usuario", "completa", "fecha_respuesta")
    list_filter = ("completa",)


@admin.register(CumplimientoRonda)
class CumplimientoRondaAdmin(admin.ModelAdmin):
    list_display = ("ronda", "usuario")


@admin.register(RespuestaPregunta)
class RespuestaPreguntaAdmin(admin.ModelAdmin):
    list_display = ("respuesta_ronda", "pregunta")


@admin.register(RecordatorioUsuario)
class RecordatorioUsuarioAdmin(admin.ModelAdmin):
    list_display = ("ronda", "usuario", "fecha_proximo_aviso")
