# Fix conflicto de migraciones en users

## Contexto

`development` quedo con dos hojas en el grafo de migraciones de `users`:

- `0023_merge_20260331_1500`
- `0024_rename_vat_secondary_groups_to_cfp`

Esto bloqueaba `python manage.py migrate auth` durante el arranque porque Django
detectaba multiples leaf nodes.

## Que se corrigio

- Se agrego `users/migrations/0025_merge_20260404_0000.py`.
- La nueva migracion unifica las dos ramas sin introducir operaciones nuevas de
  esquema ni de datos.

## Criterio aplicado

- `0023_merge_20260331_1500` ya resolvia la bifurcacion previa entre
  `0021_profile_password_reset_requested_at` y
  `0022_profile_temporary_password_plaintext`.
- `0024_rename_vat_secondary_groups_to_cfp` continua una rama independiente de
  renombres de grupos sobre `0023_rename_vat_sse_group_to_cfpinet`.
- Como ambas lineas son compatibles y deben convivir en el historial, el ajuste
  correcto es una migracion `merge` final.

## Validacion

- Revision manual del grafo y de dependencias de `users/migrations`.
- Confirmacion de que la hoja esperada pasa a ser `0025_merge_20260404_0000`.
