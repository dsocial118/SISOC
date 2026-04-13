# Estandarizacion de ENVIRONMENT a qa, hml y prd

Fecha: 2026-04-13

## Que cambio

- El runtime de SISOC deja de tratar `homologacion` como valor operativo de `ENVIRONMENT`.
- Los valores activos soportados por codigo y tests quedan alineados a `qa`, `hml` y `prd`.
- Se actualizo `.env.homologacion` para que su valor interno use `ENVIRONMENT=hml`, sin renombrar el archivo.
- Se ajustaron entrypoint y Sentry para que `hml` use el mismo perfil endurecido que antes se asociaba a homologacion.

## Decision principal

Se estandarizo el valor de la variable `ENVIRONMENT` sin renombrar convenciones historicas del repo, como archivos, docs narrativas o comentarios existentes.

La meta es evitar que el entorno quede partido entre dos nombres validos para el mismo runtime.

## Impacto operativo

- Los deploys que antes usaban `ENVIRONMENT=homologacion` deben pasar a `ENVIRONMENT=hml`.
- `hml` sigue comportandose como entorno similar a produccion para HTTPS, cookies seguras, Gunicorn y Sentry.
- Sentry pasa a identificar ese entorno como `sisoc-hml`.

## Validacion esperada

- `ENVIRONMENT=hml` activa el perfil productivo-like en `config/settings.py`.
- `docker/django/entrypoint.py` usa Gunicorn para `qa`, `hml` y `prd`.
- Las pruebas enfocadas de settings, entrypoint y Sentry deben pasar con la nueva nomenclatura.
