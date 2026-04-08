# 2026-04-08 - Credenciales masivas: corte preventivo del lote antes del timeout web

## Contexto

Despues del fix de timeout SMTP, siguieron apareciendo `SystemExit` en
`/usuarios/credenciales-masivas/`, pero ahora durante `check_password`.

La causa raiz es distinta: el flujo sigue corriendo sincronicamente dentro de la
request web, y un lote suficientemente grande puede acumular tiempo de CPU
(PBKDF2 en `check_password` / `set_password`) hasta alcanzar el timeout del
worker de Gunicorn.

## Cambio aplicado

- Se agrego un presupuesto total de tiempo para el lote, derivado del timeout
  del worker web con un margen de seguridad.
- Si el sistema detecta que no queda tiempo suficiente para iniciar otra fila,
  marca la fila actual y las restantes como rechazadas con mensaje explicito en
  lugar de dejar que el worker caiga por timeout.
- El envio de mail ahora recibe el tiempo restante del lote para no iniciar
  reintentos que ya no entran en el presupuesto total.
- Se agrego una optimizacion para evitar `check_password` cuando el usuario ya
  tiene la misma password temporal en `Profile.temporary_password_plaintext`.
- Se corrigio la firma del helper de envio para usar explicitamente
  `recipient_email` como destino.

## Validacion

- `USE_SQLITE_FOR_TESTS=1 python -m pytest tests\\test_users_bulk_credentials.py -q`
- `python -m black --check users\\services_bulk_credentials.py tests\\test_users_bulk_credentials.py`

## Limite conocido

El flujo sigue siendo sincrono; cuando el lote excede el presupuesto de tiempo,
se corta en forma controlada y se debe reintentar en archivos mas chicos.
