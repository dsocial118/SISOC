# Campanita de reset mobile junto al usuario en sidebar

Fecha: 2026-03-30

## Qué cambió

- Se movió la notificación de pedidos de reseteo de clave mobile desde el header superior al bloque de usuario de la barra lateral.
- La campanita ahora se renderiza al lado del nombre del usuario en `templates/includes/sidebar/opciones.html`.
- El comportamiento se mantiene igual para permisos:
  - solo se muestra para administradores habilitados por `users.context_processors.mobile_password_reset_notifications`;
  - si hay pedidos pendientes, muestra badge rojo con cantidad;
  - al hacer click abre el mismo tooltip con mensaje y acceso al listado de usuarios.

## Alcance

- Se eliminó la campanita del header superior para evitar duplicación visual.
- Se actualizaron los tests de auth flows para validar la presencia y ausencia del control en la sidebar.

## Validación

- `docker-compose exec django pytest tests/test_users_auth_flows.py -k "sidebar_shows_mobile_reset_notification_for_admin_with_pending_request or sidebar_hides_mobile_reset_notification_for_non_admin or sidebar_shows_mobile_reset_notification_for_admin_without_pending_request"`
