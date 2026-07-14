# Deploy automatizado con self-hosted runners

Estado: runbook operativo para automatizar el deploy de SISOC en QA, homologacion y produccion usando GitHub Actions con runners self-hosted instalados en cada servidor de aplicacion.

El workflow no usa runners cloud ni `actions/checkout`: cada runner ejecuta el script local `scripts/operacion/deploy_refresh.sh` dentro del checkout ya provisionado en el servidor.

## Flujo operativo

| Entorno | Branch | GitHub Environment | Runner labels | Variable requerida |
| --- | --- | --- | --- | --- |
| QA | `development` | `qa` | `self-hosted`, `sisoc-qa` | `APP_ROOT` |
| Homologacion | `homologacion` | `homologacion` | `self-hosted`, `sisoc-homologacion` | `APP_ROOT` |
| Produccion | `main` | `production` | `self-hosted`, `sisoc-produccion` | `APP_ROOT` |

En cada push o dispatch a la branch del entorno, GitHub agenda el job
correspondiente. El runner local:

1. resuelve `APP_ROOT` desde la variable del Environment;
2. entra al checkout provisionado en el servidor;
3. registra `git rev-parse HEAD` como referencia previa de rollback;
4. ejecuta `./scripts/operacion/deploy_refresh.sh --yes`.

El script existente conserva las validaciones operativas: lee `ENVIRONMENT`
desde `.env`, valida branch esperada, ejecuta `docker compose config -q`, baja
el stack sin volumenes, hace `git pull --ff-only` y levanta con `up -d --build`.
Cuando incluye SISOC-Mobile, valida que `origin` sea el repositorio publico
esperado y normaliza las variantes SSH conocidas a HTTPS antes del downtime.

## Plan A: `main` como subconjunto comun

`.github/workflows/sync-main-downstream.yml` mantiene automaticamente este
invariante:

- `development` contiene todo `main` y puede tener extras de QA;
- `homologacion` contiene todo `main` y puede tener extras de HML;
- `main` no recibe los extras de esas ramas por este mecanismo.

Ante cada push a `main`, y tambien como reconciliacion horaria, el workflow abre
o reutiliza PRs `main -> development` y `main -> homologacion`. Solo los integra
si GitHub confirma que no hay conflictos. Luego invoca `deploy.yml` de forma
explicita sobre la rama actualizada.

Un conflicto deja el PR abierto, falla el job y no despliega ese entorno. No se
usa force push, rebase automatico, PAT ni resolucion automatica de conflictos.

## Instalar runner por entorno

Ejecutar en el servidor de aplicacion de cada entorno con el usuario operativo del deploy, por ejemplo `sisoc-deploy`. Reemplazar `<TOKEN_REGISTRO>` por un token de registro nuevo generado en GitHub para el repositorio `dsocial118/SISOC`.

```bash
sudo -iu sisoc-deploy
mkdir -p ~/actions-runner
cd ~/actions-runner

RUNNER_VERSION=<version-vigente>
curl -o actions-runner-linux-x64.tar.gz -L \
  "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
tar xzf actions-runner-linux-x64.tar.gz

./config.sh \
  --url https://github.com/dsocial118/SISOC \
  --token <TOKEN_REGISTRO> \
  --name sisoc-<entorno> \
  --labels sisoc-<entorno> \
  --unattended
```

Usar el label final segun entorno:

| Entorno | `--name` sugerido | `--labels` |
| --- | --- | --- |
| QA | `sisoc-qa` | `sisoc-qa` |
| Homologacion | `sisoc-homologacion` | `sisoc-homologacion` |
| Produccion | `sisoc-produccion` | `sisoc-produccion` |

Instalar y arrancar como servicio:

```bash
sudo ./svc.sh install sisoc-deploy
sudo ./svc.sh start
sudo ./svc.sh status
```

## Permisos locales del runner

El usuario del runner debe tener:

- pertenencia al grupo `docker` o permisos equivalentes para ejecutar `docker compose`;
- permisos de lectura/escritura sobre `APP_ROOT`;
- acceso Git al remoto de SISOC con la deploy key `github-sisoc`;
- para SISOC-Mobile no hace falta una clave SSH: el repositorio publico usa
  `https://github.com/dsocial118/SISOC-Mobile.git`;
- `.env` real del entorno presente en `APP_ROOT` con permisos `600`;
- branch correcta para el entorno (`development`, `homologacion` o `main`).

Validacion minima en cada servidor:

```bash
id sisoc-deploy
docker compose version
git -C "$APP_ROOT" branch --show-current
git -C "$APP_ROOT" rev-parse --short HEAD
git -C "$APP_ROOT" remote -v
test -f "$APP_ROOT/.env" && ls -l "$APP_ROOT/.env"
```

## Configurar GitHub

Crear los Environments del repositorio:

- `qa`
- `homologacion`
- `production`

En cada Environment, crear la variable:

```text
APP_ROOT=<ruta-real-del-checkout>
```

No hardcodear una ruta global: los servidores existentes pueden usar rutas distintas, por ejemplo `/opt/sisoc/SISOC` o `/opt/ssies/SISOC-Backoffice`.

En `production`, configurar Required reviewers. Esa regla materializa la aprobacion manual antes de que el job de produccion corra en el runner self-hosted.

La politica de Actions del repositorio debe permitir que `GITHUB_TOKEN` cree y
fusione pull requests. El workflow solicita solo `contents: write`,
`pull-requests: write` y `actions: write`; esta ultima habilita el dispatch
explicito de `deploy.yml`.

## Seguridad

- Solo `.github/workflows/deploy.yml` debe usar estos runners self-hosted.
- No correr workflows de PR ni jobs que ejecuten codigo no confiable en los runners de deploy.
- Registrar cada runner solo en el repositorio `dsocial118/SISOC`, no a nivel organizacion, salvo decision explicita de infraestructura.
- No commitear secretos ni `.env` reales. Los `.env` viven en cada servidor con `chmod 600`.
- Rotar tokens de registro inmediatamente si se exponen durante la instalacion.
- Mantener el acceso SSH/VPN segun el modelo actual; el runner elimina la necesidad de SSH manual desde GitHub, no abre los servidores a Internet.

## Rollback

El rollback sigue el procedimiento actual documentado en `docs/operacion/infraestructura.md`, seccion 9:

- volver al ultimo tag estable o commit acordado;
- restaurar backup de DB si el cambio lo requiere;
- ejecutar el deploy operativo del entorno.

Cada ejecucion del workflow registra el commit que estaba desplegado antes del refresh (`git rev-parse HEAD`). Ese valor sirve como referencia rapida para volver al commit previo si el tag estable no alcanza o si se necesita reconstruir la secuencia del incidente.

## Fallas frecuentes

| Sintoma | Causa probable | Accion |
| --- | --- | --- |
| El job queda en cola | Runner offline o label incorrecto | Revisar `svc.sh status`, conectividad VPN/local y labels del runner |
| Falla `APP_ROOT no esta configurado` | Falta variable del Environment | Definir `APP_ROOT` en `qa`, `homologacion` o `production` |
| Falla por branch esperada | Checkout local en branch equivocada | Corregir branch en el servidor o revisar el mapping del entorno |
| Falla `git pull --ff-only` | Historial local divergio | Resolver manualmente en el servidor; no usar merge automatico en el runner |
| Falla `Origin inesperado para SISOC-Mobile` | El checkout apunta a otro repositorio | Verificar el remote; no forzar el deploy ni aceptar una URL no documentada |
| PR descendente queda abierto | Hay conflicto o GitHub rechazo el merge | Resolver por PR en la rama afectada; el deploy queda correctamente bloqueado |
| Falla Docker | Usuario sin grupo `docker` o daemon detenido | Revisar `id`, `systemctl status docker` y `docker compose version` |
