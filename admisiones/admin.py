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
    IncidenciaTemplateInformeTecnico,
    IncidenciaTemplateInformeTecnicoCaso,
    PlantillaInformeTecnico,
    PlantillaInformeTecnicoVersion,
    PlantillaInformeTecnicoPublicacion,
    VariableTemplateInformeTecnico,
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


@admin.register(PlantillaInformeTecnico)
class PlantillaInformeTecnicoAdmin(BaseExportAdmin):
    list_display = ("codigo", "nombre", "tipo_admision", "tipo_convenio", "estado")
    list_filter = ("tipo_admision", "estado", "tipo_convenio")
    search_fields = ("codigo", "nombre")
    readonly_fields = ("codigo", "creado", "modificado")

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj is None:
            return readonly_fields
        return (
            *readonly_fields,
            "tipo_admision",
            "tipo_convenio",
            "es_ex_pnud",
            "estado_convenio_pnud",
            "tipo_renovacion",
            "estado_financiamiento",
        )


@admin.register(PlantillaInformeTecnicoVersion)
class PlantillaInformeTecnicoVersionAdmin(BaseExportAdmin):
    list_display = ("plantilla", "numero", "estado", "creado", "publicado")
    list_filter = ("estado",)
    search_fields = ("plantilla__codigo", "plantilla__nombre")
    readonly_fields = ("creado", "modificado", "publicado")

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj is None or obj.estado == "borrador":
            return readonly_fields
        return (
            *readonly_fields,
            "plantilla",
            "numero",
            "contenido_html",
            "observaciones",
            "estado",
            "creado_por",
            "publicado_por",
        )


@admin.register(PlantillaInformeTecnicoPublicacion)
class PlantillaInformeTecnicoPublicacionAdmin(BaseExportAdmin):
    list_display = ("plantilla", "version", "publicada", "publicada_por")
    search_fields = ("plantilla__codigo", "plantilla__nombre", "clave_condiciones")
    readonly_fields = ("clave_condiciones", "publicada", "publicada_por")


@admin.register(VariableTemplateInformeTecnico)
class VariableTemplateInformeTecnicoAdmin(BaseExportAdmin):
    list_display = ("nombre", "categoria", "codigo", "activo", "orden")
    list_filter = ("activo", "categoria")
    search_fields = ("nombre", "codigo", "descripcion")
    ordering = ("categoria", "orden", "nombre")


@admin.register(IncidenciaTemplateInformeTecnico)
class IncidenciaTemplateInformeTecnicoAdmin(BaseExportAdmin):
    list_display = (
        "codigo",
        "estado",
        "cantidad_casos",
        "plantilla",
        "ultima_fecha",
    )
    list_filter = ("estado",)
    search_fields = ("codigo", "clave_condiciones")
    readonly_fields = (
        "codigo",
        "clave_condiciones",
        "clave_abierta",
        "condiciones",
        "cantidad_casos",
        "primera_fecha",
        "ultima_fecha",
    )


@admin.register(IncidenciaTemplateInformeTecnicoCaso)
class IncidenciaTemplateInformeTecnicoCasoAdmin(BaseExportAdmin):
    list_display = (
        "incidencia",
        "admision_id_reportada",
        "informe_id_reportado",
        "comedor_nombre",
        "creado",
    )
    search_fields = (
        "incidencia__codigo",
        "comedor_nombre",
        "organizacion_nombre",
    )
    readonly_fields = (
        "incidencia",
        "referencia_caso",
        "admision",
        "admision_id_reportada",
        "informe",
        "informe_id_reportado",
        "comedor_nombre",
        "organizacion_nombre",
        "programa_nombre",
        "estado_admision",
        "detalle",
        "reportado_por",
        "creado",
        "modificado",
    )
