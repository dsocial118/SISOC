# Bootstrap de Compose en despliegues

## Cambio

`scripts/operacion/deploy_refresh.sh` realiza el `fast-forward` validado antes
de exigir los archivos Compose del release. Antes, un checkout de HML anterior
al release no podía desplegar una revisión que agregara un archivo Compose.

## Garantías conservadas

- Se sigue validando que el checkout esté limpio y en la rama esperada.
- Si se informa `--expected-revision`, se valida contra `origin/<branch>` antes
  de modificar el checkout y contra `HEAD` después del fast-forward.
- Docker sólo se valida, baja y levanta después de resolver los Compose de la
  revisión a desplegar.

## Cobertura

`tests/test_deploy_refresh_script.py` cubre un checkout sin
`docker-compose.celery.yml` que lo recibe durante el fast-forward.
