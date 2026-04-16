# VAT localidades sin paginacion

Fecha: 2026-04-13

## Que cambio

- El endpoint `GET /api/vat/localidades/` deja de usar la paginacion global de DRF.
- La respuesta ahora devuelve una lista plana de localidades, ordenada por nombre.

## Decision clave

- Se desactivo la paginacion solo en `LocalidadViewSet` con `pagination_class = None` para no alterar el resto de los endpoints VAT ni la configuracion global de DRF.

## Validacion prevista

- Test de regresion en `VAT/tests.py` que verifica que el endpoint responde una lista JSON y no el envelope paginado (`count`, `results`).
