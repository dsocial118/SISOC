from django.contrib import admin
from .models import (
    Centro,
    Actividad,
    ParticipanteActividad,
    Categoria,
    ModalidadInstitucional,
    Sector,
    Subsector,
    TituloReferencia,
    ModalidadCursada,
    PlanVersionCurricular,
)


@admin.register(Centro)
class CentroAdmin(admin.ModelAdmin):
    list_display = ("nombre", "modalidad_institucional", "tipo_gestion", "activo")
    list_filter = ("activo", "modalidad_institucional", "tipo_gestion")
    search_fields = ("nombre",)
    fieldsets = (
        ("Información General", {
            "fields": ("nombre", "codigo", "organizacion_asociada", "referente")
        }),
        ("Ubicación", {
            "fields": ("provincia", "municipio", "localidad", "calle", "numero", "domicilio_actividad")
        }),
        ("Contacto", {
            "fields": ("telefono", "celular", "correo", "sitio_web", "link_redes")
        }),
        ("Responsable", {
            "fields": ("nombre_referente", "apellido_referente", "telefono_referente", "correo_referente")
        }),
        ("Información DER v4", {
            "fields": ("modalidad_institucional", "tipo_gestion", "clase_institucion", "situacion", "fecha_alta")
        }),
        ("Estado", {
            "fields": ("foto", "activo")
        }),
    )


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria")
    list_filter = ("categoria",)
    search_fields = ("nombre",)


class ActividadCentroAdmin(admin.ModelAdmin):
    list_display = (
        "centro",
        "actividad",
        "get_categoria",
        "cantidad_personas",
        "dias",
        "horariosdesde",
        "horarioshasta",
    )
    list_filter = ("centro", "actividad", "actividad__categoria")

    def get_categoria(self, obj):
        return obj.actividad.categoria

    get_categoria.short_description = "Categoría"


@admin.register(ParticipanteActividad)
class ParticipanteActividadAdmin(admin.ModelAdmin):
    list_display = ("actividad_centro", "ciudadano", "fecha_registro")
    search_fields = ("ciudadano__apellido", "ciudadano__nombre", "ciudadano__documento")
    list_filter = ("actividad_centro__centro",)


@admin.register(ModalidadInstitucional)
class ModalidadInstitucionalAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo", "fecha_creacion")
    list_filter = ("activo", "fecha_creacion")
    search_fields = ("nombre",)
    readonly_fields = ("fecha_creacion", "fecha_modificacion")


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)
    inlines = []


class SubsectorInline(admin.TabularInline):
    model = Subsector
    extra = 1


@admin.register(Subsector)
class SubsectorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "sector")
    list_filter = ("sector",)
    search_fields = ("nombre",)


@admin.register(TituloReferencia)
class TituloReferenciaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "sector", "subsector", "activo")
    list_filter = ("sector", "subsector", "activo")
    search_fields = ("nombre", "codigo_referencia")
    fieldsets = (
        ("Información General", {
            "fields": ("nombre", "codigo_referencia", "descripcion")
        }),
        ("Clasificación", {
            "fields": ("sector", "subsector")
        }),
        ("Estado", {
            "fields": ("activo",)
        }),
    )


@admin.register(ModalidadCursada)
class ModalidadCursadaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre",)


@admin.register(PlanVersionCurricular)
class PlanVersionCurricularAdmin(admin.ModelAdmin):
    list_display = ("titulo_referencia", "modalidad_cursada", "version", "activo")
    list_filter = ("titulo_referencia", "modalidad_cursada", "activo")
    search_fields = ("titulo_referencia__nombre", "version")
    fieldsets = (
        ("Información General", {
            "fields": ("titulo_referencia", "modalidad_cursada", "version")
        }),
        ("Normativa y Horas", {
            "fields": ("normativa", "horas_reloj")
        }),
        ("Niveles y Frecuencia", {
            "fields": ("nivel_requerido", "nivel_certifica", "frecuencia")
        }),
        ("Estado", {
            "fields": ("activo",)
        }),
    )
