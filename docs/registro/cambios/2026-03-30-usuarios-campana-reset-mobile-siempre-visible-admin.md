# Usuarios: campana de reset mobile siempre visible para admin

## Fecha
- 2026-03-30

## Alcance
- Ajuste del header web para asegurar visibilidad de la campana de reset mobile en perfiles administradores.

## Cambios
- La campana de reset mobile ahora se muestra siempre para usuarios administradores.
- Cuando hay solicitudes pendientes:
  - la campana se marca en rojo;
  - se muestra badge con cantidad;
  - el mensaje informa que un usuario mobile pidió resetear la clave.
- Cuando no hay solicitudes pendientes:
  - la campana sigue visible en estado neutro;
  - el tooltip informa que no hay pedidos activos.
- Se mantuvo sin cambios la regla de ocultar esta campana para usuarios no administradores.

## Validación
- `docker-compose exec django pytest tests/test_users_auth_flows.py -k "user_list_shows_reset_pending_indicator_when_reset_pending or user_list_hides_reset_column_when_no_pending_requests or header_shows_mobile_reset_notification_for_admin_with_pending_request or header_hides_mobile_reset_notification_for_non_admin or header_shows_mobile_reset_notification_for_admin_without_pending_request"`
