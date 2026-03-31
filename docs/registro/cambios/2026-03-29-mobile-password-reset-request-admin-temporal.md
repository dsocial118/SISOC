# Solicitud de reseteo mobile y generación admin de contraseña temporal

## Contexto

La app mobile no tenía un flujo de "olvidé mi contraseña" compatible con el esquema actual de usuarios PWA con contraseña temporal y cambio obligatorio en el primer ingreso.

## Cambio realizado

- La API de `POST /api/users/password-reset/request/` ahora acepta:
  - `email` para el flujo existente por correo;
  - `username` para el flujo mobile, marcando una solicitud interna pendiente.
- Se agregó `Profile.password_reset_requested_at` para persistir el pedido pendiente de reseteo mobile.
- En el listado web de usuarios:
  - se muestra la columna `Reset solicitado`;
  - si hay pedido pendiente, aparece la acción `Generar temporal`.
- La acción admin genera una nueva contraseña aleatoria temporal, invalida tokens activos, limpia el pedido pendiente y deja al usuario nuevamente obligado a cambiar la contraseña en el próximo login.
- En `mobile/` se agregó la pantalla de recuperación por username accesible desde el login.

## Impacto

- El usuario mobile puede pedir reseteo sin email ni acceso web.
- El backoffice conserva control manual sobre la emisión de la nueva contraseña temporal.
- El flujo sigue reutilizando la misma lógica de `must_change_password` y contraseña temporal visible en edición.
