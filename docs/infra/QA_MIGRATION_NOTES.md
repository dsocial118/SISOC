# QA - Notas iniciales de migracion

Estado: actualizado con inventario operativo, corte 2026-07-13.

Estas notas no autorizan una migracion. La fuente canonica confirmada es
`qa-old`; AWS queda como referencia de destino futuro y fuera de alcance actual.

## Precondiciones antes de planificar fecha

1. Confirmar inventario y capacidad del destino elegido cuando comience la
   migracion.
2. Inventariar la DB autoritativa actual en `10.80.9.18` sin mostrar credenciales.
3. Confirmar backup actual, retencion y restore probado.
4. Obtener firewall/ACL efectivos y decidir la conservacion del MySQL local ya
   inventariado antes de Stage 2.
5. Acordar si el destino mantiene SITE/DB separados.
6. Congelar una ventana de cambios y un commit fuente.

## Que habria que copiar

| Elemento | Tratamiento sugerido |
| --- | --- |
| `media/` | Copia preservando estructura, timestamps y checksum. Volumen observado: 2.8 GiB, 8.336 archivos. |
| `.env` | Transferencia por canal seguro fuera de Git; validar owner/modo 600 en destino. No copiar a backups versionados. |
| Base MySQL autoritativa | Dump consistente o mecanismo acordado con Infra, solo tras confirmar host/schema y aprobar la operacion. |
| NGINX | Respaldar `nginx.conf`, `sites-available/staging.conf`, symlinks habilitados y metadata. |
| Cron efectivo | Exportar root/`sisoc-deploy` con redaccion de secretos; no alcanza con `scripts/crontab`. |
| Configuracion systemd | Runner y cualquier unidad SISOC/custom; preferir reinstalar runner. |
| Logs | Solo si hay requisito operativo, legal o de auditoria; no son necesarios para arrancar. |
| Evidencia de versiones | SO, Docker, Compose, NGINX, MySQL, imagen Python y commit desplegado. |

No copiar como fuente primaria sin validacion:

- `static_root/`: es regenerable con `collectstatic`.
- imagenes/caches Docker: reconstruir desde Dockerfile cuando sea posible.
- dumps locales antiguos: los dos detectados fueron eliminados con aprobacion y
  no eran backups validados.
- credenciales internas del GitHub runner: re-registrar el runner en destino.
- el working tree completo como tar si se puede clonar el commit limpio desde Git.

## Que habria que reinstalar

Segun la topologia elegida:

- Docker Engine y Docker Compose plugin compatibles.
- NGINX.
- Git y cliente SSH/CA del sistema.
- MySQL 8 si el nuevo diseño mantiene DB en host dedicado/local.
- Certbot solo si QA pasa a TLS.
- agente de monitoreo confirmado para los puertos 10000/10050.
- GitHub Actions runner self-hosted, registrado con label `sisoc-qa`.

Python, Gunicorn, cliente MySQL, Tesseract, Poppler y librerias de aplicacion se
instalan dentro de la imagen Docker. El Dockerfile observado usa
`python:3.11.15-slim-bookworm`.

## Que habria que configurar

### Host de aplicacion

- hostname, zona horaria y sincronizacion de reloj;
- usuario/grupo operativo `sisoc-deploy` con acceso Docker acotado;
- checkout limpio en branch `development` y commit aprobado;
- `.env` real modo 600;
- NGINX: HTTP/HTTPS, limite de upload, aliases de static/media y proxy a 8001;
- firewall/ACL: SSH, 80/443 y necesidad real de 8001;
- GitHub Environment `qa`: `APP_ROOT` correcto;
- runner `sisoc-qa` restringido al workflow de deploy confiable;
- cron real y logrotate;
- monitoreo/alertas de disco, health y errores.

### Host de base de datos

- MySQL 8 compatible y charset/collation requeridos;
- bind y firewall limitado al host de aplicacion y redes aprobadas;
- schema/user de QA con privilegios minimos;
- backup, retencion, cifrado y restore test;
- capacidad de disco y crecimiento;
- logs y monitoreo sin exponer queries/datos sensibles.

## Secretos que habria que recrear o transferir de forma segura

No registrar valores en Git, consola compartida ni estos documentos.

- `DJANGO_SECRET_KEY` y configuracion de hosts/origins.
- credenciales y nombre de base MySQL.
- claves/endpoints de GESTIONAR.
- credenciales RENAPER.
- Google Maps API key.
- Sentry DSN/configuracion.
- SMTP y remitente.
- claves web push.
- Ticketera, si esta habilitada.
- deploy key Git/SSH.
- token efimero de registro del runner.

Las credenciales del runner viejo no deben copiarse como archivos; se debe crear
un runner nuevo y retirar el anterior solo despues del cutover validado.

## Servicios que habria que levantar

Orden conceptual, no ejecutable sin aprobacion:

1. red/firewall y DNS interno;
2. MySQL y restauracion validada;
3. Docker/containerd en SITE;
4. servicios Compose `django` y `ocr_worker`;
5. NGINX;
6. cron y monitoreo;
7. runner self-hosted, preferentemente despues de validar manualmente el runtime.

Precaucion: levantar `django` ejecuta migraciones, fixtures, usuarios/grupos y
`collectstatic`. No iniciar el servicio como simple prueba antes de autorizar esos
side effects sobre la DB restaurada.

## Dominios y SSL

Situacion observada en QA viejo:

- acceso por `http://10.80.9.15/`;
- NGINX en 80, sin `server_name` detectado;
- sin certificados bajo `/etc/letsencrypt/live`.

Antes de migrar, decidir si QA seguira por IP/HTTP interno o tendra hostname/TLS.
Si hay dominio:

- confirmar ownership DNS y TTL antes de la ventana;
- emitir certificado nuevo o transferirlo segun politica de Infra;
- validar cadena, renovacion y timer autoritativo;
- no copiar claves privadas a Git ni a backups sin cifrar.

## Checklist de datos y archivos

- [x] Fuente QA canonica confirmada: `qa-old`.
- [ ] Commit de `development` congelado y registrado.
- [ ] Working tree fuente limpio o excepciones identificadas.
- [ ] `.env` transferido por canal seguro y validado sin imprimir valores.
- [ ] `media/` copiado con conteo y checksums.
- [x] Routing DB fuente identificado en configuracion: `10.80.9.18:3306`, schema
      `sisoc_local`; falta validar backup/restore y estado del servicio.
- [ ] Backup consistente creado y checksum registrado.
- [ ] Restore probado en destino aislado.
- [ ] NGINX y cron exportados.
- [ ] Puertos 8001, 3306, 10000 y 10050 justificados/restringidos.
- [ ] Runner nuevo registrado sin reutilizar credenciales persistentes.
- [x] Dumps viejos detectados eliminados con aprobacion; no usarlos como fuente
      de migracion.

## Comandos de validacion del QA migrado

Ejecutar solo en la fase aprobada, sin imprimir secretos:

```bash
hostnamectl
date --iso-8601=seconds
df -hT /
df -ih /

systemctl is-active docker containerd nginx cron
systemctl is-enabled docker nginx

git -C "$APP_ROOT" branch --show-current
git -C "$APP_ROOT" rev-parse HEAD
GIT_OPTIONAL_LOCKS=0 git -C "$APP_ROOT" status --short --branch

docker compose -f "$APP_ROOT/docker-compose.deploy.yml" ps
docker compose -f "$APP_ROOT/docker-compose.deploy.yml" logs --tail 200 django

nginx -t
ss -lntup
curl --max-time 8 -fsS http://127.0.0.1/health/
curl --max-time 8 -fsS "http://<QA_HOST>/health/"
```

El endpoint `/health/` solo devuelve OK y no demuestra conectividad DB. Agregar una
prueba explicita de conexion, de solo lectura y sin credenciales visibles:

```bash
docker compose -f "$APP_ROOT/docker-compose.deploy.yml" exec -T django \
  python manage.py shell -c \
  "from django.db import connection; connection.ensure_connection(); print(connection.vendor)"
```

Validaciones funcionales minimas posteriores:

- login QA con usuario autorizado;
- carga de una pagina que consulte DB;
- acceso a un archivo media existente;
- estaticos servidos por NGINX;
- worker OCR visible/estable sin ejecutar un job real no aprobado;
- egresos a GESTIONAR/RENAPER/SMTP/Sentry segun pruebas acordadas;
- logs sin errores nuevos, revisados localmente y sin pegarlos en reportes;
- deploy automatico en una ejecucion controlada, solo despues de aprobar migraciones
  y backup.

## Rollback conceptual

Antes del cutover conservar:

- QA viejo sin cambios;
- commit previo y commit nuevo;
- backup DB validado;
- copia verificada de media;
- configuracion NGINX/cron/runner inventariada;
- mecanismo para devolver DNS/ruta al host anterior.

Si falla la validacion, no improvisar limpieza ni restauracion parcial: detener el
destino, devolver trafico al QA viejo y preservar logs/evidencia para diagnostico.

## Informacion pendiente que bloquea un plan final

1. Inventario del destino cuando se active la migracion AWS u otra.
2. Tamanio, consistencia y backup de la DB `10.80.9.18`.
3. Decision de conservacion o borrado del MySQL local despues del 2026-07-20.
4. Backup vigente y restore probado.
5. Crontab de root.
6. Firewall/ACL efectivos.
7. Owner de puertos 10000/10050.
8. Politica de DNS/TLS para QA.
9. Ventana y responsable de aprobar los side effects automaticos del entrypoint.
