# PR 1546: resolucion de conflictos contra development

## Que se resolvio

- Se integro `origin/development` sobre la rama del PR `#1546`.
- El conflicto quedo concentrado en `VAT/views/centro.py`.
- Se preservo la paginacion sin `count()` incorporada en `development`.
- Se preservo la anotacion `codigo_cue` agregada por el PR para que el filtro avanzado `Codigo` siga operando sobre el CUE vigente con fallback a `Centro.codigo`.

## Decision de integracion

- El queryset base del listado de centros ahora centraliza ambas necesidades:
  - optimizacion del listado sin `count()`,
  - soporte para filtrar por `codigo_cue`.
- No se tocaron servicios, templates ni tests fuera de lo necesario para destrabar el merge.

## Validacion esperada

- Abrir `/vat/centros/`.
- Confirmar que el listado siga paginando normalmente.
- Aplicar el filtro avanzado `Codigo` con el CUE vigente de un centro.
- Verificar que el resultado coincida con el comportamiento esperado del PR original.
