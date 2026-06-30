# Usuarios: email opcional, username como clave, envío masivo agrupado

Issue: #1979.

## Cambios funcionales

- **Email opcional y no único en usuarios.** `UserCreationForm` y `CustomUserChangeForm`
  ya no exigen `email`, ni rechazan emails repetidos. El `username` sigue siendo el
  identificador único (constraint a nivel BD de `auth.User`). Se quitó la validación
  equivalente en `services_pwa.crear_operador_pwa` y `services_generate_user._validar_email`
  (en este último solo el check de duplicado; el email continúa siendo obligatorio
  para enviar credenciales del referente).
- **Importación masiva sin columna `Correo`.** `services_user_import` ahora trata
  `correo` como columna opcional. Si la fila no trae email, el username se genera
  desde `apellido.nombre` normalizado; si la fila trae email pero ya está en uso,
  el usuario se crea igual (sin marcar `SKIPPED`). Si la fila no tiene email y
  `send_credentials=True`, el envío se omite silenciosamente.
- **Envío masivo agrupa por destinatario.** Cuando dos o más filas comparten el
  mismo mail destinatario (informado en la planilla o resuelto desde `user.email`),
  `process_bulk_credentials_file` y el worker `process_bulk_credentials_job` envían
  un único correo al destinatario con la lista de credenciales. Cada fila del grupo
  queda persistida individualmente como `SENT` para preservar el detalle del lote.
- **Datos personales en el email.** Los templates `bulk_credentials_email.txt` y
  `bulk_credentials_email_inet.txt` ahora muestran `Nombre y apellido` (`first_name`
  + `last_name`) además de usuario y contraseña. En el modo agrupado se itera
  sobre la lista de credenciales mostrando nombre/apellido por cada usuario.

## Compatibilidad

- `services_bulk_credentials.process_bulk_credentials_row` se mantiene como wrapper
  fino sobre `process_bulk_credentials_group` para no romper consumidores externos.
- `services_generate_user._enviar_credenciales` y
  `services_user_import._enviar_credenciales_import` arman un `BulkCredentialEntry`
  singular para reutilizar el mismo template con el contexto nuevo (`entries`,
  `is_grouped`).
- `services_auth.request_password_reset_for_email` ya iteraba sobre las coincidencias
  de email, por lo que sigue siendo correcto con emails repetidos.

## Defensas implementadas

- **INET con centros distintos no se agrupa.** `_row_grouping_key` usa el par
  `(recipient, nombre_del_centro)` como clave cuando el send_type requiere el
  centro. Dos filas con mismo mail destinatario pero centros distintos viajan
  en correos separados, evitando mezclar datos de centros en un mismo cuerpo.
- **Cache de destinatarios.** `_build_recipient_cache(rows)` pre-carga
  `username -> email` en una sola query antes de procesar el lote, eliminando
  el O(N) de lookups del flujo anterior.
- **Resume sin duplicar correos.** El worker aplica dos reglas defensivas en
  `_select_group_for_row`:
  1. Si la fila primaria ya tiene `attempts > 0` (resume tras fallo posible
     post-envío SMTP exitoso), se procesa SOLA — no se re-arma el grupo.
  2. Si existe alguna fila SENT en este mismo job con `mail_destino` igual al
     destinatario candidato, no se agrupan filas pendientes con él: cada una
     se envía por separado para no volver a entregar las credenciales que el
     destinatario ya recibió en el correo agrupado original.

## Pendientes

- El template INET en modo agrupado mantiene el saludo con
  `nombre_del_centro` del primer entry; con la nueva regla R3 esto siempre
  coincide para todas las filas del grupo.
