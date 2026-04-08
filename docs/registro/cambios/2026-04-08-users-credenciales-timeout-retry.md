# 2026-04-08 - Credenciales masivas: timeout controlado y reintento de envio

## Contexto

El envio masivo de credenciales corre dentro de una request web sincrona. Si el
SMTP queda colgado esperando respuesta, el worker de Gunicorn puede abortar la
request y provocar un `500`, aun cuando el flujo procesa las filas una por una.

## Cambio aplicado

- Se agrego un timeout controlado por intento de envio de mail, usando una
  guarda local para cortar antes de llegar al timeout del worker web.
- Se agrego un reintento automatico por fila cuando el envio falla por timeout o
  error SMTP/transitorio.
- Si el segundo intento tambien falla, la fila queda rechazada con mensaje
  explicito y el lote continua con las demas filas.
- Se agregaron tests de regresion para:
  - timeout en el primer intento y exito en el segundo;
  - timeout persistente con rollback de la fila y sin `500` del flujo.

## Validacion

- `USE_SQLITE_FOR_TESTS=1 python -m pytest tests\\test_users_bulk_credentials.py -q`
- `python -m black --check users\\services_bulk_credentials.py tests\\test_users_bulk_credentials.py`

## Limite conocido

El flujo sigue siendo sincrono dentro de la request web. Este ajuste evita que
un timeout individual del SMTP derribe toda la operacion y agrega un reintento,
pero no reemplaza una futura migracion a procesamiento asincrono si el volumen
del lote crece mucho.
