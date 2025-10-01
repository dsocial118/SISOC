from django.contrib import admin
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

admin.site.register(EstadoAdmision)
admin.site.register(TipoConvenio)
admin.site.register(Admision)
admin.site.register(Documentacion)
admin.site.register(ArchivoAdmision)
admin.site.register(InformeTecnico)
admin.site.register(InformeTecnicoPDF)
admin.site.register(AdmisionHistorial)
admin.site.register(FormularioProyectoDisposicion)
admin.site.register(FormularioProyectoDeConvenio)
admin.site.register(DocumentosExpediente)
