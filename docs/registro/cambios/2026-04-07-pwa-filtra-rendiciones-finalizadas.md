# PWA mensajes: ocultar notificaciones de rendiciones finalizadas

## Contexto

Aunque backend ya no generaba nuevas notificaciones cuando una rendicion quedaba
`finalizada`, todavia podian verse en la bandeja mobile comunicados viejos que
habian quedado publicados antes de esa correccion.

## Cambio realizado

- La capa de mensajes PWA ahora filtra los comunicados de accion
  `rendicion_detalle` cuando la rendicion apuntada ya se encuentra en estado
  `finalizada`.
- El filtro aplica tanto al listado como al acceso puntual del mensaje.

## Validacion

- `docker compose exec django pytest tests/test_pwa_mensajes_api.py -q`
