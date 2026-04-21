# PR 1565: fix de CI y render de responsable

## Qué se corrigió

- Se agregó una migración merge en `ciudadanos` para resolver el conflicto entre `0026_merge_...` y `0027_alter_ciudadano_telefono_longitud`.
- Se ajustó el render de las etiquetas del bloque de responsable en `expediente_detail` para que el asterisco obligatorio quede en la misma línea del texto visible, manteniendo la lógica actual que solo exige esos campos cuando corresponde.

## Impacto

- `migrations_check` y `mysql_compat` dejan de fallar por hojas múltiples en la app `ciudadanos`.
- El test de regresión que busca `Apellido Responsable *` en el detalle de expediente vuelve a reflejar el HTML real renderizado.
