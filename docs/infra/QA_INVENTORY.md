# QA - Inventario inicial de infraestructura

Estado: Fases 1 a 4 completadas el 2026-07-13 y retiro Stage 2 del MySQL local
aplicado el 2026-07-21. La auditoria inicial fue solo lectura; luego se
aplicaron el mantenimiento de disco, su cron, el Stage 1 reversible y el
retiro irreversible aprobado. No se reinicio la aplicacion, no se editaron
configuraciones criticas, no se ejecutaron deploys/migraciones ni se imprimieron
secretos.

## Alcance y nivel de certeza

El usuario confirmo que los aliases terminados en `-old` son los entornos
canonicos actuales. AWS queda fuera de alcance y se conserva solo como referencia
de una migracion futura:

| Huella | Estado de auditoria | Evidencia |
| --- | --- | --- |
| `qa-old` (`10.80.9.15`) | Canonico y auditado por SSH | Tiene el runner `sisoc-qa`, el checkout en `development` y la aplicacion respondiendo 200. |
| `qa-site-aws` (`10.1.131.121`) | Fuera de alcance | Referencia de migracion; no auditar ni modificar en esta etapa. |
| `qa-db-aws` (`10.1.130.88`) | Fuera de alcance | Referencia de migracion; no auditar ni modificar en esta etapa. |

Este documento describe el QA canonico `qa-old`. No autoriza apagarlo ni hacer
cutover hacia AWS.

## Resumen del entorno accesible

| Item | Hallazgo |
| --- | --- |
| Host | `mdsldmz-ssies-test`, VMware VM |
| Alias SSH | `qa-old` |
| SO | Ubuntu 22.04.5 LTS, kernel 5.15, x86_64 |
| Uptime observado | 172 dias |
| Usuarios de auditoria | `jportilla` para host y `sisoc-deploy` temporalmente para Docker/config operativa |
| Usuario operativo | `sisoc-deploy`, miembro del grupo `docker` |
| Aplicacion | Django/Gunicorn en Docker Compose, NGINX como reverse proxy |
| URL comprobada | `http://10.80.9.15/` |
| Health comprobado | `http://127.0.0.1/health/`, HTTP 200 |
| Filesystem raiz | Antes: 93%, 7.2 GiB libres. Tras Stage 2: 34%, 62 GB libres |
| Inodos | 7% usados al cierre; el riesgo era capacidad, no inodos |
| TLS | No detectado en esta huella; NGINX escucha HTTP/80 |

## Servicios y procesos detectados

| Servicio | Estado | Inicio automatico | Nota |
| --- | --- | --- | --- |
| `docker` | activo | habilitado | Docker Engine 27.3.1 |
| `containerd` | activo | habilitado | Runtime de contenedores |
| `nginx` | activo | habilitado | NGINX 1.18.0 |
| MySQL server local | no instalado | no aplica | Stage 2 retiro unidad, paquetes y datadir; no hay rollback local |
| `cron` | activo | habilitado | `sisoc-deploy` tiene una tarea semanal de mantenimiento Docker; cron de root no auditado |
| `actions.runner.dsocial118-SISOC.sisoc-qa` | activo | habilitado | Corre como `sisoc-deploy` desde `/home/sisoc-deploy/actions-runner/` |
| `apache2` | fallido | habilitado | Apache esta instalado pero no sirve la app observada |

Se observaron dos cgroups de contenedor. Los procesos son consistentes con los
dos servicios declarados en Compose:

- `django`: Python + Gunicorn, publicado como `0.0.0.0:8001 -> 8000`.
- `ocr_worker`: proceso Python sin puerto publicado.

No se detectaron Supervisor, PM2, Celery, Redis ni PostgreSQL en la revision
acotada. Con `sisoc-deploy` se confirmaron dos contenedores activos,
`backoffice-django-1` y `backoffice-ocr_worker-1`, sin volumenes Docker locales.

## Puertos escuchando

| Puerto | Bind observado | Asociacion |
| --- | --- | --- |
| 22/tcp | `0.0.0.0` y `::` | SSH |
| 80/tcp | `0.0.0.0` | NGINX |
| 8001/tcp | `0.0.0.0` y `::` | `docker-proxy`, Django/Gunicorn por contrato Compose |
| 3306/tcp | sin listener | MySQL local retirado; DB remota en `10.80.9.18:3306` |
| 33060/tcp | sin listener | MySQL X Protocol local retirado |
| 10000/tcp y udp | `0.0.0.0` | Proceso no confirmado con los permisos actuales |
| 10050/tcp | `0.0.0.0` y `::` | Proceso no confirmado con los permisos actuales |

El estado efectivo de firewall no pudo verificarse. El archivo de UFW indica
`ENABLED=yes`, pero la unidad `ufw` esta inactiva y enmascarada. Se requieren
reglas de red/ACL externas para evaluar la exposicion real.

## Paths importantes

| Path | Uso | Estado observado |
| --- | --- | --- |
| `/home/admin-ssies/sisoc-comedores-test/BACKOFFICE` | Checkout y bind mount de la aplicacion | `sisoc-deploy:sisoc-deploy`, modo 755 |
| `/home/admin-ssies/sisoc-comedores-test/BACKOFFICE/.env` | Configuracion real | modo 600; solo se relevaron claves de routing no secretas |
| `/home/admin-ssies/sisoc-comedores-test/BACKOFFICE/media` | Uploads/media | 2.8 GiB, 8.336 archivos |
| `/home/admin-ssies/sisoc-comedores-test/BACKOFFICE/static` | Estaticos fuente | 11 MiB, 364 archivos |
| `/home/admin-ssies/sisoc-comedores-test/BACKOFFICE/static_root` | Estaticos recolectados | 27 MiB, 807 archivos; se regenera al iniciar web |
| `/home/admin-ssies/sisoc-comedores-test/BACKOFFICE/logs` | Logs Django por fecha/nivel | 3.7 MiB, 350 archivos |
| `/var/log/nginx/` | Logs de NGINX | archivos `staging-sisoc-*` con rotacion |
| `/etc/nginx/sites-available/staging.conf` | Virtual host observado | root:root, modo 644 |
| `/home/sisoc-deploy/actions-runner/` | GitHub Actions runner | servicio systemd activo |
| `/home/sisoc-deploy/bin/` | Scripts operativos instalados | owner `sisoc-deploy`, scripts modo 750 |
| `/home/sisoc-deploy/backups/infra/qa/` | Backups de configuracion fuera del repo | directorios 700, archivos 600 |
| `/var/lib/mysql` | Datadir del clon MySQL local heredado | Eliminado en Stage 2 el 2026-07-21 |
| `/var/lib/docker` | Datos Docker | contenido no legible sin privilegios |

Existian dos dumps SQL antiguos y grandes fuera del checkout:

- `/home/admin-ssies/dumps/15-07-2025.sql`: aproximadamente 2.4 GB, modo 664.
- `/home/admin-ssies/sisoc_local.sql`: aproximadamente 5.1 GB, modo 664.

No se leyo su contenido ni se valido si eran utilizables como backup. El usuario
autorizo explicitamente su eliminacion el 2026-07-13. Se borraron solo esos dos
paths y se verifico su ausencia; el uso de `/` bajo de 85% a 77%.

No se encontraron virtualenvs, `node_modules` ni builds Node dentro del checkout.
Si existen fuera del path inspeccionado, quedan pendientes.

## Repositorio Git

| Item | Valor observado |
| --- | --- |
| Repo | `https://github.com/dsocial118/SISOC.git` |
| Branch | `development` |
| HEAD | `7e5cb3052d02614258f185982c23196596368093` |
| Commit | `Merge pull request #2031 from dsocial118/HotfixVAt` |
| Tracking | `origin/development`, sin ahead/behind informado |
| Working tree | Un archivo no trackeado cuyo nombre son cuatro caracteres ESC |

El archivo no trackeado ya habia sido observado en una operacion anterior. No se
inspecciono, movio ni borro.

## Configuracion web server

Configuracion detectada en `/etc/nginx/sites-enabled/staging.conf`:

- `listen 80 default_server`.
- `client_max_body_size 500M`.
- `/static/` usa alias a `static_root/`.
- `/media/` usa alias a `media/`.
- `/` hace proxy a `http://localhost:8001`.
- logs dedicados `staging-sisoc-access.log` y `staging-sisoc-error.log`.
- no se detecto `server_name` efectivo ni configuracion TLS en el archivo.

No se pudo ejecutar `nginx -T` con privilegios. Lo anterior describe los archivos
habilitados, no garantiza que el proceso haya recargado exactamente ese contenido.
Apache 2.4.52 esta instalado y habilitado, pero la unidad esta fallida.

## Configuracion de procesos y runtimes

| Componente | Version/contrato |
| --- | --- |
| Python host | 3.10.12 |
| Imagen Python declarada | `python:3.11.15-slim-bookworm`; runtime de contenedor no verificado directamente |
| Docker Engine | 27.3.1 |
| Docker Compose | 2.29.7 |
| MySQL server local | Retirado en Stage 2; sin unidad ni binario `mysqld` |
| NGINX | 1.18.0 |
| Apache | 2.4.52, unidad fallida |
| Certbot | comando 5.6.0; tambien existe paquete apt 1.21 y timer snap |
| Node/npm/yarn/pnpm | no detectados en el host |
| Redis/PostgreSQL client | no detectados en el host |

El Compose de deploy monta todo el checkout en `/sisoc/`, carga `.env` y define
`restart: unless-stopped`. No hay volumen Docker declarado para media porque los
archivos persisten en el bind mount del host.

Docker antes del mantenimiento tenia 28 imagenes para 2 activas y 10.96 GB
reportados como recuperables. Despues de podar imagenes y build cache sin uso con
mas de 14 dias quedaron 2 imagenes activas, 0 volumenes y 1.79 GB de build cache
reciente/compartido. El filesystem bajo de 93% a 85%; la eliminacion posterior y
aprobada de los dos dumps antiguos lo dejo en 77%.

El entrypoint web realiza, en cada arranque:

1. espera de MySQL;
2. ajuste de historial de migraciones;
3. `migrate auth` y `migrate --noinput`;
4. `load_fixtures`, `create_test_users` y `create_groups`;
5. borrado de `static_root` y `collectstatic`;
6. inicio de Gunicorn.

`makemigrations` queda desactivado por defecto fuera de desarrollo, pero las
migraciones y otros comandos con escritura de DB no quedan desactivados.

## Variables y archivos de configuracion, sin secretos

- `.env` real: existe, owner `sisoc-deploy`, modo 600, 5.646 bytes, ultima
  modificacion observada 2026-04-27. Se consultaron solo claves de routing sin
  imprimir credenciales: `ENVIRONMENT=qa`, DB en `10.80.9.18:3306`, schema
  `sisoc_local`, `WAIT_FOR_DB=false` y logs relativos bajo `logs/`.
- `.env.example`, `.env.qa`, `.env.homologacion` y `.env.prod` estan trackeados.
  Sus valores no fueron inspeccionados durante esta auditoria.
- Familias de configuracion versionadas: Django/host/origins, MySQL, Gunicorn,
  GESTIONAR, RENAPER, Google Maps, Sentry, email SMTP, web push, Ticketera, OCR,
  logs y workers.

## Logs, static, media y uploads

- Django escribe bajo `logs/<fecha>/{info,error,warning,critical,data}.log`.
- Los logs mas recientes observados son del 2026-07-12.
- Parte de los logs recientes pertenece a `root:root` y parte a
  `sisoc-deploy:sisoc-deploy`, consistente con escritura desde contenedores que
  corren como root sobre un bind mount.
- NGINX tiene logs generales y `staging-sisoc-*` rotados.
- No se leyo contenido de logs para evitar exponer PII, tokens o URLs sensibles.
- `media/` es el principal conjunto de archivos que debe preservarse en una
  migracion; `static_root/` es regenerable.

## Base de datos

Confirmado en `qa-old`:

- Stage 2 retiro `mysql-server`, `mysql-server-8.0` y
  `mysql-server-core-8.0`, sin `autoremove`.
- no queda unidad MySQL local, binario `mysqld`, proceso ni listener local
  3306/33060.
- `/var/lib/mysql` fue eliminado; el uso de `/` bajo de 80% a 34%, con
  62 GB libres.
- Django no apunta al MySQL local: su configuracion usa `10.80.9.18:3306` y el
  schema `sisoc_local`.
- El responsable confirmo que todos los entornos usan DB separada: QA
  `10.80.9.18`, HML `10.80.5.48` y PRD `10.80.5.46`.
- `10.80.9.18:3306` es alcanzable desde el host QA.
- Tres muestras no mostraron conexiones establecidas al puerto local 3306.
- El preflight previo a Stage 1 confirmo cero clientes inesperados, eventos,
  replicas o miembros de Group Replication. La conexion inicial era interna.
- Backup Stage 1 root-only conservado:
  `/var/backups/sisoc/mysql-local-retirement/20260713_115645`. Contiene
  metadatos, no una copia recuperable de los 43 GB eliminados.

No confirmado:

- tamanio, retencion y estrategia de backup de la DB remota `10.80.9.18`;
- ultimo backup valido y ultimo restore probado.

Solo se ejecutaron consultas SQL de identidad y metadatos para validar routing,
conexiones, eventos y replicacion. No se consultaron datos de negocio ni se
leyeron credenciales.

## Scripts existentes y flujo de deploy inferido

Artefactos principales:

- `.github/workflows/deploy.yml`.
- `scripts/operacion/deploy_refresh.sh`.
- `docker-compose.deploy.yml`.
- `docker/django/entrypoint.py`.
- `scripts/crontab` como contrato versionado, no como prueba de instalacion.

Flujo actual confirmado por codigo y runner activo:

1. push a `development` dispara el job `deploy-qa` en runner `sisoc-qa`;
2. GitHub Environment `qa` aporta `APP_ROOT`;
3. el runner registra el commit previo;
4. `deploy_refresh.sh` valida `.env`, entorno, branch y Compose;
5. ejecuta `git fetch`, `docker compose config -q`, `docker compose down`,
   `git pull --ff-only`, `docker compose up -d --build` y `ps`;
6. el entrypoint web ejecuta migraciones, fixtures, usuarios/grupos y
   `collectstatic` antes de Gunicorn.

El deploy es automatizado; `docs/operacion/infraestructura.md` todavia lo describe
como manual y necesita reconciliacion documental.

## Cron jobs

El crontab de `sisoc-deploy` estaba vacio. Tras backup y aprobacion se instalo una
unica tarea, domingo 03:00:

```cron
0 3 * * 0 /home/sisoc-deploy/bin/cleanup_qa_disk.sh --apply --yes >/dev/null 2>&1
```

Valida host/entorno, solo actua con `/` al 80% o mas, conserva 14 dias y no poda
volumenes. Los eventos van al journal con tag `sisoc-qa-disk-cleanup`. El crontab
de root no fue auditado.

El archivo historico `scripts/crontab` no coincide con la instalacion real:

- limpieza diaria de logs;
- `docker system prune` semanal;
- agente de monitoreo cada cinco minutos;
- purga diaria de auditlog mayor a 180 dias.

Sus paths no existen en el QA canonico y su prune incluye `--volumes`; no debe
instalarse tal como esta.

## SSL, dominios y monitoreo

- QA viejo responde por IP y HTTP.
- No hay directorios bajo `/etc/letsencrypt/live`.
- Existe Certbot por mas de un mecanismo de paquete/timer; no se determino cual es
  autoritativo.
- Los listeners 10000/10050 y su relacion con monitoreo quedan sin confirmar.
- La documentacion declara el QA AWS tambien por HTTP, sin dominio publico.

## Dependencias externas criticas

Detectadas por configuracion/codigo versionado, no validadas con llamadas reales:

- GESTIONAR.
- RENAPER.
- Google Maps.
- Sentry.
- correo SMTP.
- web push.
- Ticketera, cuando esta habilitada.
- GitHub Actions/GitHub para deploy.
- SISOC Mobile segun entorno/flujo.

## Archivos y datos a considerar en una migracion

- repo Git en el commit/branch correcto;
- `.env` recreado por canal seguro;
- `media/` completo;
- base MySQL real, una vez identificada y respaldada consistentemente;
- NGINX y configuracion de red/firewall;
- definicion/registro del runner, sin copiar tokens del runner viejo;
- cron efectivo, no solo `scripts/crontab`;
- logs solo si existe necesidad legal u operativa;
- no depender de dumps locales antiguos; los dos detectados fueron eliminados con
  aprobacion y no eran backups validados.

## Comandos utiles de diagnostico

Ejecutar con un usuario de solo lectura que tenga visibilidad sobre Docker y
servicios, sin imprimir `.env`:

```bash
hostnamectl
id
df -hT /
df -ih /
systemctl is-active docker nginx mysql cron actions.runner.dsocial118-SISOC.sisoc-qa
git -C /home/admin-ssies/sisoc-comedores-test/BACKOFFICE status --short --branch
docker compose -f /home/admin-ssies/sisoc-comedores-test/BACKOFFICE/docker-compose.deploy.yml ps
ss -lntup
nginx -T
curl --max-time 8 -fsS http://127.0.0.1/health/
```

`nginx -T` y reglas de firewall requieren permisos que no estuvieron disponibles.
Las consultas Docker deben ejecutarse como `sisoc-deploy`.

## Comandos ejecutados durante esta auditoria

Se usaron consultas de estas familias, todas sin mutacion remota:

- conectividad: `ssh ... true`, directa y con `ProxyJump`;
- red local: `route print`, `Get-NetRoute`, `Get-NetAdapter`;
- identidad/SO: `date`, `hostnamectl`, `uname`, `/etc/os-release`, `id`,
  `groups`, `umask`, `uptime`;
- capacidad: `df`, `findmnt`, `stat`, `du`, `find`;
- Git: `branch --show-current`, `rev-parse`, `log`, `status`, `remote get-url`,
  `ls-files`, `sha256sum` con `GIT_OPTIONAL_LOCKS=0`;
- procesos: `systemctl list-units`, `is-active`, `is-enabled`, `show`, `status`,
  `ps`, lectura de cgroups;
- Docker: `version`, `compose version`, `ps`, `compose ls`, `inspect`, `images`,
  `volume ls`, `system df`, `builder du` y podas aprobadas;
- red/web: `ss`, lectura acotada de directivas NGINX/MySQL, `curl` a `/` y
  `/health/`;
- runtimes: comandos `--version` y `dpkg-query` acotado;
- logs/backups/config: solo paths, metadata, tamanios y owners;
- cron/firewall: crontab del usuario, contrato versionado y metadata UFW.

Las escrituras aprobadas fueron: backup fuera del repo, scripts bajo
`/home/sisoc-deploy/bin`, poda conservadora de imagenes/build cache sin uso y una
tarea cron de `sisoc-deploy`. El checkout remoto no fue modificado.

## Dudas e informacion no confirmada

1. Estado, tamanio y backup/restore de la DB autoritativa en `10.80.9.18`.
2. Destino de conservacion o autorizacion de borrado para los 43 GB locales
   despues del 2026-07-20.
3. Reglas efectivas de firewall/ACL y responsables de los puertos 10000/10050.
4. Crontab efectivo de root.
5. Backup de datos vigente, retencion y ultimo restore probado.
6. Configuracion efectiva cargada por NGINX (`nginx -T`) y logs actuales con root.
