"""Configuracion de columnas para el listado de grupos."""

from core.services.column_preferences import ColumnDefinition

GRUPOS_LIST_KEY = "grupos_list"

GRUPOS_COLUMNS = [
    ColumnDefinition(
        key="name",
        title="Nombre",
        header={"sortable": True, "sort_key": "name"},
        field={"name": "name"},
        default=True,
        export_field="name",
        export_title="Nombre",
        sort_field="name",
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

__all__ = ["GRUPOS_LIST_KEY", "GRUPOS_COLUMNS"]
