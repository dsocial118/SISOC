# Preferencias de columnas

Este archivo describe cómo reutilizar el sistema de preferencias de columnas (column config) en nuevas vistas/listados.

## 1. Catálogo y definición

1. Crear una lista de `core.services.column_preferences.ColumnDefinition` para describir cada columna del listado. Cada definición debe incluir:
   - `key`, `title`, `field` (diccionario con `name` y atributos de renderizado o `label`).
   - Flags como `default` (si aparece por omisión), `required` (no puede ocultarse), `export_field`/`export_title`, `sort_field` y relaciones (`select_related`, `prefetch_related`, `only_fields`) para ajustar el queryset.
2. Si no tenés objetos `ColumnDefinition` (por ejemplo usás celdas personalizadas), podés usar los helpers:
   - `build_columns_context_from_fields(request, list_key, headers, fields, …)` para tablas renderizadas con headers y fields paralelos.
   - `build_columns_context_for_custom_cells(request, list_key, headers, items, …)` para listas donde cada `item` tiene un array `cells`.

## 2. Contexto en la vista

1. En la vista que renderiza la tabla:
   - Llamá a `build_columns_context(request, list_key, catalog)` (o la variante adecuada) y `update` el contexto con el resultado.
   - El helper retorna `table_headers`, `table_fields`, `column_config`, `column_active_keys`, `column_default_keys`.
   - Guardá el mismo `list_key` en todas las llamadas (ej. `"listado_comedores"`) para que el endpoint de preferencias de `core.views` use la misma clave.
2. Antes de ejecutar el queryset, podés aplicar `apply_queryset_column_hints(queryset, catalog, active_keys)` para añadir `select_related`, `prefetch_related` y `only` dinámicamente según las columnas visibles.
3. Si necesitás ir a mano, podés usar `resolve_column_state(request, list_key, catalog)` para obtener las claves activas y defaults sin reconstruir el contexto completo.

## 3. Template y modal

1. Reutilizar `templates/components/data_table.html` (o `comedor_table.html`). Ya incluyen:
   - El modal con `data-column-config`, la lista ordenable de columnas y los botones “Configurar columnas”.
   - La inclusión de `{% json_script column_config.script_id %}` y el script `static/custom/js/column_config.js`.
2. Si creás un markup propio:
   - Asegurate de que el wrapper tenga `data-column-config`.
   - Introducir un `<script type="application/json" id="{{ column_config.script_id }}">{{ column_config|json_script }}</script>` o usar `json_script`.
   - Cada `li` debe contener `data-column-key` y un checkbox `.column-config-checkbox`.
3. El JS (`column_config.js`):
   - Lee `column_config`, muestra las columnas activas, permite mover filas y togglear visibilidad.
   - Al guardar, manda POST a `core:column_preferences` con `list_key` y `columns` (ordenada).
   - También permite resetear la configuración (envía `reset: true`).

## 4. Endpoints

1. El endpoint `core.views.columnas_preferencias` ya acepta GET/POST:
   - GET recibe `list_key` y devuelve las columnas guardadas.
   - POST guarda una lista ordenada o resetea (`reset` true).
2. El modelo `core.models.PreferenciaColumnas` guarda `usuario`, `listado`, el arreglo de `columnas` y timestamps. No requiere cambios, solo usar la misma `list_key`.

Con esto tenés un patrón replicable para habilitar configuración de columnas en cualquier listado nuevo. Si necesitás que te ayude a convertir un template existente, lo armamos sobre este esquema.
