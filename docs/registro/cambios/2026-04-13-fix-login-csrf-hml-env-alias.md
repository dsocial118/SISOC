# Fix login CSRF en entorno HML por valor de ENVIRONMENT

Fecha: 2026-04-13

## Que cambio

- `config/settings.py` usa `ENVIRONMENT=hml` como valor operativo para el perfil similar a producción.
- El login web de HML vuelve a calcular hardening y orígenes confiables con esquema HTTPS cuando el entorno usa `hml`.
- Se agregó test de regresión en `tests/test_settings_env_parsing.py` para cubrir el caso `ENVIRONMENT=hml`.

## Causa raiz

El perfil HTTPS/CSRF de SISOC depende de que `ENVIRONMENT` use un valor productivo-like (`hml` o `prd`).

Si un servidor nuevo no usaba `ENVIRONMENT=hml`, el runtime podía quedar tratado como no productivo:

- `DEFAULT_SCHEME` pasaba a `http`
- `CSRF_TRUSTED_ORIGINS` se derivaba como `http://<host>`
- el login web accedido por `https://...` podía fallar con `403 Verificacion CSRF fallida`

## Decision principal

Se eligió corregir la causa raíz en settings y no relajar CSRF ni tocar la vista de login.

De esta forma el despliegue sigue siendo estricto y la convención operativa queda alineada a `qa`, `hml` y `prd`.

## Validacion esperada

- `pytest -q tests/test_settings_env_parsing.py`
- En HML, verificar que el `.env` del servidor use `ENVIRONMENT=hml` y que el login web deje de responder 403 por CSRF.
