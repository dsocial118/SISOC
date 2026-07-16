# CDI: alta automática de referente

## Cambio

Al guardar un CDI con nombre, apellido y email de referente completos, se crea
automáticamente un usuario `CDI - Referente centro` y su `AccesoCDI`.

## Garantías

- El guardado del CDI no falla si no se puede crear el usuario.
- Re-guardar no duplica accesos ni usuarios.
- Sin email, email ya usado o falta de delegación, se conserva el CDI y se
  informa el resultado mediante mensajes.

## Validación

`docker compose exec -T django pytest centrodeinfancia/tests/test_automatic_user_provisioning.py -p no:cacheprovider`
