from django.contrib import admin
from .models import Centro, Categoria, Actividad, ActividadCentro, ParticipanteActividad

@admin.register(Centro)
class CentroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'activo', 'faro_asociado')
    list_filter = ('tipo', 'activo')
    search_fields = ('nombre',)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria')
    list_filter = ('categoria',)
    search_fields = ('nombre',)

@admin.register(ActividadCentro)
class ActividadCentroAdmin(admin.ModelAdmin):
    list_display = ('centro', 'actividad', 'cantidad_personas', 'dias', 'horarios')
    list_filter = ('centro', 'actividad')

@admin.register(ParticipanteActividad)
class ParticipanteActividadAdmin(admin.ModelAdmin):
    list_display = ('actividad_centro', 'cuit', 'fecha_registro')
    search_fields = ('cuit',)
    list_filter = ('actividad_centro__centro',)
