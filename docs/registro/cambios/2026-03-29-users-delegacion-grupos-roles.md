# Delegacion de grupos y roles en alta/edicion de usuarios

## Fecha
2026-03-29

## Cambio
Se agrego soporte para definir por usuario que grupos y roles (`auth.role_*`) puede asignar a terceros.

## Detalle tecnico
- Se incorporaron en `Profile` los campos:
  - `grupos_asignables` (M2M a `auth.Group`)
  - `roles_asignables` (M2M a `auth.Permission`)
- Los formularios de alta/edicion de usuarios ahora reciben el `actor` (usuario logueado) y:
  - filtran `groups` y `user_permissions` segun su alcance de delegacion,
  - filtran los nuevos campos de delegacion (`grupos_asignables`, `roles_asignables`),
  - validan que no pueda delegar ni asignar fuera de su propio alcance.
- Los campos de delegacion se muestran en la UI de usuario.
- Se agrega migracion `users/migrations/0017_profile_delegation_scope_fields.py`.

## Comportamiento esperado
- Superusuario: mantiene acceso completo para asignar/delegar grupos y roles.
- Usuario no superuser con permiso de crear/editar usuarios:
  - solo puede asignar grupos/roles dentro de su alcance configurado,
  - solo puede delegar subconjuntos de su propio alcance.

## Tests
Se agregaron pruebas en `users/tests.py` para:
- validar el bloqueo de asignacion/delegacion fuera de alcance,
- validar persistencia del alcance delegado en `Profile`.
