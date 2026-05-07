from django.contrib import admin

from dispositivos.models import Dispositivo


@admin.register(Dispositivo)
class DispositivoAdmin(admin.ModelAdmin):
	list_display = (
		"nombre_institucion",
		"tipo_dispositivo",
		"provincia",
		"municipio",
		"created_at",
	)
	search_fields = (
		"nombre_institucion",
		"razon_social",
		"cuit_institucion",
	)
	list_filter = ("tipo_dispositivo", "modalidad_funcionamiento", "provincia")
