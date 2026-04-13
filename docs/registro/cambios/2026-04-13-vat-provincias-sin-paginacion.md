# VAT provincias sin paginacion

Fecha: 2026-04-13

## Que cambio

- El endpoint `GET /api/vat/provincias/` deja de usar la paginacion global de DRF.
- La respuesta ahora devuelve una lista plana de provincias, ordenada por nombre.

## Decision clave

- Se desactivo la paginacion solo en `ProvinciaViewSet` con `pagination_class = None` para no alterar el resto de los endpoints VAT ni la configuracion global de DRF.

## Validacion prevista

- Test de regresion en `VAT/tests.py` que verifica que el endpoint responde una lista JSON y no el envelope paginado (`count`, `results`).
