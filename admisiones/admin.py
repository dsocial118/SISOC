from django.contrib import admin

from core.admin_import_export import BaseExportAdmin
from admisiones.models.admisiones import (
    EstadoAdmision,
    TipoConvenio,
    Admision,
    Documentacion,
    ArchivoAdmision,
    InformeTecnico,
    InformeTecnicoPDF,
    AdmisionHistorial,
    FormularioProyectoDisposicion,
    FormularioProyectoDeConvenio,
    DocumentosExpediente,
)


# EstadoAdmision y TipoConvenio se resuelven por nombre dentro de los servicios
# de admisiones (ej. EstadoAdmision.objects.get(nombre=...)): renombrarlos en
# lote rompería el flujo de estados, por eso solo se habilita exportación.
@admin.register(EstadoAdmision)
class EstadoAdmisionAdmin(BaseExportAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)


@admin.register(TipoConvenio)
class TipoConvenioAdmin(BaseExportAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)


admin.site.register(Admision)
admin.site.register(Documentacion)
admin.site.register(ArchivoAdmision)
admin.site.register(InformeTecnico)
admin.site.register(InformeTecnicoPDF)
admin.site.register(AdmisionHistorial)
admin.site.register(FormularioProyectoDisposicion)
admin.site.register(FormularioProyectoDeConvenio)
admin.site.register(DocumentosExpediente)
