# 2026-05-26 - Sentry filtra SystemExit de Gunicorn

## Contexto
- Sentry reportaba eventos `SystemExit: 1` desde `gunicorn.error`.
- El stack no incluia frames de aplicacion: Gunicorn abortaba un worker mientras esperaba datos del socket.
- El evento generaba ruido operativo y podia confundirse con un bug funcional de Django.

## Cambios aplicados
- Se agrego un `before_send` en la inicializacion de Sentry para descartar solo eventos `SystemExit` emitidos por loggers `gunicorn.*`.
- Se ajusto el handler propio de Sentry para no capturar `SystemExit` de `gunicorn.*`.
- Se agregaron tests de regresion para confirmar que:
  - `gunicorn.error` + `SystemExit` se descarta;
  - errores no-Gunicorn se conservan;
  - errores Gunicorn distintos de `SystemExit` se conservan.

## Impacto esperado
- Menos ruido en Sentry por abortos internos de Gunicorn.
- Los errores reales de Django, aplicacion y Gunicorn no relacionados con `SystemExit` siguen reportandose.

## Validacion
- `docker compose -f BACKOFFICE\docker-compose.yml exec -T django pytest sentry/tests.py -q`
- `docker compose -f BACKOFFICE\docker-compose.yml exec -T django python manage.py check`

## Riesgos y rollback
- Riesgo principal: que un `SystemExit` de Gunicorn oculte una senal operativa util.
- Mitigacion: el filtro esta acotado a loggers `gunicorn.*`; no afecta `django.request` ni errores de aplicacion.
- Rollback: revertir los cambios en `sentry/services.py`, `sentry/handlers.py`, `sentry/tests.py` y este registro.
