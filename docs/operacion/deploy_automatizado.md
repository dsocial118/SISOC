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
3. verifica que `origin/<branch>` siga siendo el SHA exacto que disparó el
   workflow, antes de bajar Docker;
4. registra `git rev-parse HEAD` como referencia previa de rollback y ejecuta
   `deploy_refresh.sh --expected-revision <SHA>`;
5. prueba `migrate --check`, el healthcheck específico del entorno y registra
   el SHA realmente desplegado en el summary del job.

El script existente conserva las validaciones operativas: lee `ENVIRONMENT`
desde `.env`, valida branch esperada, ejecuta `docker compose config -q`, baja
el stack sin volumenes, hace `git fetch` y un `merge --ff-only` de la referencia
ya verificada, y levanta con `up -d --build`.
Cuando incluye SISOC-Mobile, valida que `origin` sea el repositorio publico
esperado y normaliza las variantes SSH conocidas a HTTPS antes del downtime.

## Plan A: `main` como subconjunto comun

`.github/workflows/sync-main-downstream.yml` mantiene automaticamente este
invariante:

- `development` contiene todo `main` y puede tener extras de QA;
- `homologacion` contiene todo `main` y puede tener extras de HML;
- `main` no recibe los extras de esas ramas por este mecanismo.

Ante cada push a `main`, y también como reconciliación horaria, el workflow abre
o reutiliza PRs `main -> development` y `main -> homologacion`, y habilita
auto-merge nativo. GitHub los integra únicamente cuando los checks requeridos
por la ruleset están verdes y no hay conflictos. El push resultante activa un
único deploy de la rama actualizada; no se hace un dispatch adicional.

Un conflicto deja el PR abierto, falla el job y no despliega ese entorno. No se
usan force push, rebase automático ni resolución automática de conflictos. Las
mutaciones de PR se autentican con el token técnico acotado que se documenta
más abajo, nunca con un PAT personal ni con un merge directo.

## Promoción semanal `development -> main`

La tarea de Codex se ejecuta los miércoles a las 16:30 y no espera a que CI
termine. Crea o reutiliza un PR final exacto `development -> main` en draft, y
un PR temporal `codex/predeploy-dev-main-AAAAMMDD -> development` solo si hay
saneamiento versionable. Ambos PRs incluyen metadata y evidencia para generar
los artefactos spec-as-source desde el diff real.

El PR temporal se arma con auto-merge nativo y GitHub lo integra cuando sus
checks requeridos terminan. `.github/workflows/release-orchestrator.yml`
continúa por eventos: deja listo el PR final, crea el check pendiente
`release_baseline` y habilita su auto-merge. Cuando los otros checks están
verdes y `development` contiene el `main` más reciente, crea el tag anotado
`AAAA.MM.DD-stable` apuntando al `main` que se reemplaza, publica su release de
baseline y recién entonces completa `release_baseline`. El tag no se
sobreescribe: si el nombre ya apunta a otro SHA, el workflow se bloquea para
conservar un rollback inequívoco.

El body del PR final también fija el SHA de `development` analizado. Un push
posterior no se promueve por accidente: deja el PR bloqueado hasta que la tarea
programada vuelva a analizar y actualizar el snapshot.

El PR final no produce un deploy automático sin intervención: el job de
`production` queda sujeto a Required reviewers del Environment. Si `main`
avanzó antes de esa aprobación, el job obsoleto se omite y se debe aprobar el
job del SHA actual.

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

En `production`, configurar Required reviewers. Esa regla materializa la
aprobación manual antes de que el job de producción corra en el runner
self-hosted.

Mantener una ruleset base para `development`, `homologacion` y `main` con
`deploy_guard`, `architecture_imports`, `gitleaks` y `sync_pr_artifacts`; y
una ruleset exclusiva para `main` que suma `release_baseline`, cuya fuente debe
ser la GitHub App `SISOC Release Automation`. En ambas,
exigir que la rama esté al día y dejar el conteo de aprobaciones en cero para
estos flujos. Habilitar Auto-merge en el repositorio. Estas opciones requieren
rol de administrador y complementan, no sustituyen, los gates versionados.

Crear una GitHub App privada de servicio, instalada solamente en
`dsocial118/SISOC`, sin webhooks. Debe recibir permisos de repositorio en
escritura para `Contents`, `Pull requests`, `Checks` e `Issues` (`Metadata` es
lectura implícita); no necesita permisos de `Actions`. En **Settings → Secrets
and variables → Actions**, crear:

```text
Variable: RELEASE_AUTOMATION_APP_CLIENT_ID=<Client ID de la GitHub App>
Secret:   RELEASE_AUTOMATION_APP_PRIVATE_KEY=<PEM de una private key vigente>
```

Los workflows generan un installation token temporal, restringido al repositorio
actual, con `actions/create-github-app-token@v3`. No usar un PAT personal ni el
`GITHUB_TOKEN`: este último no dispara los workflows posteriores y un PAT no
puede emitir los check-runs requeridos por `release_baseline`. El workflow falla
con `SETUP_BLOCKED` hasta que existan la variable y el secreto.

Los workflows habilitan el auto-merge nativo; no hacen merge directo ni
despachan el deploy de forma explícita.

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
| Falla `merge --ff-only` o SHA esperado | El checkout o la rama avanzaron fuera del evento | No se bajó Docker; revisar el SHA vigente y reintentar desde el job actual |
| Falla `Origin inesperado para SISOC-Mobile` | El checkout apunta a otro repositorio | Verificar el remote; no forzar el deploy ni aceptar una URL no documentada |
| PR descendente queda abierto | Hay conflicto o GitHub rechazo el merge | Resolver por PR en la rama afectada; el deploy queda correctamente bloqueado |
| Tag estable bloqueado | Ya existe `AAAA.MM.DD-stable` con otro SHA | No sobrescribirlo; decidir explícitamente el tag/baseline antes de promover |
| Falla Docker | Usuario sin grupo `docker` o daemon detenido | Revisar `id`, `systemctl status docker` y `docker compose version` |
