# CDI: alta automática de usuarios de trabajadores

## Cambio

`Trabajador` incorpora el vínculo opcional `usuario`. Al guardar un trabajador
con email, el referente del CDI crea un usuario `CDI - Trabajador` y queda
vinculado por ese FK, sin crear `AccesoCDI`.

## Garantías

- Sin email no se crea usuario.
- Si el trabajador ya tiene `usuario`, re-guardar no crea otro.
- Un fallo de provisión no revierte el guardado del trabajador; la creación y
  el vínculo se ejecutan dentro de la transacción del servicio reutilizado.

## Validación

`docker compose exec -T django pytest centrodeinfancia/tests/test_automatic_user_provisioning.py -p no:cacheprovider` (7 passed).
