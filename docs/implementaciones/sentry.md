# Implementacion de Sentry en SISOC

Esta guia explica como esta integrada la app `sentry` en SISOC y como usarla en QA, Homologacion y Produccion.

## 1. Que hace la implementacion actual

La integracion se apoya en 5 piezas:

1. `sentry/apps.py`
   - En `SentryConfig.ready()` llama `initialize_sentry_sdk()` al iniciar Django.
2. `sentry/services.py`
   - Inicializa `sentry_sdk` una sola vez por proceso.
   - Solo activa Sentry si se cumplen condiciones de entorno.
3. `sentry/handlers.py`
   - Handler de logging que reenvia eventos `ERROR`/`CRITICAL` a Sentry.
4. `sentry/middleware.py`
   - Adjunta contexto de usuario autenticado (`id`, `username`) en cada request.
5. `sentry/context_processors.py` + `templates/includes/scripts/sentry_replay.html`
   - Exponen config de Sentry al frontend e inicializan Session Replay en templates base.

Ademas, `config/settings.py` ya incluye:

- `sentry.apps.SentryConfig` en `INSTALLED_APPS`.
- `sentry.middleware.SentryUserContextMiddleware` en `MIDDLEWARE`.
- Handler `sentry.handlers.SentryEventHandler` en `LOGGING`.

## 2. Cuando se inicializa Sentry

`initialize_sentry_sdk()` inicializa Sentry unicamente cuando:

1. `SENTRY_ENABLED=true` (si no existe, por defecto se toma `true`).
2. `ENVIRONMENT` es `qa`, `homologacion` o `prd`.
3. `SENTRY_DSN` (definido por variable de entorno) tiene valor.
4. `SENTRY_DSN` es un DSN valido (incluye `public_key@...`).

Si `ENVIRONMENT=dev`, Sentry no se inicializa aunque haya DSN.

## 3. Variables de entorno

Variables soportadas (configurables por `.env`):

```env
SENTRY_ENABLED=true
SENTRY_DSN=
SENTRY_RELEASE=
SENTRY_SEND_DEFAULT_PII=false
# Rates/replay definidos en config/settings.py segun ENVIRONMENT
```

### Recomendacion para QA/Homologacion/PRD

Notas:

- `SENTRY_DSN` se inyecta por entorno (`.env`/secret manager), nunca hardcodeado.
- `SENTRY_LOG_EVENT_LEVEL` se define en `config/settings.py` con default `WARNING`.
- El environment enviado a Sentry se deriva siempre de `ENVIRONMENT` (sin variable extra):
  - `qa -> sisoc-qa`
  - `homologacion -> sisoc-homologacion`
  - `prd -> sisoc-prd`
- Mantener `SENTRY_SEND_DEFAULT_PII=false` salvo necesidad explicita.
- Los rates se definen condicionalmente en `config/settings.py`:
  - `ENVIRONMENT=qa`: `SENTRY_ERROR_SAMPLE_RATE=0.75`, `SENTRY_TRACES_SAMPLE_RATE=0.75`, sin replay.
  - `ENVIRONMENT=homologacion`: `SENTRY_ERROR_SAMPLE_RATE=1.0`, `SENTRY_TRACES_SAMPLE_RATE=1.0`, replay habilitado.
  - `ENVIRONMENT=prd`: `SENTRY_ERROR_SAMPLE_RATE=1.0`, `SENTRY_TRACES_SAMPLE_RATE=1.0`, replay al 100%.

## 4. Que se reporta automaticamente

1. Excepciones no manejadas en Django (integracion `DjangoIntegration`).
2. Logs con nivel configurable (`SENTRY_LOG_EVENT_LEVEL`, default `WARNING`) via handler custom.
3. Contexto de usuario autenticado en requests web:
   - `id`: `user.pk`
   - `username`: `user.get_username()`
4. Session Replay en frontend (templates base) cuando `SENTRY_REPLAY_ENABLED=true`.

## 5. Como reportar errores desde codigo

Patron recomendado en SISOC: usar `logging`.

```python
import logging

logger = logging.getLogger(__name__)

try:
    proceso_critico()
except Exception:
    logger.exception("Error procesando relevamiento %s", relevamiento_id)
    raise
```

Comportamiento:

- Con `logger.exception(...)` (o `exc_info=True`) el handler envia `capture_exception`.
- Con `logger.warning/error/critical(...)` sin traceback, envia `capture_message` con el nivel correspondiente.

## 6. Smoke test manual

Con el entorno levantado y `ENVIRONMENT=qa|homologacion|prd`:

```bash
docker compose exec django python manage.py shell -c "import logging; logging.getLogger('sentry.smoke').error('Smoke test Sentry: mensaje de error')"
```

Luego verificar en Sentry que aparezca el evento en el proyecto correcto.

## 7. Validacion automatizada

Tests existentes:

```bash
docker compose exec django pytest sentry/tests.py -q
```

Cobertura actual:

- Inicializacion con/sin DSN.
- Restriccion por entorno (`dev` no inicializa).
- Mapeo de entorno (`qa`, `homologacion` y `prd`).
- Captura de excepcion/mensaje por handler.
- Contexto de usuario en middleware.

## 8. Troubleshooting rapido

### No llegan eventos a Sentry

Revisar:

1. `ENVIRONMENT` sea `qa`, `homologacion` o `prd`.
2. `SENTRY_ENABLED=true`.
3. `SENTRY_DSN` definido en variables de entorno.
4. `SENTRY_DSN` con formato valido: `https://<public_key>@o<org>.ingest.sentry.io/<project_id>`.
5. Revisar logs de arranque por warning `SENTRY_DSN invalido...`.
6. Reinicio del contenedor Django tras cambiar `.env`.
7. Que el evento sea `ERROR` o mayor.

### El evento llega sin usuario

- El request era anonimo o no autenticado.
- Verificar que `AuthenticationMiddleware` y `SentryUserContextMiddleware` esten activos en `MIDDLEWARE`.

### Eventos duplicados

- Evitar combinar para el mismo error:
  - `logger.exception(...)`
  - y ademas `sentry_sdk.capture_exception(...)`

Usar un unico mecanismo por error para evitar duplicados.
