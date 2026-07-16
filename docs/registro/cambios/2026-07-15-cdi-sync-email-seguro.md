# CDI: sincronización segura de emails

## Cambio

Al editar los datos de contacto del referente o de un trabajador, el email del
usuario vinculado se actualiza solo mientras `Profile.must_change_password` es
verdadero.

## Garantías

- Después de que la persona modifica su cuenta, el email de `User` no se pisa y
  se muestra un aviso.
- `username` no se recalcula ni modifica en ninguna actualización.

## Validación

`docker compose exec -T django pytest centrodeinfancia/tests/test_automatic_user_provisioning.py -p no:cacheprovider` (11 passed).
