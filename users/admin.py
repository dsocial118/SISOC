from django.contrib import admin

from users.models import AuditAccesoComedorPWA, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "source",
        "must_change_password",
        "initial_password_expires_at",
    )
    list_filter = ("must_change_password", "source")
    search_fields = ("user__username", "user__email")
    raw_id_fields = ("user",)
    readonly_fields = ("fecha_creacion",)


@admin.register(AuditAccesoComedorPWA)
class AuditAccesoComedorPWAAdmin(admin.ModelAdmin):
    list_display = (
        "fecha_evento",
        "accion",
        "user",
        "comedor",
        "actor",
    )
    list_filter = ("accion", "fecha_evento")
    search_fields = (
        "user__username",
        "user__email",
        "actor__username",
        "comedor__nombre",
    )
    raw_id_fields = ("acceso", "user", "comedor", "organizacion", "actor")
    readonly_fields = (
        "acceso",
        "user",
        "comedor",
        "organizacion",
        "accion",
        "fecha_evento",
        "actor",
        "metadata",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
