# Deploy automatizado con self-hosted runners

Fecha: 2026-07-08

## Cambio

Se agrego un workflow de GitHub Actions para desplegar automaticamente QA, homologacion y produccion desde runners self-hosted instalados en cada servidor de aplicacion.

El flujo queda atado a las branches operativas:

- `development` despliega `qa`;
- `homologacion` despliega `homologacion`;
- `main` despliega `production`.

Cada job corre con labels estaticos del entorno y delega en `scripts/operacion/deploy_refresh.sh --yes` dentro del checkout local del servidor.

## Decision

No se usa `actions/checkout` porque el deploy debe operar sobre el checkout provisionado del servidor, con su `.env`, deploy key y permisos locales.

`APP_ROOT` se resuelve desde una variable del GitHub Environment para no fijar una ruta unica de servidor. Si no existe, el workflow falla antes de ejecutar el deploy.

La aprobacion manual de produccion se traslada a GitHub Environments mediante Required reviewers en `production`.

## Impacto operativo

- El deploy manual por SSH queda reemplazado por push a la branch del entorno y, en produccion, aprobacion del Environment.
- Los servidores siguen sin exponerse a runners cloud: cada runner ejecuta localmente dentro de la red/VPN existente.
- El rollback conserva el procedimiento actual: tag estable y backup de DB, con el commit previo al refresh logueado por el workflow.

## Validacion esperada

- Sintaxis YAML del workflow.
- Primer deploy controlado en `qa` validando que el runner tenga permisos Docker, acceso a `APP_ROOT`, deploy key `github-sisoc` y variable `APP_ROOT` definida.

## Riesgos

- Si el checkout local no esta en la branch esperada para el `ENVIRONMENT`, `deploy_refresh.sh` bloquea el deploy.
- Si un runner esta offline o mal etiquetado, el job queda en cola.
- Si `APP_ROOT` apunta a un checkout incorrecto, el deploy puede operar sobre otro repo; revisar la variable por Environment antes de habilitarlo.
- Si se habilitan workflows de PR sobre estos runners, codigo no confiable podria ejecutarse en servidores internos; mantenerlos exclusivos para `deploy.yml`.
