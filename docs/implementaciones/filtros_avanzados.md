# Filtros avanzados y favoritos

Este documento describe cómo reutilizar el motor de filtros avanzados, la configuración por sección y el respaldo de filtros favoritos cuando se agrega un listado nuevo.

## 1. Definir la configuración del listado

1. Crear un módulo `*/services/<mi_app>_filter_config.py` que exporte los mismos elementos que los ejemplos existentes (`comedores/services/filter_config.py`, `centrodefamilia/services/beneficiarios_filter_config.py`, etc.):
   - `FIELD_MAP`: mapeo del nombre expuesto al lookup real del ORM (FKs, campos anotados, funciones).
   - `FIELD_TYPES`: tipo lógico (`text`, `number`, `choice`, `date`, `boolean`) por campo; sirve para validar operadores.
   - Operadores por tipo (`TEXT_OPS`, `NUM_OPS`, `CHOICE_OPS`, `DATE_OPS`, `BOOL_OPS`).
   - `FILTER_FIELDS`: lista serializable con `name`, `label`, `type`, `choices`, `input`, etc., que se consume en el frontend.
   - `get_filters_ui_config()`: función que combina los campos y operadores en el DTO JSON que inyecta el formulario (`json_script`) y que luego lee `advanced_filters.js`.

2. En servicios o vistas de listado:
   - Instanciar `AdvancedFilterEngine` (`core/services/advanced_filters.py`) con `field_map`, `field_types`, `allowed_ops` y `field_casts` si necesitás castear entradas especiales (ej. latitud).
   - Antes de paginar o serializar, llamar a `engine.filter_queryset(base_qs, request_or_get)`; el motor busca el parámetro GET `filters` por defecto (puede cambiarse con `param_name`).
   - Opcionalmente aprovechar el resultado para validar columnas o exportaciones (ver doc de columnas).

## 2. Favoritos compartidos

1. Agregar una entrada en `core/services/favorite_filters.py::SeccionesFiltrosFavoritos` y proveer su configuración (`ConfiguracionFiltrosSeccion`) con los mapeos de tipos y operadores definidos en el paso anterior. Esto permite validar filtros salvados y cargar los controles.
2. El endpoint genérico `core.views.filtros_favoritos` (GET/POST) y `detalle_filtro_favorito` (GET/DELETE) ya se encargan de persistir `core.models.FiltroFavorito` y limpiar la caché (`TTL_CACHE_FILTROS_FAVORITOS`).
3. El frontend carga una sola sección por formulario:
   - Usar el componente `templates/components/search_bar.html` con `filters_mode=True` y pasar `seccion_filtros_favoritos`, `filters_config`, `filters_action`, `filters_js`, `reset_url`, `filters_action`, etc.
   - El modal de favoritos se renderiza automáticamente y el script `static/custom/js/favorite_filters.js` se encarga de cargar/guardar/aplicar/eliminar favoritos.
   - Al guardar, `favorite_filters.js` manda POST a `core:filrtros_favoritos` con `seccion`, `nombre` y la carga serializada; al aplicar, consume `core:detalle_filtro_favorito` y recarga el listado con `filters`.
   - Además mantiene el favorito activo en `localStorage` y lo reaplica automáticamente (si no hay `filters` en la URL).

## 3. Interacción con la UI

1. Incluir `<script src="{% static filters_js|default:'custom/js/advanced_filters.js' %}"></script>` y `<script src="{% static 'custom/js/favorite_filters.js' %}"></script>` junto con el formulario `id="filters-form"` (ya armado por `search_bar.html`).
2. Asegurarse de que los `name` de `FILTER_FIELDS` coincidan con los usados al construir el queryset; el JSON generado por `advanced_filters.js` tiene la forma:
   ```json
   {
     "logic": "AND",
     "items": [
       {"field": "nombre", "op": "contains", "value": "foo"},
       {"field": "estado", "op": "eq", "value": "activo"}
     ]
   }
   ```
   y se envía en el input oculto `filters`.
3. El backend siempre normaliza la carga (`core.services.favorite_filters.normalizar_carga`) antes de guardarla en la DB y la valida con `obtener_items_obsoletos` usando la configuración de la sección.

Con estos pasos podés desplegar nuevos listados que ya usan filtros avanzados, validan y guardan favoritos sin repetir lógica. Si necesitás un ejemplo concreto (motor + vista + template), avisame y lo armamos juntos.
