from django.contrib import admin

from .models import Dashboard


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ("llave", "cantidad")
    list_filter = ("llave",)
