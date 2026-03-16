# Fix filtro booleano de comedores

## Fecha
- 2026-03-16

## Contexto
- El PR `#1307` agregó el campo `es_judicializado` en comedores y lo conectó al motor de filtros avanzados.
- La revisión detectó dos cortes de contrato: la UI no recibía operadores para el tipo `boolean` y la validación de filtros favoritos de comedores no aceptaba ese nuevo tipo.

## Cambios realizados
- Se agregó `boolean` a `get_filters_ui_config()` en `comedores/services/filter_config/impl.py`.
- Se incorporó `BOOL_OPS` en la configuración de `SeccionesFiltrosFavoritos.COMEDORES` dentro de `core/services/favorite_filters/config.py`.
- Se sumaron tests de regresión para:
  - exponer operadores booleanos en la config UI de comedores;
  - aceptar `es_judicializado` en favoritos sin marcarlo como obsoleto.

## Validación esperada
- El filtro avanzado de comedores muestra operadores válidos para `¿Es judicializado?`.
- Los favoritos de la sección comedores permiten guardar y reaplicar filtros con `es_judicializado`.
