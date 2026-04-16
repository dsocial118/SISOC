# Fix subtipos de intervención CDI

## Qué cambió

- El formulario de intervenciones de `centrodeinfancia` ahora carga `subintervencion` vacía por defecto y la filtra por `tipo_intervencion` seleccionado.
- El endpoint AJAX compartido de subintervenciones ahora excluye registros con `nombre` vacío y devuelve solo los subtipos del tipo pedido.
- Se agregaron tests de regresión para cubrir el queryset inicial del form, el filtrado por tipo y la respuesta AJAX.
- Se saneó el fixture `intervenciones/fixtures/subintervencion_tipointervencion.json` removiendo 366 registros con `nombre` vacío y se agregó un test para evitar reintroducirlos.
- `load_fixtures` ahora sincroniza explícitamente todo el catálogo de intervenciones por nombre/programa después de cargar fixtures, para no depender de PKs históricas en bases con datos preexistentes.

## Motivación

- En producción, al levantar fixtures, aparecían subtipos vacíos en la creación de intervenciones de Centro de Infancia.
- El selector también exponía subtipos que no correspondían al tipo de intervención elegido.

## Validación esperada

- Crear una intervención CDI no debe mostrar subtipos hasta elegir un tipo.
- Al elegir un tipo, solo deben aparecer subtipos de ese tipo y con nombre visible.
