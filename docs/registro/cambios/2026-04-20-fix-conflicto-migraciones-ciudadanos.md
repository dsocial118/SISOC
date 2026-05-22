# Fix conflicto de migraciones en `ciudadanos`

## Contexto

Los jobs `migrations_check` y `mysql_compat` del PR quedaban bloqueados antes de
ejecutar sus validaciones reales porque Django detectaba multiples leaf nodes en
la app `ciudadanos`:

- `0026_merge_0023_optimize_listado_ciudadanos_indexes_0025_alter_ciudadano_fecha_nacimiento_nullable`
- `0027_alter_ciudadano_telefono_longitud`

## Que se corrigio

- Se agrego `ciudadanos/migrations/0028_merge_20260420_0000.py`.
- La nueva migracion unifica ambas ramas sin introducir operaciones de schema ni
  de datos.

## Impacto

- No cambia el modelo `Ciudadano`.
- Destraba `python manage.py makemigrations --check --dry-run`.
- Permite que `mysql_compat` arranque con un grafo de migraciones consistente.
