# Produccion - Inventario inicial de infraestructura

Estado: auditoria inicial cerrada en modo exclusivamente read-only el
2026-07-13. Luego, con aprobacion explicita, se creo una copia local de media.
No se modificaron servicios, cron, permisos existentes, Git, Docker, MySQL,
NGINX, TLS ni datos de origen.

## Alcance y fuente canonica

El entorno canonico es `prd-old` (`10.80.5.45`). Los aliases AWS quedan fuera de
alcance y se conservan solo como referencia de una posible migracion.

| Item | Hallazgo |
| --- | --- |
| Host | `mdsldmz-ssies`, VMware VM |
| SO | Ubuntu 22.04.5 LTS, kernel 5.15.0-181, x86_64 |
| Usuario de auditoria | `jportilla`, grupos `docker`, `admin-ssies` y `sisoc` |
| Aplicacion | Django/Gunicorn y cinco workers en Docker Compose |
| Frontend | SISOC-Mobile en un segundo stack Docker Compose |
| Proxy | NGINX con HTTP/HTTPS |
| DB canonica | MySQL separado en `10.80.5.46:3306`, schema `sisoc_local` |
| Filesystem raiz antes del backup local | 785 GB, 90 GB usados, 663 GB libres, 12% |
| Inodos | 2% usados |
| Uptime observado | 25 dias |

## Comparacion QA / HML / produccion

| Area | QA | HML | Produccion | Evaluacion |
| --- | --- | --- | --- | --- |
| App host | `10.80.9.15` | `10.80.5.47` | `10.80.5.45` | Separacion esperada |
| DB host | `10.80.9.18` | `10.80.5.48` | `10.80.5.46` | Separacion confirmada |
| Branch backend | `development` | `homologacion` | `main` | Esperada |
| Backend path | path historico QA | `/sisoc/SISOC` | `/sisoc/SISOC` | HML/PRD alineados |
| Containers app | 2 | 3 | 7 | PRD agrega cuatro workers especializados |
| Media | 2.8 GiB | 48 GiB | 65 GiB | Principal dato a migrar |
| Disco raiz | 77% post-limpieza | 88% post-limpieza | 12% | PRD no tiene presion de disco |
| MySQL local | Stage 1 inactivo | Stage 1 inactivo | Activo/habilitado, 200 MB | No tocar en esta fase |
| Deploy mobile | no aplica | incluido en workflow | no incluido en `main` actual | Diferencia real de ramas |

## Servicios y agentes

| Servicio | Estado | Inicio | Nota |
| --- | --- | --- | --- |
| `docker` | activo | habilitado | Docker Engine 28.0.1 |
| `containerd` | activo | habilitado | runtime de contenedores |
| `nginx` | activo | habilitado | NGINX 1.18.0 |
| `mysql` | activo | habilitado | instancia local heredada, no usada por Django observado |
| `cron` | activo | habilitado | root tiene cuatro entradas sanitizadas |
| runner `sisoc-produccion` | activo | habilitado | corre como `sisoc-deploy` |
| `zabbix-agent` | activo | habilitado | monitoreo, asociado previsiblemente a 10050 |
| `webmin` | activo | habilitado | administracion, asociado previsiblemente a 10000 |
| `apache2` | fallido | habilitado | no sirve la app; NGINX usa paths de certificados bajo `/etc/apache2` |
| `sisoc.service` | fallido | habilitado | apunta a `/opt/ssies/SISOC-Backoffice`, path inexistente |

No se detectaron Supervisor, PM2, Redis ni PostgreSQL activos/instalados. El
listener local 556 no fue clasificado.

## Docker y procesos de aplicacion

Stacks activos:

| Proyecto | Config | Servicios activos |
| --- | --- | --- |
| `sisoc` | `docker-compose.deploy.yml` + `docker-compose.produccion.yml` | Django, OCR, mailing, importacion de usuarios, importacion de ciudadanos y credenciales masivas |
| `sisoc-mobile` | `/sisoc/SISOC-Mobile/compose.prod.yaml` | frontend mobile |

Los siete contenedores estaban activos; mobile reportaba healthy. Los seis
servicios backend montan `/sisoc/SISOC` completo en `/sisoc`.

- Django publica `0.0.0.0:8001 -> 8000`.
- Mobile publica solo `127.0.0.1:8080 -> 8080`.
- Hay 32 imagenes para 7 activas: 5.062 GB, casi todo marcado recuperable.
- Build cache: 338 MB.
- Un volumen nombrado inactivo de 210 MB:
  `sisoc-mobile_frontend_node_modules`, regenerable pero no clasificado para
  borrado.
- El disco al 12% no justifica una poda manual.

Los workers `ciudadanos_import`, `bulk_credentials`, `user_import` y `mailing`
habian sido recreados cuatro horas antes de la auditoria, mientras Django/OCR y
mobile llevaban cuatro dias. No se investigo la causa porque hubiera requerido
ampliar el analisis de deploy/logs.

## Puertos escuchando

| Puerto | Bind | Asociacion |
| --- | --- | --- |
| 22/tcp | todas las interfaces | SSH |
| 80/tcp | todas las interfaces | NGINX |
| 443/tcp | todas las interfaces | NGINX TLS |
| 8001/tcp | todas las interfaces | Django/Gunicorn via Docker |
| 8080/tcp | `127.0.0.1` | SISOC-Mobile via Docker |
| 3306/tcp | todas las interfaces | MySQL local heredado |
| 33060/tcp | `127.0.0.1` | MySQL X Protocol local |
| 10000/tcp+udp | todas las interfaces | compatible con Webmin activo |
| 10050/tcp | IPv4/IPv6 | compatible con Zabbix activo |
| 556/tcp | `127.0.0.1` | no confirmado |

No habia conexiones establecidas al listener MySQL local 3306 en las muestras.

## Paths, repositorios y estado Git

| Path | Uso/estado |
| --- | --- |
| `/sisoc/SISOC` | checkout backend activo, owner `sisoc-deploy`, modo 2775 |
| `/sisoc/SISOC/.env` | configuracion real, `sisoc-deploy:sisoc-deploy`, modo 640 |
| `/sisoc/SISOC/media` | 65 GiB; 68,548 archivos al copiar; dato critico no regenerable |
| `/sisoc/backups/media/20260713_172352/media` | copia local aprobada, privada de root y en el mismo filesystem |
| `/sisoc/SISOC/static_root` | 27 MiB, 894 archivos; regenerable |
| `/sisoc/SISOC/logs` | 1.3 GiB, logs por fecha |
| `/sisoc/SISOC/tmp` | 24 KiB, tres archivos no trackeados; contenido no leido |
| `/sisoc/SISOC-Mobile` | checkout mobile activo, owner `admin-ssies:sisoc`, modo 775 |
| `/sisoc/SISOC-Mobile/.env` | configuracion local, `root:root`, modo 664 |
| `/sisoc/logs/nginx` | logs NGINX fuera de `/var/log/nginx` |
| `/var/www/SISOC` | checkout historico, `www-data:www-data`, modo 777 |
| `/opt/ssies/SISOC-Backoffice-deprecated` | checkout historico/deprecated |
| `/var/lib/mysql` | datadir local heredado, 200 MB, `mysql:mysql`, modo 700 |

Backend activo:

- branch `main`;
- HEAD `980c2b05397b3a18bdcd5853763c6942632232ed`;
- coincide exactamente con `main` actual de GitHub al 2026-07-13;
- working tree sin cambios tracked, con `tmp/` no trackeado.

Mobile activo:

- branch `main`;
- HEAD `ec7c163fede8b3877fff0fd7863f0a7812043c2c`;
- sin cambios tracked, con `.env` no trackeado esperado.

No se leyo ni borro contenido de `tmp/`, media, checkouts historicos o `.env`.

## Backup local de media

El 2026-07-13 se creo, con aprobacion explicita, el snapshot local
`/sisoc/backups/media/20260713_172352/media`:

- fuente `/sisoc/SISOC/media`, sin mover ni borrar el original;
- fuente medida en 69,226,448,310 bytes mediante `du -sb`;
- 68,548 archivos regulares en fuente y destino, con igual suma de bytes;
- dos pasadas `rsync -aH --numeric-ids --one-file-system --partial`;
- segunda pasada con cero archivos transferidos;
- dry-run final con `PENDING_CHANGES=0`;
- prioridad reducida mediante `nice` e `ionice`;
- estado root-only en
  `/sisoc/backups/media/20260713_172352/status.txt`;
- ningun servicio fue detenido o reiniciado.

La copia es util para rollback local y como fuente de migracion, pero no es
disaster recovery: comparte servidor, disco logico y filesystem con el origen.
Fue tomada en vivo, por lo que no constituye un snapshot atomico. No se hizo un
checksum completo ni una copia fuera del host.

## Base de datos

La identidad canonica fue confirmada desde Django con una consulta de solo
metadatos:

- configurado `10.80.5.46:3306` por TCP;
- servidor real `ldmzsql-sisoc`;
- UUID remoto `029056ed-ca22-11ea-a02b-005056a21400`;
- schema `sisoc_local`;
- conectividad TCP confirmada.

El responsable informo que existen backups de la DB. No se inspeccionaron su
ubicacion, retencion, integridad ni evidencia de restore, por lo que esos puntos
siguen pendientes.

MySQL local:

- servicio activo y habilitado desde 2026-06-24;
- listener en `0.0.0.0:3306`;
- datadir de 200 MB;
- UUID `39c3f26e-78f1-11f0-8e8b-005056a21960`, igual al MySQL local heredado
  observado en HML;
- cero schemas de aplicacion;
- unica conexion observada: daemon interno `event_scheduler`;
- cero eventos habilitados, replicas o miembros Group Replication;
- cero conexiones de clientes en las muestras;
- sin referencias localhost/MySQL en systemd o `/etc/cron.d` detectadas.

La evidencia es favorable a evaluar un Stage 1 reversible en el futuro, pero en
produccion no se aplico ni se autoriza ningun cambio.

## NGINX, dominios y TLS

Configuracion activa: `/etc/nginx/sites-enabled/sisoc` ->
`/etc/nginx/sites-available/sisoc`.

- dominio canonico: `sisoc.secretarianaf.gob.ar`;
- alias observado: `com.sisoc.secretarianaf.gob.ar`;
- `/static/` y `/media/` salen de `/sisoc/SISOC`;
- `/mobile/` proxya a `127.0.0.1:8080`;
- `/` proxya a `localhost:8001`;
- `client_max_body_size 500M`;
- NGINX escribe en `/sisoc/logs/nginx`.

`/`, `/health/` y `/mobile/` respondieron HTTP 200 al validar funcionalidad. El
wildcard configurado es el mismo certificado vencido el 2026-03-06 observado en
HML; HTTPS normal fallo y con validacion deshabilitada respondio. Por instruccion
del responsable, TLS queda documentado pero fuera del trabajo siguiente.

No se ejecuto `nginx -t`, no se edito configuracion y no se recargo NGINX.

## Logs y observabilidad

- access log NGINX: aproximadamente 1.90 GB, owner `www-data:root`, modo 644;
- error log NGINX: aproximadamente 116 MB, mismo owner/modo;
- logs Django en disco: 1.3 GB organizados por fecha;
- no se detecto una regla logrotate que referencie `/sisoc`;
- conteos de los ultimos 30 minutos: cero lineas con patrones
  error/exception/traceback/critical/fatal en los siete contenedores;
- journal ultimas 24 horas: cero entradas prioridad error para Docker, NGINX,
  MySQL y runner;
- no se imprimio contenido de logs para evitar PII, URLs o secretos.

## Cron efectivo

- `jportilla`: cero entradas activas.
- root: cuatro entradas activas, auditadas por conteos sanitizados.
- Se confirmo una referencia a cada familia: `docker system prune`,
  `purge_auditlog`, path historico bajo `/home/admin-ssies`, path historico bajo
  `/opt/ssies` y HetrixTools.
- Los dos paths historicos ya no existen.
- `scripts/crontab` versionado contiene esas cuatro entradas, incluida una poda
  Docker semanal con retencion 24h y `--volumes`.

El contador puntual de `--volumes` del preflight tuvo un error de argumentos y
no se usa como evidencia. Antes de cualquier cambio debe confirmarse que la
linea efectiva coincide exactamente con el contrato versionado. No se imprimio
el crontab completo y no se modifico.

## Runtimes detectados

| Componente | Version |
| --- | --- |
| Python host | 3.10.12 |
| Python Django container | 3.11.15 |
| Docker Engine | 28.0.1 |
| Docker Compose | 2.33.1 |
| MySQL server/client | 8.0.46 |
| NGINX | 1.18.0 |
| Apache | 2.4.52, servicio fallido |
| Node/npm/yarn/pnpm host | no detectados |
| Redis/PostgreSQL | no detectados |

El contenedor final de mobile no incluye el binario Node, consistente con un
artefacto frontend servido por NGINX.

## Deploy actual

1. Un push a `main` dispara `.github/workflows/deploy.yml`.
2. El job usa GitHub Environment `production` y runner `sisoc-produccion`.
3. `APP_ROOT` apunta al checkout ya provisionado; no usa `actions/checkout`.
4. Ejecuta `scripts/operacion/deploy_refresh.sh --yes`.
5. El script baja el stack, hace pull `--ff-only`, reconstruye y levanta.
6. El entrypoint puede ejecutar migraciones y otras escrituras DB.

El workflow presente en `main` productivo no incluye `--with-mobile`, mientras
la rama usada en HML si lo incluye. El checkout productivo coincide con GitHub;
no es drift local. El deploy/rollback de SISOC-Mobile en produccion queda como
flujo separado no confirmado.

## Dependencias externas criticas

- MySQL produccion `10.80.5.46`.
- GitHub Actions, Environment `production` y runner self-hosted.
- SISOC-Mobile.
- GESTIONAR y RENAPER.
- correo, Sentry y Ticketera.
- DNS/TLS.
- Zabbix, Webmin y HetrixTools.

Solo se relevaron nombres de variables/configuracion; no se imprimieron valores.

## Comandos ejecutados

Solo lectura:

- SSH batch y consultas de host/usuario;
- `hostnamectl`, `uname`, `id`, `uptime`, `df`, `du`, `stat`, `find`;
- `systemctl show/is-active/is-enabled/list-timers`;
- `ss` y metadata de procesos/puertos;
- Git branch, HEAD y status con locks opcionales deshabilitados;
- Docker `ps`, `compose ls/config --services`, `inspect` sin environment,
  `system df` y metadata de volumenes;
- `curl` local con `--resolve` y metadata publica `openssl x509`;
- consulta DB de identidad desde Django y preflight MySQL local con SQL de
  metadatos, sin query text;
- conteos sanitizados de cron y logs, sin imprimir su contenido;
- consulta read-only del `main` actual mediante GitHub.

Escritura aprobada:

- creacion de `/sisoc/backups/media/20260713_172352/media` y `status.txt`;
- copia local de media en dos pasadas con `rsync`, sin `--delete`;
- validacion por conteo, bytes y dry-run final sin diferencias pendientes.

## No verificado

1. Ubicacion, retencion, integridad y ultimo restore probado de los backups DB
   informados para `10.80.5.46`.
2. Checksum completo, copia fuera del host y crecimiento historico de media.
3. Linea exacta del cron root de poda Docker y resultado de sus ejecuciones.
4. Flujo efectivo de deploy/rollback de SISOC-Mobile.
5. Owner/proceso exacto del listener local 556.
6. Necesidad real de Apache, `sisoc.service` y checkouts historicos.
7. Firewall/ACL efectivos para 3306, 8001, 10000 y 10050.
8. Politica de retencion legal/operativa de logs y auditoria.
9. Backups seguros de configuracion fuera del host.
10. Uso de disco posterior al backup local: el reintento read-only de `df`
    encontro un timeout SSH y no se repitio en esta fase.
