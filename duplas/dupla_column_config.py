"""Configuracion de columnas para el listado de duplas."""

from core.services.column_preferences import ColumnDefinition

DUPLA_LIST_KEY = "duplas_list"

DUPLA_COLUMNS = [
    ColumnDefinition(
        key="nombre",
        title="Nombre",
        header={"sortable": True, "sort_key": "nombre"},
        field={"name": "nombre", "link_field": True, "link_url": "dupla_detalle"},
        default=True,
        required=True,
        export_field="nombre",
        export_title="Nombre",
        sort_field="nombre",
    ),
    ColumnDefinition(
        key="coordinador_nombre",
        title="Coordinador",
        header={"sortable": True, "sort_key": "coordinador_nombre"},
        field={"name": "coordinador_nombre"},
        default=True,
        export_field="coordinador_nombre",
        export_title="Coordinador",
        sort_field="coordinador__last_name",
        select_related=("coordinador",),
    ),
    ColumnDefinition(
        key="tecnicos_nombres",
        title="Tecnico/s",
        header={"sortable": True, "sort_key": "tecnicos_nombres"},
        field={"name": "tecnicos_nombres"},
        default=True,
        export_field="tecnicos_nombres",
        export_title="Tecnicos",
        prefetch_related=("tecnico",),
    ),
    ColumnDefinition(
        key="abogado_nombre",
        title="Abogado",
        header={"sortable": True, "sort_key": "abogado_nombre"},
        field={"name": "abogado_nombre"},
        default=True,
        export_field="abogado_nombre",
        export_title="Abogado",
        sort_field="abogado__last_name",
        select_related=("abogado",),
    ),
    ColumnDefinition(
        key="estado",
        title="Estado",
        header={"sortable": True, "sort_key": "estado"},
        field={"name": "estado"},
        default=True,
        export_field="estado",
        export_title="Estado",
        sort_field="estado",
    ),
    ColumnDefinition(
        key="fecha",
        title="Fecha",
        header={"sortable": True, "sort_key": "fecha"},
        field={"name": "fecha"},
        default=False,
        export_field="fecha",
        export_title="Fecha",
        sort_field="fecha",
    ),
    ColumnDefinition(
        key="id",
        title="ID",
        header={"sortable": True, "sort_key": "id"},
        field={"name": "id"},
        default=False,
        export_field="id",
        export_title="ID",
        sort_field="id",
    ),
]

__all__ = ["DUPLA_LIST_KEY", "DUPLA_COLUMNS"]
