from django.contrib import admin

from core.models import (
    Localidad,
    Provincia,
    Municipio,
    Sexo,
    Mes,
    Dia,
    Turno,
    Programa,
    Nacionalidad,
    MontoPrestacionPrograma,
)

admin.site.register(Provincia)
admin.site.register(Municipio)
admin.site.register(Sexo)
admin.site.register(Mes)
admin.site.register(Dia)
admin.site.register(Turno)


@admin.register(Programa)
class ProgramaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "estado", "organismo")
    list_filter = ("estado",)
    search_fields = ("nombre",)
    readonly_fields = ("descripcion",)


@admin.register(Nacionalidad)
class NacionalidadAdmin(admin.ModelAdmin):
    list_display = ("nacionalidad",)
    search_fields = ("nacionalidad",)


@admin.register(MontoPrestacionPrograma)
class MontoPrestacionProgramaAdmin(admin.ModelAdmin):
    list_display = ("programa", "desayuno_valor", "almuerzo_valor", "merienda_valor", "cena_valor", "fecha_creacion")
    list_filter = ("programa",)
    raw_id_fields = ("usuario_creador",)
    readonly_fields = ("fecha_creacion", "fecha_modificacion")


@admin.register(Localidad)
class LocalidadAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "municipio":
            provincia_id = request.GET.get("provincia")
            if provincia_id:
                kwargs["queryset"] = Municipio.objects.filter(provincia_id=provincia_id)
            else:
                kwargs["queryset"] = Municipio.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
