# Merge de migraciones en `comedores`

## Contexto

El arranque del contenedor `django` fallaba en `python manage.py makemigrations` por un conflicto de migraciones en la app `comedores`.

Los leaf nodes detectados eran:

- `0030_programas_usa_admision_para_nomina`
- `0033_rename_comedores_a_comedor_89ef7d_idx_comedores_a_comedor_4b1714_idx_and_more`

## Cambio realizado

Se agregó la migración vacía `comedores/migrations/0034_merge_20260329_0001.py` para unificar ambas ramas del grafo sin alterar operaciones ya definidas.

## Impacto

- No cambia modelos ni datos.
- Permite que `makemigrations` recorra el grafo sin detectar múltiples leaf nodes en `comedores`.
- Mantiene intactas las migraciones funcionales existentes de programas y colaboradores del espacio.
