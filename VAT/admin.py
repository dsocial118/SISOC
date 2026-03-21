from django.contrib import admin
from .models import Centro, Actividad, ParticipanteActividad, Categoria, ModalidadInstitucional


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
