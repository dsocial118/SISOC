from django.contrib import admin
from django.contrib import messages

from pas.models import (
    PasAviso,
    PasCircuitoMensual,
    PasControlRenaper,
    PasDeclaracionJurada,
    PasEstado,
    PasExportacionTokens,
    PasHistorialEstado,
    PasIncompatibilidad,
    PasInforme,
    PasInvitacionDDJJ,
    PasPersona,
)
from pas.services.ddjj_service import regenerar_invitacion


@admin.register(PasEstado)
class PasEstadoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre", "descripcion")


@admin.register(PasAviso)
class PasAvisoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "descripcion", "observacion")
    list_filter = ("estados",)
    search_fields = ("codigo", "descripcion")
    filter_horizontal = ("estados",)


@admin.register(PasPersona)
class PasPersonaAdmin(admin.ModelAdmin):
    list_display = ("id_persona", "apellidos", "nombres", "dni", "provincia", "estado")
    list_filter = ("estado", "provincia")
    search_fields = ("id_persona", "apellidos", "nombres", "dni", "cuit")
    filter_horizontal = ("avisos",)
    actions = ("regenerar_token_ddjj",)

    @admin.action(description="Regenerar token vigente de DDJJ")
    def regenerar_token_ddjj(self, request, queryset):
        cantidad = 0
        for persona in queryset.iterator():
            regenerar_invitacion(persona, usuario=request.user)
            cantidad += 1
        self.message_user(
            request,
            f"Se regeneraron {cantidad} token(s) de DDJJ.",
            level=messages.SUCCESS,
        )


@admin.register(PasHistorialEstado)
class PasHistorialEstadoAdmin(admin.ModelAdmin):
    list_display = ("persona", "estado_anterior", "estado_nuevo", "fecha_cambio")
    list_filter = ("estado_nuevo", "fecha_cambio")
    search_fields = ("persona__apellidos", "persona__nombres", "persona__dni")
    filter_horizontal = ("avisos_anteriores", "avisos_nuevos")


@admin.register(PasInforme)
class PasInformeAdmin(admin.ModelAdmin):
    list_display = ("numero", "usuario", "creado", "total_personas", "total_cambios")
    list_filter = ("creado", "usuario")
    search_fields = (
        "id",
        "usuario__username",
        "usuario__first_name",
        "usuario__last_name",
    )
    filter_horizontal = ("personas", "cambios")


@admin.register(PasCircuitoMensual)
class PasCircuitoMensualAdmin(admin.ModelAdmin):
    list_display = (
        "periodo",
        "fecha_exportacion_sintys",
        "fecha_importacion_sintys",
        "fecha_cierre",
    )
    readonly_fields = (
        "fecha_exportacion_sintys",
        "exportado_por",
        "fecha_importacion_sintys",
        "importado_por",
    )


@admin.register(PasControlRenaper)
class PasControlRenaperAdmin(admin.ModelAdmin):
    list_display = ("persona", "fecha_consulta", "resultado", "consultado")
    list_filter = ("fecha_consulta", "resultado")
    search_fields = ("persona__dni", "persona__apellidos", "persona__nombres")
    readonly_fields = (
        "persona",
        "fecha_consulta",
        "resultado",
        "sexo_consulta",
        "error_tipo",
        "consultado",
    )


@admin.register(PasIncompatibilidad)
class PasIncompatibilidadAdmin(admin.ModelAdmin):
    list_display = (
        "persona",
        "categoria",
        "periodo_impacto",
        "estado",
        "fecha_deteccion",
    )
    list_filter = ("categoria", "periodo_impacto", "estado")
    search_fields = ("persona__dni", "persona__apellidos", "persona__nombres")


@admin.register(PasInvitacionDDJJ)
class PasInvitacionDDJJAdmin(admin.ModelAdmin):
    list_display = ("persona", "token", "creada", "vence", "utilizada", "revocada")
    readonly_fields = (
        "token",
        "creada",
        "utilizada",
        "revocada",
        "creada_por",
        "persona",
        "vence",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PasDeclaracionJurada)
class PasDeclaracionJuradaAdmin(admin.ModelAdmin):
    list_display = ("persona", "version", "presentada", "finalizada")
    search_fields = ("persona__dni", "persona__apellidos", "persona__nombres")
    readonly_fields = tuple(field.name for field in PasDeclaracionJurada._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PasExportacionTokens)
class PasExportacionTokensAdmin(admin.ModelAdmin):
    list_display = ("fecha", "usuario", "cantidad")
    readonly_fields = ("fecha", "usuario", "cantidad")
    ordering = ("-fecha", "-id")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
