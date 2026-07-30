"""Resources de django-import-export para los catálogos de ``intervenciones``."""

from import_export import fields, resources

from intervenciones.models.intervenciones import SubIntervencion, TipoIntervencion

TIPO_INTERVENCION_CAMPOS = ("id", "nombre", "programa")
SUB_INTERVENCION_CAMPOS = (
    "id",
    "nombre",
    "tipo_intervencion",
    "tipo_intervencion_nombre",
)


class TipoIntervencionResource(resources.ModelResource):
    class Meta:
        model = TipoIntervencion
        fields = TIPO_INTERVENCION_CAMPOS
        export_order = TIPO_INTERVENCION_CAMPOS


class SubIntervencionResource(resources.ModelResource):
    """``tipo_intervencion`` se importa por id.

    ``TipoIntervencion.nombre`` no es único (se repite entre programas), así que
    resolver la relación por nombre sería ambiguo. La columna
    ``tipo_intervencion_nombre`` es solo de lectura, para que el Excel exportado
    se entienda sin cruzar tablas.
    """

    tipo_intervencion_nombre = fields.Field(
        column_name="tipo_intervencion_nombre", readonly=True
    )

    class Meta:
        model = SubIntervencion
        fields = SUB_INTERVENCION_CAMPOS
        export_order = SUB_INTERVENCION_CAMPOS

    def dehydrate_tipo_intervencion_nombre(self, subintervencion):
        tipo = getattr(subintervencion, "tipo_intervencion", None)
        return tipo.nombre if tipo else ""
