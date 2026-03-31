# Formulario CDI: edición renderiza ids de formsets

## Qué cambió

- Se renderizan los campos ocultos `id` de las filas existentes en los tres formsets del formulario CDI.
- Se agregó una regresión que crea un formulario vacío, entra a editarlo y confirma que guardar sin cambios vuelve a funcionar.

## Problema que resuelve

En edición, el template no enviaba los `id` de las filas ya persistidas. Django interpretaba eso como formularios inválidos en los formsets y devolvía el mensaje general de error sin resaltar campos visibles.

## Impacto esperado

- Un formulario CDI vacío puede volver a guardarse en edición sin cambios.
- Si hay un error real de datos, el formulario ya no falla por falta de `id` ocultos en las tablas.
