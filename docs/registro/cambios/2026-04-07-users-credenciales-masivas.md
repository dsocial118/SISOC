# 2026-04-07 - Envio masivo de credenciales de usuarios

## Contexto

En el modulo web de usuarios hacia falta una operatoria para enviar credenciales en lote cuando se crean varios accesos juntos. El equipo necesitaba una carga simple por Excel, con plantilla descargable, validacion del usuario existente y sincronizacion del mail y la password vigentes antes de enviar el correo.

## Cambio aplicado

- Se agrego una pantalla web nueva en `users` para subir un archivo `.xlsx` con columnas `usuario`, `mail` y `password`.
- La pantalla reutiliza el patron visual de importaciones existentes: card central, ayuda sobre el formato esperado, boton `Descargar plantilla` y resumen de resultados al finalizar.
- Se agrego una plantilla Excel generada desde backend con hoja `credenciales` y encabezados `usuario`, `mail`, `password`.
- El procesamiento:
  - normaliza encabezados por trim, case y acentos;
  - ignora columnas extra;
  - rechaza filas sin `usuario`, `mail` o `password`;
  - busca al usuario por `username__iexact`;
  - actualiza `email` si difiere;
  - actualiza la password solo si no coincide con la vigente;
  - envia el correo con la credencial final usada.
- Cuando la password cambia, se replica el flujo de password temporal existente:
  - `must_change_password=True`;
  - `password_changed_at=None`;
  - `initial_password_expires_at` usando `INITIAL_PASSWORD_MAX_AGE_HOURS`;
  - `password_reset_requested_at=None`;
  - `temporary_password_plaintext` con la clave enviada;
  - eliminacion de tokens DRF del usuario.
- Cada fila se procesa dentro de su propia transaccion. Si falla la validacion o el envio del mail de una fila, los cambios de esa fila se revierten y el resto del archivo continua.
- Se agrego un permiso dedicado `auth.role_enviar_credenciales_masivas`, visible en el registry IAM y asignado por bootstrap al grupo `Admin`.
- El listado de usuarios muestra el boton `ENVIO DE CREDENCIALES` solo cuando el actor tiene `auth.change_user` y `auth.role_enviar_credenciales_masivas` o es superuser, reutilizando el mismo estilo azul del boton `Exportar`.

## Archivos principales

- `users/services_bulk_credentials.py`
- `users/views.py`
- `users/urls.py`
- `users/forms.py`
- `users/services.py`
- `users/templates/user/bulk_credentials_form.html`
- `users/templates/user/bulk_credentials_email.txt`
- `users/migrations/0026_admin_bulk_credentials_permission.py`
- `users/bootstrap/groups_seed.py`
- `core/permissions/registry.py`
- `tests/test_users_bulk_credentials.py`

## Validacion

- `.\.venv\Scripts\python.exe -m black --check core\permissions\registry.py users\bootstrap\groups_seed.py users\forms.py users\services.py users\urls.py users\views.py users\services_bulk_credentials.py tests\test_users_bulk_credentials.py`
- `set USE_SQLITE_FOR_TESTS=1; .\.venv\Scripts\python.exe -m pytest tests\test_users_bulk_credentials.py -q`

## Supuestos

- En esta iteracion solo se soporta `.xlsx`; no se habilitan `.csv` ni `.xls`.
- El username del Excel es solo llave de busqueda y nunca se modifica.
- El correo se envia aun cuando mail y password ya coinciden con los datos vigentes, para cubrir el caso operativo de reenvio de credenciales.
