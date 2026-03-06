# Registro de cambio: variables faltantes en `.env.qa` y `.env.prod`

Fecha: 2026-03-06

## Contexto

Se detectó que los archivos de entorno de QA y Producción no incluían todas las variables documentadas en `.env.example` y usadas por `config/settings.py`.

## Cambios aplicados

- Se agregaron en `.env.qa` y `.env.prod` las variables faltantes:
  - `USE_SQLITE_FOR_TESTS`, `PYTEST_RUNNING`
  - `GOOGLE_MAPS_API_KEY`
  - `LOG_FALLBACK_DIR`
  - `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL`, `EMAIL_TIMEOUT`, `DEFAULT_FROM_EMAIL`
  - `PASSWORD_RESET_TIMEOUT`, `INITIAL_PASSWORD_MAX_AGE_HOURS`
- Además, en `.env.qa` se incorporaron `RUN_UID` y `RUN_GID` (presentes en la plantilla base).
- Además, en `.env.prod` se incorporó `LOG_DIR` explícito (`/var/log/sisoc`) para mantener consistencia con QA.

## Impacto

- No se introducen secretos ni credenciales.
- No cambia comportamiento si estas variables ya tomaban defaults en `settings.py`; el cambio explicita configuración para evitar omisiones entre entornos.

