# Celiaquia expedientes: refresco del buscador de localidades

Fecha: 2026-04-20

## Contexto

En `/celiaquia/expedientes/nuevo/`, el modal `Buscar localidades` usa tres
filtros encadenados (`provincia`, `municipio`, `localidad`) sobre Select2.

La regla de negocio correcta se mantuvo:

- el usuario provincial solo ve su provincia asignada en el selector,
- el listado del modal debe refrescarse automaticamente a medida que cambia
  cada filtro.

El problema estaba en la sincronizacion frontend del modal: la grilla no siempre
quedaba alineada con la seleccion actual del usuario, especialmente cuando
Select2 recreaba el control o cuando habia cambios rapidos entre filtros.

## Cambio aplicado

- `static/custom/js/localidades_modal.js`
  - se encapsulo el binding de eventos del modal para escuchar el `change`
    efectivo del select manejado por Select2;
  - el filtrado de tabla ahora contempla provincia, municipio, localidad y
    texto en un mismo paso, para que la grilla quede sincronizada con el estado
    actual de los tres filtros;
  - se agrego un control simple de concurrencia (`activeRequestId`) para evitar
    que una respuesta vieja del lookup sobrescriba una seleccion mas reciente.

## Decision clave

La correccion se hizo solo en frontend. No se modifico la regla de negocio de
`ExpedienteCreateView` ni el alcance del endpoint
`expediente_localidades_lookup`, porque el problema observado era de refresco y sincronizacion visual dentro del modal.

## Pruebas automaticas

- `docker compose exec -T django pytest -q celiaquia/tests/test_localidades_lookup.py tests/test_celiaquia_expediente_view_helpers_unit.py -k "localidades_lookup or expediente_create_view_context_by_user_type"`
  - resultado local final: `4 passed, 24 deselected in 20.80s`
- Se agrego cobertura en `celiaquia/tests/test_localidades_lookup.py` para
  dejar fijado que el lookup filtrado por provincia resuelve el catalogo con un solo query sobre `core_localidad`.

## Medicion local en Docker

Medicion ejecutada sobre el catalogo local:

- provincias: `25`
- municipios: `2166`
- localidades: `8928`

Tiempos observados del lookup:

- sin filtro: `8928` filas en aproximadamente `334 ms`
- por provincia: `42` filas en aproximadamente `3.67 ms`
- por municipio: `6` filas en aproximadamente `1.91 ms`

Para la regla de negocio actual, el caso real de uso es el filtrado por
provincia asignada, por lo que no se considero necesaria una optimizacion
adicional en backend.

## Validacion manual recomendada

1. Abrir `/celiaquia/expedientes/nuevo/`.
2. Abrir el modal `Buscar localidades`.
3. Seleccionar la provincia visible del usuario y verificar que la grilla quede
   acotada a esa provincia.
4. Seleccionar un municipio y verificar que se refresquen la grilla y el combo
   de localidades.
5. Seleccionar una localidad y verificar que la tabla quede reducida a ese
   registro.
6. Limpiar filtros y verificar que el modal reconstruya el listado de la
   provincia asignada.
