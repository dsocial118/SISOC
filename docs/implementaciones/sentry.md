# Implementación de Sentry en SISOC

Esta guía explica cómo está integrada la app `sentry` en SISOC y cómo usarla en QA/Producción.

## 1. Qué hace la implementación actual

La integración se apoya en 4 piezas:

1. `sentry/apps.py`
   - En `SentryConfig.ready()` llama `initialize_sentry_sdk()` al iniciar Django.
2. `sentry/services.py`
   - Inicializa `sentry_sdk` una sola vez por proceso.
   - Solo activa Sentry si se cumplen condiciones de entorno.
3. `sentry/handlers.py`
   - Handler de logging que reenvía eventos `ERROR`/`CRITICAL` a Sentry.
4. `sentry/middleware.py`
   - Adjunta contexto de usuario autenticado (`id`, `username`) en cada request.

Además, `config/settings.py` ya incluye:

- `sentry.apps.SentryConfig` en `INSTALLED_APPS`.
- `sentry.middleware.SentryUserContextMiddleware` en `MIDDLEWARE`.
- Handler `sentry.handlers.SentryEventHandler` en `LOGGING`.

## 2. Cuándo se inicializa Sentry

`initialize_sentry_sdk()` inicializa Sentry únicamente cuando:

1. `SENTRY_ENABLED=true` (si no existe, por defecto se toma `true`).
2. `ENVIRONMENT` es `qa` o `prd`.
3. `SENTRY_DSN` tiene valor.

Si `ENVIRONMENT=dev`, Sentry no se inicializa aunque haya DSN.

## 3. Variables de entorno

Variables soportadas (definidas en `.env.example`):

```env
SENTRY_ENABLED=true
SENTRY_DSN=
SENTRY_ENVIRONMENT=dev
SENTRY_RELEASE=
SENTRY_SEND_DEFAULT_PII=false
SENTRY_TRACES_SAMPLE_RATE=0.0
SENTRY_PROFILES_SAMPLE_RATE=0.0
```

### Recomendación para QA/PRD

En `.env.qa` y `.env.prod` definir explícitamente:

```env
SENTRY_ENABLED=true
SENTRY_DSN=https://<public_key>@o<org>.ingest.sentry.io/<project_id>
SENTRY_ENVIRONMENT=sisoc-qa   # qa
# SENTRY_ENVIRONMENT=sisoc-prd # prd
SENTRY_RELEASE=<tag_o_sha_del_deploy>
SENTRY_SEND_DEFAULT_PII=false
SENTRY_TRACES_SAMPLE_RATE=0.0
SENTRY_PROFILES_SAMPLE_RATE=0.0
```

Notas:

- Si `SENTRY_ENVIRONMENT` queda vacío, SISOC usa mapeo automático:
  - `qa -> sisoc-qa`
  - `prd -> sisoc-prd`
- Mantener `SENTRY_SEND_DEFAULT_PII=false` salvo necesidad explícita.

## 4. Qué se reporta automáticamente

1. Excepciones no manejadas en Django (integración `DjangoIntegration`).
2. Logs con nivel `ERROR` o mayor (handler custom de Sentry).
3. Contexto de usuario autenticado en requests web:
   - `id`: `user.pk`
   - `username`: `user.get_username()`

## 5. Cómo reportar errores desde código

Patrón recomendado en SISOC: usar `logging`.

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

- Con `logger.exception(...)` (o `exc_info=True`) el handler envía `capture_exception`.
- Con `logger.error(...)` sin traceback, envía `capture_message`.

## 6. Smoke test manual

Con el entorno levantado y `ENVIRONMENT=qa|prd`:

```bash
docker compose exec django python manage.py shell -c "import logging; logging.getLogger('sentry.smoke').error('Smoke test Sentry: mensaje de error')"
```

Luego verificar en Sentry que aparezca el evento en el proyecto correcto.

## 7. Validación automatizada

Tests existentes:

```bash
docker compose exec django pytest sentry/tests.py -q
```

Cobertura actual:

- Inicialización con/sin DSN.
- Restricción por entorno (`dev` no inicializa).
- Mapeo de entorno (`qa` y `prd`).
- Captura de excepción/mensaje por handler.
- Contexto de usuario en middleware.

## 8. Troubleshooting rápido

### No llegan eventos a Sentry

Revisar:

1. `ENVIRONMENT` sea `qa` o `prd`.
2. `SENTRY_ENABLED=true`.
3. `SENTRY_DSN` configurado.
4. Reinicio del contenedor Django tras cambiar `.env`.
5. Que el evento sea `ERROR` o mayor.

### El evento llega sin usuario

- El request era anónimo o no autenticado.
- Verificar que `AuthenticationMiddleware` y `SentryUserContextMiddleware` estén activos en `MIDDLEWARE`.

### Eventos duplicados

- Evitar combinar para el mismo error:
  - `logger.exception(...)`
  - y además `sentry_sdk.capture_exception(...)`

Usar un único mecanismo por error para evitar duplicados.
