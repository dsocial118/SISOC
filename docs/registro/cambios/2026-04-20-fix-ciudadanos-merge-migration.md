# 2026-04-20 - Ciudadanos: merge migration para destrabar CI

## Qué cambió

- Se agregó `ciudadanos/migrations/0028_merge_0026_0027.py`.
- La nueva migración unifica las dos hojas activas del grafo de `ciudadanos`:
  - `0026_merge_0023_optimize_listado_ciudadanos_indexes_0025_alter_ciudadano_fecha_nacimiento_nullable`
  - `0027_alter_ciudadano_telefono_longitud`

## Decisión clave

- Se eligió una merge migration vacía en lugar de reescribir dependencias de migraciones ya publicadas.
- Esto preserva el historial existente y resuelve el conflicto que estaba rompiendo `makemigrations --check` y la inicialización de la base de tests MySQL.

## Validación

- `docker compose exec -T django python manage.py makemigrations --check --dry-run`
- `docker compose exec -T django pytest -m mysql_compat -q`
