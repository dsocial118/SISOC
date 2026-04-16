# Merge migrations para users y comedores

## Contexto

El entrypoint de Django ejecuta `python manage.py makemigrations` al iniciar el
contenedor. Luego de corregir los errores de sintaxis en `users`, el arranque quedo
bloqueado por conflictos de migraciones con multiples hojas en `users` y
`comedores`, y despues por operaciones duplicadas al aplicar `migrate`.

## Que se corrigio

- Se restauro `users/migrations/0022_profile_temporary_password_plaintext.py`
  como migracion canonica para agregar `Profile.temporary_password_plaintext`.
- Se elimino la migracion autogenerada
  `users/migrations/0024_profile_temporary_password_plaintext.py`, que volvia a
  intentar agregar el mismo campo por desalineacion del estado migratorio.
- Se agrego `users/migrations/0023_merge_20260331_1500.py` para unificar:
  - `0021_profile_password_reset_requested_at`
  - `0022_profile_temporary_password_plaintext`
- Se agrego `comedores/migrations/0035_merge_20260331_1500.py` para unificar:
  - `0034_merge_20260329_0001`
  - `0034_rename_comedores_a_comedor_89ef7d_idx_comedores_a_comedor_4b1714_idx_and_more`
- Se dejo `comedores/migrations/0034_rename_comedores_a_comedor_89ef7d_idx_comedores_a_comedor_4b1714_idx_and_more.py`
  como no-op porque duplicaba los `RenameIndex` ya definidos en
  `0033_rename_comedores_a_comedor_89ef7d_idx_comedores_a_comedor_4b1714_idx_and_more.py`.

## Impacto

- `makemigrations` deja de autogenerar una nueva migracion para
  `temporary_password_plaintext`.
- `migrate` vuelve a tener una unica migracion responsable de crear ese campo en
  `users_profile`.
- `migrate` deja de fallar al intentar aplicar por segunda vez el mismo rename de
  indices en `AuditColaboradorEspacio`.
- No se alteran operaciones funcionales del esquema; se normaliza el historial de
  migraciones para que sea reproducible en ambientes limpios y en PRD.

## Validacion

- Revision manual de dependencias de migraciones.
