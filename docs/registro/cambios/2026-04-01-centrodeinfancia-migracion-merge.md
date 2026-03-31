# 2026-04-01 - Merge de migraciones en `centrodeinfancia`

## Qué pasó

Se detectaron dos hojas finales en el grafo de migraciones de `centrodeinfancia`:

- `0021_expandir_nomina_cdi`
- `0022_alter_centrodeinfancia_ambito_and_more`

Eso hacía que `python manage.py makemigrations` fallara con `Conflicting migrations detected`.

## Qué se hizo

Se agregó una migración de merge vacía:

- `centrodeinfancia/migrations/0023_merge_0021_expandir_nomina_cdi_0022_alter_centrodeinfancia_ambito_and_more.py`

La migración depende de ambas ramas y no modifica el esquema.

## Razonamiento

No había choque funcional entre las ramas:

- una rama agrega campos a `NominaCentroInfancia`
- la otra agrega y ajusta campos de `CentroDeInfancia` y sus derivados

El problema era solo estructural, no de datos ni de modelo. Un merge migration mantiene el historial limpio y evita reescribir migraciones ya generadas.
