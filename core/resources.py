"""Resources de django-import-export para los modelos de ``core``.

Solo se definen los que necesitan acotar campos o mostrar relaciones por
nombre. Los catálogos de un único campo usan el ``ModelResource`` por defecto.
"""

from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget

from core.models import (
    Localidad,
    MontoPrestacionPrograma,
    Municipio,
    Programa,
    Provincia,
)

MUNICIPIO_CAMPOS = ("id", "nombre", "provincia")
LOCALIDAD_CAMPOS = ("id", "nombre", "municipio", "provincia")
PROGRAMA_CAMPOS = ("id", "nombre", "estado", "organismo", "descripcion")
MONTO_PRESTACION_CAMPOS = (
    "id",
    "programa",
    "desayuno_valor",
    "almuerzo_valor",
    "merienda_valor",
    "cena_valor",
    "fecha_creacion",
    "fecha_modificacion",
)


class MunicipioResource(resources.ModelResource):
    provincia = fields.Field(
        column_name="provincia",
        attribute="provincia",
        widget=ForeignKeyWidget(Provincia, "nombre"),
    )

    class Meta:
        model = Municipio
        fields = MUNICIPIO_CAMPOS
        export_order = MUNICIPIO_CAMPOS


class LocalidadResource(resources.ModelResource):
    municipio = fields.Field(
        column_name="municipio",
        attribute="municipio",
        widget=ForeignKeyWidget(Municipio, "nombre"),
    )
    provincia = fields.Field(column_name="provincia", readonly=True)

    class Meta:
        model = Localidad
        fields = LOCALIDAD_CAMPOS
        export_order = LOCALIDAD_CAMPOS

    def dehydrate_provincia(self, localidad):
        municipio = getattr(localidad, "municipio", None)
        provincia = getattr(municipio, "provincia", None)
        return str(provincia) if provincia else ""


class ProgramaResource(resources.ModelResource):
    # Se resuelve el modelo por el FK para no importar `organizaciones` desde core.
    organismo = fields.Field(
        column_name="organismo",
        attribute="organismo",
        widget=ForeignKeyWidget(
            Programa._meta.get_field("organismo").related_model, "nombre"
        ),
    )

    class Meta:
        model = Programa
        fields = PROGRAMA_CAMPOS
        export_order = PROGRAMA_CAMPOS


class MontoPrestacionProgramaResource(resources.ModelResource):
    """Excluye ``usuario_creador``: es dato de usuario y no aporta al análisis."""

    programa = fields.Field(
        column_name="programa",
        attribute="programa",
        widget=ForeignKeyWidget(Programa, "nombre"),
    )

    class Meta:
        model = MontoPrestacionPrograma
        fields = MONTO_PRESTACION_CAMPOS
        export_order = MONTO_PRESTACION_CAMPOS
