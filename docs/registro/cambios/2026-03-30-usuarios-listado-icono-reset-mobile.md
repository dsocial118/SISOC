# Listado de usuarios: ícono para reset mobile pendiente

## Fecha
- 2026-03-30

## Alcance
- Ajuste visual puntual en el listado web de usuarios para la columna `Reset`.

## Cambios
- Cuando un usuario tiene `password_reset_requested_at` informado, la tabla web ya no muestra el valor textual del indicador.
- En su lugar se renderiza un ícono rojo de alerta en la columna `Reset`.
- Cuando no existe solicitud pendiente, la tabla mantiene `-` como valor vacío.

## Validación
- `docker-compose exec django pytest tests/test_users_auth_flows.py -k user_list_shows_reset_pending_indicator_when_reset_pending`
