# Exportar listados a CSV

Este documento resume cómo reutilizar la infraestructura de exportación CSV existente (`core.mixins.CSVExportMixin` y `static/custom/js/export_helper.js`) en nuevas vistas.

## 1. Backend

1. Crear una vista basada en `View` que herede de `CSVExportMixin`. Las vistas de ejemplo (`acompanamientos/views_export.py`, `users/views_export.py`, `comedores/views/export.py`, etc.) siguen el patrón:
   - Definir `export_filename` (ej. `"listado_comedores.csv"`).
   - Sobrescribir `get_export_columns()` para devolver una lista `[("Encabezado","campo.path"), …]`; podés usar `build_export_columns(catalog, active_keys)` para sincronizarla con el catálogo de columnas.
   - En `get()`, obtener el queryset filtrado (reutilizando los mismos filtros que el listado si hace falta) y retornar `self.export_csv(queryset)`.
2. `CSVExportMixin.check_export_permission()` lanza `PermissionDenied` si el usuario no es superuser ni pertenece al grupo `permission_group_export` (puede redefinirse). Asegurate de remover o crear un grupo nuevo si el permiso es distinto.
3. La respuesta streaming usa `StreamingHttpResponse` para evitar cargar todo el CSV en memoria; cada fila se genera con `resolve_field()` que maneja dicts, objetos y fechas.

## 2. Frontend

1. El botón contiene la clase `.btn-export-csv` y el atributo `data-url="{{ export_url }}"`. El template `templates/components/search_bar.html` ya lo incluye cuando se pasa `export_url`.
2. Asegurate de cargar `static/custom/js/export_helper.js` en el template del listado. Este script:
   - Captura los parámetros actuales de la URL (`filters`, `page`, etc.).
   - Detecta el orden actual de la tabla leyendo `th.sortable.sort-asc`/`sort-desc` (opcional, depende de `listSort.js`).
   - Combina todo en la URL del endpoint de exportación respetando el mismo origen y esquema.
   - Redirige con `window.location.href` para disparar la descarga.

## 3. Sincronizar columnas y filtros

1. Para evitar exportar columnas distintas a las visibles:
   - Reutilizá el mismo catálogo de `ColumnDefinition` que alimenta el modal de columnas y `build_export_columns`.
   - Si el listado guarda columnas activas (`ColumnResolution.active_keys`), emoji pasarlas al endpoint de export (por ejemplo `?column_keys=...`) y que la vista llame `build_export_columns(catalog, active_keys)`.
   - Asegurate de aplicar los mismos `select_related`/`only_fields` usando `apply_queryset_column_hints`.
2. Si necesitás exportar según filtros avanzados, simplemente reutilizá el mismo queryset del listado (filter engine, filtros favoritos, etc.) para que la exportación refleje exactamente los datos mostrados.

Con esto podés añadir un botón de exportación consistente en cualquier listado nuevo sin duplicar la lógica de streaming ni permisos. Si querés puedo ayudarte a crear la vista + template base para tu próximo listado.
