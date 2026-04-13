# Fix login CSRF en entorno HML por alias de ENVIRONMENT

Fecha: 2026-04-13

## Que cambio

- `config/settings.py` ahora normaliza aliases de `ENVIRONMENT` antes de calcular hardening y orígenes confiables.
- Se agregó soporte para `hml -> homologacion`, además de aliases seguros de producción (`prod` y `production` -> `prd`).
- Se agregó test de regresión en `tests/test_settings_env_parsing.py` para cubrir el caso `ENVIRONMENT=hml`.

## Causa raiz

El perfil HTTPS/CSRF de SISOC depende de que `ENVIRONMENT` quede normalizado a `homologacion` o `prd`.

Si un servidor nuevo define `ENVIRONMENT=hml`, el runtime quedaba tratado como no productivo:

- `DEFAULT_SCHEME` pasaba a `http`
- `CSRF_TRUSTED_ORIGINS` se derivaba como `http://<host>`
- el login web accedido por `https://...` podía fallar con `403 Verificacion CSRF fallida`

## Decision principal

Se eligió corregir la causa raíz en settings y no relajar CSRF ni tocar la vista de login.

De esta forma el despliegue sigue siendo estricto, pero tolera aliases operativos razonables del entorno.

## Validacion esperada

- `pytest -q tests/test_settings_env_parsing.py`
- En HML, verificar que el `.env` del servidor use `ENVIRONMENT=hml` o `ENVIRONMENT=homologacion` y que el login web deje de responder 403 por CSRF.
