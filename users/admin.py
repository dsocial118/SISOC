from django.contrib import admin

from users.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "source", "must_change_password", "initial_password_expires_at")
    list_filter = ("must_change_password", "source")
    search_fields = ("user__username", "user__email")
    raw_id_fields = ("user",)
    readonly_fields = ("fecha_creacion",)
