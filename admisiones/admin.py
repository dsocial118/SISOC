from django.contrib import admin
from admisiones.models.admisiones import (
    EstadoAdmision,
    TipoConvenio,
    Admision,
    TipoDocumentacion,
    Documentacion,
    ArchivoAdmision,
    InformeTecnicoBase,
    InformeTecnicoJuridico,
    InformeTecnicoPDF,
    AdmisionHistorial,
    FormularioRESO,
    FormularioProyectoDeConvenio,
    DocumentosExpediente,
)

admin.site.register(EstadoAdmision)
admin.site.register(TipoConvenio)
admin.site.register(Admision)
admin.site.register(TipoDocumentacion)
admin.site.register(Documentacion)
admin.site.register(ArchivoAdmision)
admin.site.register(InformeTecnicoBase)
admin.site.register(InformeTecnicoJuridico)
admin.site.register(InformeTecnicoPDF)
admin.site.register(AdmisionHistorial)
admin.site.register(FormularioRESO)
admin.site.register(FormularioProyectoDeConvenio)
admin.site.register(DocumentosExpediente)
