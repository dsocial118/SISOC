# Cambio obligatorio de contraseña en Mobile

## Contexto

Los usuarios PWA creados con contraseña automática ya quedaban marcados con `must_change_password=True` en backend, pero la app `mobile/` no tenía un flujo para resolver ese primer ingreso.

## Cambio realizado

- Se agregó el endpoint autenticado `POST /api/users/password-change-required/`.
- El endpoint valida la nueva contraseña con las reglas actuales de Django y limpia:
  - `must_change_password`
  - `password_changed_at`
  - `initial_password_expires_at`
  - `temporary_password_plaintext`
- La app mobile ahora:
  - persiste `mustChangePassword` en la sesión local;
  - redirige al usuario autenticado a una pantalla obligatoria de cambio de contraseña;
  - bloquea el acceso al resto de la app hasta completar el cambio;
  - actualiza el estado local una vez guardada la nueva contraseña.

## Impacto

- Los usuarios PWA con contraseña temporal pueden completar el primer ingreso desde Mobile sin pasar por web.
- No cambia el contrato de login existente; se agrega un paso posterior basado en `GET /api/users/me/`.
- No se modifican permisos ni alcance PWA.
