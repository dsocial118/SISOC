# 2026-03-18 - Tableros: grupos por tablero

## Contexto
- `templates/includes/sidebar/opciones.html` muestra cada tablero embebido individualmente.
- Hasta hoy el único grupo bootstrap que otorgaba los permisos `auth.role_tablero_*` era `Tableros Total`.
- Necesitamos poder asignar/revocar el acceso a cada tablero sin regalar todos los demás.

## Qué se hizo
- Se agregaron `BootstrapGroupSeed` separados para cada alias de tablero (`Tablero DataCalle Chaco`, `Tablero Aduana`, etc.) dentro de `users/bootstrap/groups_seed.py`.
- Cada grupo individual declara únicamente el permiso legacy correspondiente (`auth.role_tablero_*`) para esa vista.
- El grupo `Tableros Total` se mantiene como combinación de los permisos más generales (`dashboard.view_dashboard`, `centrodefamilia.view_centro`, `auth.role_dashboard_*` y los `auth.role_tablero_*` existentes) para quienes deben ver todos los tableros a la vez.
- `python manage.py create_groups` y `sync_group_permissions_from_registry` ahora incluyen automaticamente estos grupos, igual que los demás seeds.

## Riesgos / seguimiento
- Hay que mantener sincronizados los alias/permiso de `dashboard/fixtures/tableros.json` con estas entradas; cualquier tablero nuevo debe sumar un `BootstrapGroupSeed` equivalente.
