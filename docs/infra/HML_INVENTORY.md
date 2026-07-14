# HML - Inventario inicial de infraestructura

Estado: inventario inicial cerrado. El 2026-07-13 se aplicaron el mantenimiento
Docker, su recurrencia y el Stage 1 reversible del MySQL local. No se reiniciaron
contenedores ni se modificaron la DB remota, TLS o configuraciones criticas.

## Alcance y fuente canonica

El entorno canonico es `hml-old` (`10.80.5.47`). Los aliases AWS quedan fuera
de alcance y se conservan solo como referencia de una posible migracion.

| Item | Hallazgo |
| --- | --- |
| Host | `ldmzssies-homolo`, VMware VM |
| SO | Ubuntu 22.04.5 LTS, kernel 5.15, x86_64 |
| Usuario de auditoria | `jportilla`, miembro del grupo `docker`; preflight root ejecutado manualmente con sudo |
| Aplicacion | Django/Gunicorn y OCR en Docker Compose |
| Servicio asociado | SISOC-Mobile en un segundo stack Docker Compose |
| Proxy | NGINX con HTTP/HTTPS y certificado wildcard |
| DB canonica | MySQL separado en `10.80.5.48:3306`, schema `sisoc_local` |
| Filesystem raiz | Antes 93%/6.7 GB libres; despues 88%/12 GB libres |
| Inodos | Antes 21%; despues 17% |
| Uptime observado | 98 dias |

## Comparacion inicial con QA

| Area | QA canonico | HML canonico | Evaluacion |
| --- | --- | --- | --- |
| App host | `10.80.9.15` | `10.80.5.47` | Diferencia esperada |
| DB host | `10.80.9.18` | `10.80.5.48` | Separacion esperada y confirmada |
| Branch | `development` | `homologacion` | Esperada |
| Checkout | `/home/admin-ssies/sisoc-comedores-test/BACKOFFICE` | `/sisoc/SISOC` | Diferencia operativa a documentar |
| Web | HTTP por IP | TLS y dominio | HML tiene certificado vencido |
| Servicios Compose | Django + OCR | Django + OCR + frontend movil separado | HML tiene una dependencia adicional |
| Media | 2.8 GiB / 8,336 archivos | 48 GiB / 45,303 archivos | Diferencia critica para backup/migracion |
| Disco | 93% -> 77% | 93% -> 88% | Patron comun, distinta recuperacion efectiva |
| Docker despues de limpieza | 2 imagenes activas | 15 imagenes, 3 activas | Retencion de 14 dias conservada |
| MySQL local | Inactivo/deshabilitado en Stage 1 | Inactivo/deshabilitado en Stage 1; 200 MB conservados | Mismo patron reversible; sin purge ni borrado |
| Docker/Compose | 27.3.1 / 2.29.7 | 28.0.1 / 2.33.1 | Drift de runtime; no cambiar versiones ahora |

## Servicios y procesos detectados

| Servicio | Estado | Inicio automatico | Nota |
| --- | --- | --- | --- |
| `docker` | activo | habilitado | Docker Engine 28.0.1 |
| `containerd` | activo | habilitado | Runtime de contenedores |
| `nginx` | activo | habilitado | NGINX 1.18.0 |
| `mysql` | inactivo | deshabilitado | Stage 1 aplicado; datadir y paquetes intactos hasta cerrar observacion |
| `cron` | activo | habilitado | `sisoc-deploy` tiene una tarea semanal conservadora; root pendiente |
| `actions.runner.dsocial118-SISOC.sisoc-homologacion` | activo | habilitado | Corre como `sisoc-deploy` |
| `apache2` | fallido | habilitado | No sirve la app observada; NGINX usa certificados bajo `/etc/apache2/certs` |
| `sisoc.service` | fallido | habilitado | Apunta a `/opt/ssies/SISOC-Backoffice`, path inexistente |

Tambien se observo un `docker compose logs -f` ejecutado como root desde el
2026-07-03. No se interrumpio porque su origen/uso no esta confirmado.

## Docker y mecanismos de ejecucion

Stacks activos:

| Proyecto | Config | Contenedores |
| --- | --- | --- |
| `sisoc` | `/sisoc/SISOC/docker-compose.deploy.yml` | `sisoc-django-1`, `sisoc-ocr_worker-1` |
| `sisoc-mobile` | `/sisoc/SISOC-Mobile/compose.prod.yaml` | `sisoc-mobile-frontend-1` |

- Django y OCR montan `/sisoc/SISOC` completo en `/sisoc`.
- Django publica `0.0.0.0:8001 -> 8000`.
- Mobile publica solo `127.0.0.1:8080 -> 8080` y reporta estado healthy.
- No hay volumenes Docker locales declarados/activos.
Antes de la limpieza habia 76 imagenes para 3 activas y `/var/lib/docker`
ocupaba 21 GB. Docker reportaba 18.06 GB recuperables, pero gran parte eran capas
compartidas.

La poda aprobada elimino solo imagenes/build cache sin uso de mas de 14 dias:

- `/` bajo de 93% a 88%, de 6.7 GB a 12 GB libres;
- quedaron 15 imagenes, 3 activas;
- las capas restantes se reclasificaron como 3.31 GB de imagenes y 9.467 GB de
  build cache reportado, conservados por retencion;
- 3 contenedores activos, 0 detenidos y 0 volumenes antes/despues;
- no cambiaron los IDs de imagen activos ni los commits desplegados.

No se detectaron Supervisor, PM2, Redis ni PostgreSQL en el host.

## Puertos escuchando

| Puerto | Bind | Asociacion |
| --- | --- | --- |
| 22/tcp | todas las interfaces | SSH |
| 80/tcp | `0.0.0.0` | NGINX, redireccion a HTTPS |
| 443/tcp | `0.0.0.0` | NGINX TLS |
| 8001/tcp | IPv4/IPv6 todas las interfaces | Django/Gunicorn via Docker |
| 8080/tcp | `127.0.0.1` | SISOC-Mobile via Docker |
| 3306/tcp | sin listener despues de Stage 1 | MySQL local heredado detenido |
| 33060/tcp | sin listener despues de Stage 1 | MySQL X Protocol local detenido |
| 10000/tcp+udp | todas las interfaces | Proceso/agente no confirmado |
| 10050/tcp | IPv4/IPv6 todas las interfaces | Proceso/agente no confirmado |

No habia conexiones establecidas al listener local 3306 en la muestra tomada.
Esto no alcanza para concluir que la instancia local no tenga dependencias.

## Paths, repositorios y estado Git

| Path | Uso/estado |
| --- | --- |
| `/sisoc/SISOC` | Checkout activo backend, owner `sisoc-deploy`, modo 2775 |
| `/sisoc/SISOC/.env` | Config real, owner `sisoc-deploy:docker`, modo 640 |
| `/sisoc/SISOC/media` | 48 GiB, 45,303 archivos; dato critico no regenerable |
| `/sisoc/SISOC/static_root` | 27 MiB; regenerable por `collectstatic` |
| `/sisoc/SISOC/logs` | 101 MiB |
| `/sisoc/SISOC-Mobile` | Checkout activo frontend movil |
| `/sisoc/SISOC-Mobile/.env` | Config no trackeada, root:root, modo 644 |
| `/sisoc/logs` | 147 MiB, incluye logs NGINX |
| `/var/www/SISOC` | Checkout historico, owner `www-data`, modo 777, working tree muy sucio |
| `/opt/ssies/SISOC-Backoffice-deprecated` | Checkout historico/deprecated, sucio y con CSV no trackeados |
| `/var/lib/mysql` | Datadir local, owner `mysql:mysql`, modo 700; tamanio no verificable sin root |

Checkout backend activo:

- branch `homologacion`;
- HEAD `94965b7141bc725de9f519209820f89441e6cb2c`;
- coincide con `origin/homologacion` consultado el 2026-07-13;
- working tree limpio;
- `homologacion` y `development` divergieron: 13 commits exclusivos de HML y 5
  exclusivos de development. No corresponde hacer pull/merge como parte de la
  auditoria.

Checkout mobile activo:

- repo `dsocial118/SISOC-Mobile`, branch `main`;
- HEAD `1765b9b2a7dbcb0a6542182167a117b5e4b10199`;
- limpio salvo `.env` no trackeado, esperado como configuracion local.

Los checkouts historicos no aparecen como fuentes del runtime activo. No se
inspeccionaron, movieron ni borraron sus cambios.

## NGINX, dominios y TLS

Configuracion activa: `/etc/nginx/sites-enabled/sisoc` ->
`/etc/nginx/sites-available/sisoc`.

- `com.hml-sisoc.secretarianaf.gob.ar` redirige al dominio canonico.
- `hml-sisoc.secretarianaf.gob.ar` redirige HTTP a HTTPS.
- `/static/` y `/media/` se sirven desde `/sisoc/SISOC`.
- `/mobile/` se proxy a `127.0.0.1:8080`.
- `/` se proxy a `localhost:8001`.
- `client_max_body_size 500M`.
- El certificado wildcard vence/vencio el 2026-03-06. Una llamada HTTPS normal
  falla con `curl` codigo 60; usando validacion deshabilitada, `/`, `/health/` y
  `/mobile/` responden HTTP 200.
- NGINX usa certificado y key bajo `/etc/apache2/certs/`.
- Las tres copias leaf/fullchain disponibles tienen el mismo serial, fingerprint,
  public key y vencimiento; no existe un candidato valido local.
- La key activa coincide con el certificado mediante hash de su parte publica.
- El unico certificado vigente encontrado es un intermedio COMODO, que no puede
  reemplazar al wildcard leaf.
- Certbot apt y snap tienen timers activos, pero no existen archivos `renewal` ni
  directorios `live`; no administran el certificado Sectigo usado por NGINX.

No se ejecuto `nginx -t`, no se renovo el certificado y no se recargo NGINX.

## Base de datos

La identidad fue confirmada con una consulta SQL de solo metadatos desde Django:

- configurado `10.80.5.48:3306` por TCP;
- servidor real `ldmzsql-homolo`;
- schema `sisoc_local`;
- conectividad TCP confirmada desde HML.

El `.env` contiene un comentario inline que llama PRD a esa direccion, aunque la
IP coincide con la DB HML canonica confirmada por el responsable. Es un comentario
operativo confuso; no se edito.

MySQL local antes de Stage 1:

- servicio activo y habilitado desde 2026-06-23;
- listener en `0.0.0.0:3306`;
- `bind-address=0.0.0.0`;
- datadir `/var/lib/mysql` de 200 MB;
- UUID propio `39c3f26e-78f1-11f0-8e8b-005056a21960`;
- sin schemas de aplicacion;
- unica conexion: daemon interno `event_scheduler`, sin clientes reales;
- cero eventos habilitados, canales de replica o miembros Group Replication;
- sin referencias en systemd/cron detectadas por el preflight.

Stage 1 fue aplicado el 2026-07-13:

- backup root-only:
  `/var/backups/sisoc/mysql-local-retirement/hml/20260713_135622`;
- `mysql.service` quedo inactivo y deshabilitado;
- no quedo listener local en 3306;
- Django siguio conectado a `10.80.5.48`, servidor `ldmzsql-homolo`, schema
  `sisoc_local`;
- backend, OCR y mobile siguieron activos y el health funcional paso;
- `/var/lib/mysql` y paquetes quedaron intactos para rollback;
- no se considera purge antes del 2026-07-20 ni sin una aprobacion separada.

Stage 1 no recupera espacio material: el datadir conservado ocupa solo 200 MB.

## Variables/configuracion sin secretos

Se relevaron solo nombres de variables y routing no sensible. Existen familias
para Django, DB, GESTIONAR, RENAPER, Sentry, email, CSP y workers. No se imprimio
ninguna credencial.

La configuracion confirma:

- `ENVIRONMENT=homologacion`;
- DB en `10.80.5.48:3306`, schema `sisoc_local`;
- Django no debug;
- dominio `https://hml-sisoc.secretarianaf.gob.ar/`;
- `WAIT_FOR_DB=false`.

## Runtimes detectados

| Componente | Version |
| --- | --- |
| Python host | 3.10.12 |
| Docker Engine | 28.0.1 |
| Docker Compose | 2.33.1 |
| MySQL server/client | 8.0.46 |
| NGINX | 1.18.0 |
| Apache | 2.4.52, servicio fallido |
| Node/npm/yarn/pnpm host | no detectados |
| Redis/PostgreSQL client | no detectados |

Las versiones dentro de las imagenes no fueron modificadas ni inventariadas en
detalle. No se instalaron ni actualizaron paquetes.

## Deploy actual inferido y confirmado

1. Un push a `homologacion` dispara `.github/workflows/deploy.yml`.
2. El job usa el runner self-hosted `sisoc-homologacion`.
3. GitHub Environment `homologacion` aporta `APP_ROOT`.
4. `scripts/operacion/deploy_refresh.sh --yes` actualiza el checkout y reconstruye
   el stack backend.
5. El entrypoint comparte el mismo riesgo QA: arranca con migraciones y otros
   comandos que escriben DB.

El frontend movil corre en un stack y repo separados. El workflow HML invoca
`deploy_refresh.sh --with-mobile --mobile-dir /sisoc/SISOC-Mobile`; el rollback
especifico del repo mobile todavia no fue probado en esta auditoria.

## Cron, logs y scripts

- Crontab de `jportilla`: vacio o no legible.
- Crontab de root y de `sisoc-deploy`: no verificados.
- Contrato versionado: `/sisoc/SISOC/scripts/crontab`, no asumido como instalado.
- Script de deploy versionado: `scripts/operacion/deploy_refresh.sh`.
- `backup_hml_configs.sh`, `show_hml_status.sh`, `healthcheck_hml.sh` y
  `cleanup_hml_disk.sh` estan instalados bajo `/home/sisoc-deploy/bin`, owner
  `sisoc-deploy:sisoc-deploy`, modo 750.
- Status, health, backup y limpieza manual fueron validados.
- Backup: `/home/jportilla/backups/infra/hml/20260713_132045`, con checksums,
  directorios 700, archivos 600, sin valores `.env` ni clave TLS privada.
- Cron instalado de forma idempotente para `sisoc-deploy`, domingo 03:20; solo
  actua con `/` al 80% o mas, conserva 14 dias y nunca poda volumenes.
- Backup previo al cron/scripts:
  `/home/sisoc-deploy/backups/infra/hml/cron-install-20260713_133809`.
- Logs backend: `/sisoc/SISOC/logs`.
- Logs NGINX: `/sisoc/logs/nginx` segun configuracion.

No se leyo contenido de logs para evitar exponer PII, URLs, tokens o datos
operativos.

## Dependencias externas criticas

- MySQL HML `10.80.5.48`.
- GitHub Actions y runner self-hosted.
- SISOC-Mobile.
- GESTIONAR y RENAPER.
- Sentry, correo, CSP y otros endpoints configurados.
- DNS/TLS para `hml-sisoc.secretarianaf.gob.ar`.
- Agentes desconocidos asociados a 10000/10050.

## Comandos ejecutados

Auditoria/verificacion de solo lectura:

- SSH: `ssh -G`, conexion batch y comandos remotos acotados;
- host: `hostnamectl`, `uname`, `id`, `uptime`, `df`, `stat`, `du`, `find`;
- servicios: `systemctl is-active/is-enabled/show/list-unit-files/list-timers`;
- procesos/red: `ps`, `ss`;
- Git: branch, HEAD, log, status y remotes sanitizados, sin fetch remoto en HML;
- Docker: `ps`, `compose ls/ps/config --services`, `inspect` sin environment,
  `system df`, `builder du`, listado de imagenes;
- web/TLS: `curl`, `openssl x509` sobre certificado publico, lectura de
  directivas NGINX seleccionadas;
- DB: conectividad TCP, consulta de identidad/metadatos desde Django y preflight
  root local con `audit_hml_root_readonly.sh`;
- archivos: metadata, tamanios, conteos y nombres de variables sin valores
  sensibles.

Mutaciones aprobadas:

- creacion de backup fuera del repo con `backup_hml_configs.sh`;
- `docker image prune -af --filter until=336h`;
- `docker builder prune -af --filter until=336h`.
- instalacion aprobada de scripts en `/home/sisoc-deploy/bin` y una entrada cron
  semanal, preservando el crontab anterior.
- backup root-only y stop/disable del MySQL local mediante
  `retire_hml_local_mysql_stage1.sh`; datadir y paquetes intactos.

No se ejecutaron otros cambios operativos.

## No verificado

1. Backup, retencion y ultimo restore probado de `10.80.5.48`.
2. Backup y consistencia de los 48 GiB de media.
3. Crontab de root.
4. Firewall/ACL efectivos y responsables de 10000/10050.
5. Flujo de deploy/rollback de SISOC-Mobile.
6. Responsable/fuente externa del wildcard Sectigo renovado.
7. Necesidad real de Apache, `sisoc.service` y los checkouts historicos.
