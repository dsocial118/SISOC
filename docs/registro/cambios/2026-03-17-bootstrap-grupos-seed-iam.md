# 2026-03-17 - Bootstrap declarativo de grupos y permisos IAM

## Qué cambió

- Se centralizó la semilla de grupos bootstrap y sus permisos canónicos en `users/bootstrap/groups_seed.py`.
- `create_groups` ahora consume esa semilla declarativa y hace una segunda pasada de sincronización para resolver permisos cruzados `auth.role_*` en una sola ejecución.
- Se eliminó la duplicación histórica de nombres de grupos seed en `core/constants.py`.

## Impacto operativo

- El lugar recomendado para agregar grupos base o permisos iniciales no nativos pasa a ser `users/bootstrap/groups_seed.py`.
- `python manage.py create_groups` sigue siendo el comando de bootstrap principal.
- `python manage.py sync_group_permissions_from_registry` sigue siendo válido para resincronizar grupos existentes con la semilla actual.

## Validación esperada

- Crear grupos bootstrap sin duplicados.
- Asignar permisos canónicos declarados.
- Mantener compatibilidad con permisos legacy `auth.role_*`.
