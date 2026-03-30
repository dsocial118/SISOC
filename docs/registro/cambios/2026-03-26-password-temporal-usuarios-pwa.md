# 2026-03-26 - Contraseña temporal visible para usuarios PWA

## Contexto

El alta web de usuarios con acceso PWA ya generaba una contraseña automática y marcaba el cambio obligatorio al primer ingreso. Faltaban tres cosas operativas:

- saber cuál fue la contraseña generada;
- conservar la contraseña actual cuando un usuario existente pasaba a tener acceso PWA;
- dejar de mostrar la contraseña temporal una vez cambiada.

## Cambio aplicado

- Se agregó `Profile.temporary_password_plaintext` para conservar la contraseña temporal visible mientras siga pendiente el cambio.
- Cuando se crea un usuario nuevo como PWA desde web:
  - se genera contraseña automática;
  - se guarda en el usuario;
  - se persiste también en `temporary_password_plaintext`;
  - el flujo redirige a la edición del usuario para ver el dato en pantalla.
- Cuando un usuario ya existente recibe acceso PWA desde edición:
  - se conserva su contraseña actual si no se cargó una nueva;
  - no se genera una contraseña temporal nueva.
- La pantalla de edición del usuario muestra una alerta con la contraseña temporal solo si:
  - el perfil tiene `must_change_password=True`;
  - y existe `temporary_password_plaintext`.
- Al cambiar o resetear contraseña:
  - se limpia `temporary_password_plaintext`.

## Archivos principales

- `users/models.py`
- `users/migrations/0018_profile_temporary_password_plaintext.py`
- `users/forms.py`
- `users/views.py`
- `users/services_auth.py`
- `users/templates/user/user_form.html`
- `tests/test_users_auth_flows.py`

## Validación

- `docker-compose exec django pytest tests/test_users_auth_flows.py tests/test_users_pwa_forms.py`

## Supuestos

- Como el módulo no tiene una vista separada de detalle de usuario, se tomó la pantalla de edición como “detalle” operativo del usuario.
