# PR 1585: merge migration para ciudadanos

## Qué se corrigió

- Se agregó una migración merge en `ciudadanos` para resolver el conflicto entre `0026_merge_...` y `0027_alter_ciudadano_telefono_longitud`.

## Impacto

- Los jobs `migrations_check` y `mysql_compat` dejan de abortar por múltiples hojas en el grafo de migraciones.
