# 2026-08-06 - Endpoint Select2 de organizaciones fuera de core

## Contexto

`core.views` resolvia el endpoint global de busqueda de organizaciones e
importaba directamente el modelo de ese dominio.

## Decision

La vista y su ruta se trasladan a `organizaciones`. Se preservan el path
`ajax/load-organizaciones/`, el nombre `ajax_load_organizaciones`, el acceso
autenticado y el contrato JSON que usa Select2.

## Consecuencias

- `core` deja de importar `organizaciones.models`.
- El comportamiento de busqueda y paginacion no cambia.
- Se retira una excepcion runtime de `.importlinter`.

## Validacion

- `black --check core/views.py core/urls.py organizaciones/views.py organizaciones/urls.py tests/test_core_views_unit.py organizaciones/test_load_organizaciones_ajax.py`.
- `pytest tests/test_core_views_unit.py organizaciones/test_load_organizaciones_ajax.py -q`.
- `python manage.py check`.
- `lint-imports`.
