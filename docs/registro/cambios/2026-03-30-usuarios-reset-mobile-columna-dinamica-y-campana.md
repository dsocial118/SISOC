# Usuarios: columna dinámica y campana por reset mobile

## Fecha
- 2026-03-30

## Alcance
- Ajuste visible en el listado web de usuarios y en el header de la web para solicitudes de reset mobile.

## Cambios
- La columna `Reset` del listado de usuarios ahora sólo se muestra cuando existe al menos una solicitud pendiente de reset mobile en el sistema.
- Cuando no hay solicitudes pendientes, la tabla oculta esa columna completa.
- Se agregó una notificación global en el header, ubicada a la izquierda del botón de salir.
- La notificación se muestra sólo para usuarios administradores con capacidad de gestionar usuarios.
- Al abrir la campana se despliega una tarjeta inferior con el mensaje de que un usuario mobile pidió resetear la clave y un acceso directo al listado de usuarios.

## Validación
- `docker-compose exec django pytest tests/test_users_auth_flows.py -k "user_list_shows_reset_pending_indicator_when_reset_pending or user_list_hides_reset_column_when_no_pending_requests or header_shows_mobile_reset_notification_for_admin_with_pending_request or header_hides_mobile_reset_notification_for_non_admin"`
