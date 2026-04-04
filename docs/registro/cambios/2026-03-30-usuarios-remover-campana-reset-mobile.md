# Remoción de la campanita de reset mobile

Fecha: 2026-03-30

## Qué cambió

- Se removió la campanita de notificaciones de reset mobile de la interfaz web.
- Se eliminó el render en la sidebar del usuario y el context processor global que la alimentaba.
- Se quitaron los tests que verificaban esa UI porque la funcionalidad visual ya no existe.

## Qué se mantiene

- Sigue vigente el indicador de reset pendiente en el listado de usuarios.
- Sigue vigente el flujo de generación de contraseña temporal desde la edición del usuario mobile.

## Validación

- `docker-compose exec django pytest tests/test_users_auth_flows.py -k "user_list_shows_reset_pending_indicator_when_reset_pending or user_list_hides_reset_column_when_no_pending_requests or user_update_view_shows_reset_alert_and_button_inside_mobile_card or generate_temporary_password_view_resets_flags_and_redirects_to_edit"`
