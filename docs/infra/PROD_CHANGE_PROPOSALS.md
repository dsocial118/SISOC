# Produccion - Propuestas de cambio

Estado: propuestas solamente. Ningun comando de este documento fue ejecutado en
produccion. Cada propuesta requiere aprobacion separada, ventana y responsable.

No ejecutar bloques completos por copia/pega sin revisar nuevamente el estado.

## Prioridad sugerida

1. demostrar backups/restores de DB y media antes de cualquier cambio;
2. corregir cron root de forma acotada;
3. agregar rotacion a logs NGINX;
4. evaluar Stage 1 del MySQL local;
5. restringir permisos de `.env` mobile;
6. retirar referencias/servicios legacy;
7. decidir si promover deploy automatico de mobile.

TLS queda fuera por instruccion expresa del responsable.

## Propuesta 1 - Stage 1 reversible del MySQL local

### Que cambiaria

Detener y deshabilitar solo `mysql.service` del app host. Conservar
`/var/lib/mysql`, paquetes y configuracion durante al menos 14 dias.

### Por que

Django usa `10.80.5.46`; el local tiene cero schemas de aplicacion, clientes,
eventos y replicacion, pero escucha globalmente en 3306.

### Riesgo y beneficio

- Riesgo: dependencia no observada o tarea esporadica que use el socket local.
- Beneficio: menor superficie de red y menos ambiguedad operativa.
- Espacio: no es objetivo; solo ocupa 200 MB y Stage 1 no lo libera.

### Precondiciones

- aprobacion explicita de stop/disable;
- backup DB canonica vigente confirmado externamente;
- repetir preflight y observar conexiones en mas de una ventana;
- responsable disponible durante 15 minutos y observacion posterior 14 dias.

### Comandos exactos propuestos

No ejecutar sin aprobacion:

```bash
set -euo pipefail
[[ "$(hostname -s)" == "mdsldmz-ssies" ]]

docker exec sisoc-django-1 python manage.py shell -c \
  "from django.db import connection; connection.ensure_connection(); c=connection.cursor(); c.execute('SELECT @@hostname, DATABASE()'); r=c.fetchone(); c.close(); assert str(connection.settings_dict.get('HOST')) == '10.80.5.46'; assert r[0] == 'ldmzsql-sisoc'; assert r[1] == 'sisoc_local'; print('remote_db_preflight=ok')"

sudo mysql --protocol=socket --batch --skip-column-names --raw -e \
  "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name NOT IN ('information_schema','performance_schema','mysql','sys');"
sudo mysql --protocol=socket --batch --skip-column-names --raw -e \
  "SELECT COUNT(*) FROM information_schema.processlist WHERE ID <> CONNECTION_ID() AND NOT (USER='event_scheduler' AND COMMAND='Daemon');"
sudo mysql --protocol=socket --batch --skip-column-names --raw -e \
  "SELECT COUNT(*) FROM information_schema.EVENTS WHERE STATUS='ENABLED';"
sudo mysql --protocol=socket --batch --skip-column-names --raw -e \
  "SELECT COUNT(*) FROM performance_schema.replication_connection_status WHERE SERVICE_STATE='ON';"

TS="$(date +%Y%m%d_%H%M%S)"
BACKUP="/var/backups/sisoc/mysql-local-retirement/prod/$TS"
sudo install -d -m 700 "$BACKUP/metadata"
sudo cp -a /etc/mysql "$BACKUP/etc-mysql"
sudo cp -a /var/lib/mysql/auto.cnf "$BACKUP/metadata/auto.cnf"
sudo sh -c "systemctl cat mysql > '$BACKUP/metadata/mysql.service.txt'"
sudo sh -c "systemctl status mysql --no-pager > '$BACKUP/metadata/mysql.status.before.txt'"
sudo sh -c "du -sh /var/lib/mysql > '$BACKUP/metadata/datadir-size.txt'"
sudo sh -c "mysql --protocol=socket --batch --skip-column-names --raw -e 'SELECT @@hostname,@@port,@@server_uuid,@@server_id,@@datadir,@@event_scheduler,@@read_only,@@super_read_only' > '$BACKUP/metadata/identity.tsv'"
sudo find "$BACKUP" -type d -exec chmod 700 {} +
sudo find "$BACKUP" -type f -exec chmod 600 {} +

sudo systemctl stop mysql
sudo systemctl disable mysql

systemctl is-active mysql || true
systemctl is-enabled mysql || true
ss -Hlnpt 'sport = :3306' || true
docker ps --format '{{.Names}}|{{.Status}}'
docker exec sisoc-django-1 python manage.py shell -c \
  "from django.db import connection; connection.ensure_connection(); assert str(connection.settings_dict.get('HOST')) == '10.80.5.46'; c=connection.cursor(); c.execute('SELECT 1'); assert c.fetchone()[0] == 1; c.close(); print('remote_db_after=ok')"
curl --max-time 8 -fsS http://127.0.0.1:8001/health/ >/dev/null
```

Todos los conteos previos deben dar cero. Si no, detenerse.

### Backup y rollback

Backup root-only en la ruta timestamp anterior. Rollback inmediato:

```bash
sudo systemctl enable --now mysql
systemctl show mysql -p ActiveState -p UnitFileState --no-pager
ss -Hlnpt 'sport = :3306'
```

No copiar configuracion ni restaurar datadir mientras sigan intactos.

### Verificar exito / detectar fallo

Exito: MySQL inactive/disabled, sin listener 3306, siete contenedores activos,
Django en `10.80.5.46` y health 200.

Fallo: listener persiste, DB identity cambia, health falla, workers reinician o
aparece un consumidor local. Ante cualquiera, ejecutar rollback.

## Propuesta 2 - Hacer conservadora la poda Docker de root

### Que cambiaria

Reemplazar una unica linea exacta de cron que use retencion 24h y `--volumes`
por retencion 14 dias sin volumenes. Preservar el resto del crontab.

### Por que

Produccion usa solo 12% del disco. Una poda agresiva semanal reduce capacidad de
rollback y puede afectar recursos no clasificados sin necesidad operativa.

### Riesgo y beneficio

- Riesgo: error al editar root cron o acumulacion mayor de imagenes.
- Beneficio: conserva rollback reciente y nunca solicita poda de volumenes.

### Comandos exactos propuestos

El primer comando debe devolver exactamente `1`; si devuelve otro valor, no
continuar:

```bash
OLD='0 3 * * 0 /usr/bin/docker system prune -af --filter "until=24h" --volumes'
NEW='0 3 * * 0 /usr/bin/docker system prune -af --filter "until=336h"'

sudo crontab -l | grep -Fxc -- "$OLD"

TS="$(date +%Y%m%d_%H%M%S)"
BACKUP="/var/backups/sisoc/cron-prod/$TS"
TMP="/tmp/root.crontab.sisoc.$TS"
sudo install -d -m 700 "$BACKUP"
sudo sh -c "crontab -l > '$BACKUP/root.crontab.before'"
sudo chmod 600 "$BACKUP/root.crontab.before"

umask 077
sudo crontab -l | awk -v old="$OLD" -v new="$NEW" \
  '{ if ($0 == old) print new; else print }' > "$TMP"

grep -Fxc -- "$OLD" "$TMP"
grep -Fxc -- "$NEW" "$TMP"
grep -Fc -- '--volumes' "$TMP"
```

Resultados esperados: old `0`, new `1`, `--volumes` `0`. Solo entonces:

```bash
sudo crontab "$TMP"
sudo crontab -l | grep -Fxc -- "$NEW"
rm -f -- "$TMP"
```

### Backup y rollback

```bash
sudo crontab "$BACKUP/root.crontab.before"
sudo crontab -l | grep -Fxc -- "$OLD"
```

### Ventana y verificacion

Ventana de 10 minutos, sin coincidir con domingo 03:00. No requiere restart.

Exito: una linea nueva, cero `--volumes`, health sin cambios. Fallo: conteos
distintos, crontab invalido o perdida de cualquier otra entrada; restaurar backup.

## Propuesta 3 - Rotar logs NGINX bajo `/sisoc`

### Que cambiaria

Agregar una regla dedicada para los dos logs NGINX fuera de `/var/log/nginx`,
rotacion diaria/100 MB, 30 copias comprimidas y archivos nuevos modo 640.

### Por que

Access log ocupa ~1.90 GB, error log ~116 MB y no existe referencia logrotate a
`/sisoc`.

### Riesgo y beneficio

- Riesgo: compresion inicial consume CPU/I/O; owner/modo incorrecto puede cortar
  logging.
- Beneficio: crecimiento acotado y menor lectura global de logs nuevos.
- Retencion: aprobar explicitamente que rotaciones superiores a 30 se eliminen.

### Comandos exactos propuestos

```bash
TS="$(date +%Y%m%d_%H%M%S)"
BACKUP="/var/backups/sisoc/logrotate-prod/$TS"
sudo install -d -m 700 "$BACKUP"
if sudo test -e /etc/logrotate.d/sisoc-nginx; then
  sudo cp -a /etc/logrotate.d/sisoc-nginx "$BACKUP/sisoc-nginx.before"
fi

sudo tee /etc/logrotate.d/sisoc-nginx >/dev/null <<'LOGROTATE'
/sisoc/logs/nginx/*.log {
    daily
    maxsize 100M
    rotate 30
    missingok
    notifempty
    compress
    delaycompress
    create 0640 www-data root
    sharedscripts
    postrotate
        if [ -s /run/nginx.pid ]; then
            kill -USR1 "$(cat /run/nginx.pid)"
        fi
    endscript
}
LOGROTATE
sudo chown root:root /etc/logrotate.d/sisoc-nginx
sudo chmod 644 /etc/logrotate.d/sisoc-nginx
sudo logrotate -d /etc/logrotate.conf
```

Si el dry-run es limpio, en ventana de bajo trafico:

```bash
sudo logrotate -v /etc/logrotate.conf
systemctl is-active nginx
curl --max-time 8 -kfsS --resolve \
  sisoc.secretarianaf.gob.ar:443:127.0.0.1 \
  https://sisoc.secretarianaf.gob.ar/health/ >/dev/null
stat -c 'path=%n owner=%U:%G mode=%a size=%s' /sisoc/logs/nginx/*.log
```

### Backup y rollback

Si habia configuracion anterior, restaurarla con `sudo cp -a`. Si no habia:

```bash
sudo mv /etc/logrotate.d/sisoc-nginx "$BACKUP/sisoc-nginx.disabled"
sudo logrotate -d /etc/logrotate.conf
```

No borrar logs rotados durante rollback.

### Verificar exito / detectar fallo

Exito: NGINX activo, health 200, logs nuevos modo 640 y escritura continua.
Fallo: NGINX inactivo, errores de logrotate, archivos sin crecimiento o permisos
incorrectos; restaurar config y enviar `USR1` nuevamente, sin restart completo.

## Propuesta 4 - Restringir `.env` de SISOC-Mobile

### Que cambiaria

Cambiar `/sisoc/SISOC-Mobile/.env` de `root:root` 664 a
`root:sisoc-deploy` 640, manteniendo al runner como lector.

### Por que

El archivo es world-readable y su permiso depende hoy de lectura global. Aunque
las cinco variables observadas parecen publicas, el archivo puede incorporar
secretos en el futuro.

### Riesgo y beneficio

- Riesgo: operadores fuera de `sisoc-deploy` pierden lectura manual.
- Beneficio: reduce exposicion local y alinea ownership con el deploy efectivo.

### Comandos exactos propuestos

```bash
TS="$(date +%Y%m%d_%H%M%S)"
BACKUP="/var/backups/sisoc/mobile-env-permissions/$TS"
sudo install -d -m 700 "$BACKUP"
sudo cp -a /sisoc/SISOC-Mobile/.env "$BACKUP/.env.before"
sudo chmod 600 "$BACKUP/.env.before"

sudo chown root:sisoc-deploy /sisoc/SISOC-Mobile/.env
sudo chmod 640 /sisoc/SISOC-Mobile/.env

sudo -u sisoc-deploy test -r /sisoc/SISOC-Mobile/.env
sudo -u sisoc-deploy docker compose \
  -f /sisoc/SISOC-Mobile/compose.prod.yaml \
  --project-directory /sisoc/SISOC-Mobile config --services
stat -c 'path=%n owner=%U:%G mode=%a' /sisoc/SISOC-Mobile/.env
```

No requiere restart ni recreacion del contenedor.

### Backup y rollback

```bash
sudo chown root:root /sisoc/SISOC-Mobile/.env
sudo chmod 664 /sisoc/SISOC-Mobile/.env
```

### Ventana y verificacion

Ventana de 10 minutos fuera de deploy. Exito: runner puede leer/configurar y
modo queda 640. Fallo: Compose no puede resolver config o operador requerido
pierde acceso; ejecutar rollback.

## Propuesta 5 - Retirar cron y servicios legacy sin borrar datos

### Que cambiaria

Eliminar solo dos entradas root que apuntan a paths inexistentes y deshabilitar
el arranque futuro de `apache2`/`sisoc.service`, actualmente fallidos. No borrar
unidades, paquetes, certificados ni checkouts.

### Por que

Los paths `/home/admin-ssies/SISOC-Backoffice` y
`/opt/ssies/SISOC-Backoffice` no existen. Las tareas no pueden operar sobre el
runtime actual y generan deuda silenciosa.

### Riesgo y beneficio

- Riesgo: una tarea historica podria seguir siendo requisito funcional aunque
  este rota; `purge_auditlog` implica una politica de retencion a confirmar.
- Beneficio: menos ruido y menos arranques fallidos/referencias falsas.

### Comandos exactos propuestos

Primero confirmar con owner funcional de auditoria. Luego:

```bash
test ! -e /home/admin-ssies/SISOC-Backoffice
test ! -e /opt/ssies/SISOC-Backoffice

TS="$(date +%Y%m%d_%H%M%S)"
BACKUP="/var/backups/sisoc/legacy-prod/$TS"
TMP="/tmp/root.crontab.legacy.$TS"
sudo install -d -m 700 "$BACKUP"
sudo sh -c "crontab -l > '$BACKUP/root.crontab.before'"
sudo systemctl show apache2 sisoc.service \
  -p ActiveState -p UnitFileState -p FragmentPath --no-pager \
  | sudo tee "$BACKUP/systemd.before.txt" >/dev/null
sudo find "$BACKUP" -maxdepth 1 -type f -exec chmod 600 {} +

umask 077
sudo crontab -l | awk '
  /\/home\/admin-ssies\/SISOC-Backoffice\/cron_logs\/borrar_logs.py/ { next }
  /cd \/opt\/ssies\/SISOC-Backoffice .*purge_auditlog/ { next }
  { print }
' > "$TMP"

grep -Fc '/home/admin-ssies/SISOC-Backoffice' "$TMP"
grep -Fc '/opt/ssies/SISOC-Backoffice' "$TMP"
```

Ambos conteos deben ser cero. Solo con aprobacion:

```bash
sudo crontab "$TMP"
sudo systemctl disable apache2 sisoc.service
rm -f -- "$TMP"
systemctl is-active nginx docker
curl --max-time 8 -kfsS --resolve \
  sisoc.secretarianaf.gob.ar:443:127.0.0.1 \
  https://sisoc.secretarianaf.gob.ar/health/ >/dev/null
```

### Backup y rollback

```bash
sudo crontab "$BACKUP/root.crontab.before"
sudo systemctl enable apache2 sisoc.service
```

No iniciar servicios durante rollback salvo aprobacion separada.

### Ventana y verificacion

Ventana de 15 minutos. Exito: cron conserva HetrixTools/poda aprobada, servicios
quedan disabled/inactive y app sigue 200. Fallo: desaparece otra entrada o se
afecta health/monitoreo; restaurar crontab y enablement.

## Propuesta 6 - Promover deploy de SISOC-Mobile a produccion

### Que cambiaria

Crear un PR que aplique sobre `main` el cambio ya usado en HML para invocar
`deploy_refresh.sh --with-mobile --mobile-dir /sisoc/SISOC-Mobile`.

### Por que

El workflow `main` actual no despliega mobile; HML si. Esto permite versiones
backend/mobile descoordinadas y deja un flujo manual no documentado.

### Riesgo y beneficio

- Riesgo: cada deploy backend tambien reconstruye/reinicia mobile; aumenta el
  radio de impacto.
- Beneficio: flujo reproducible y version coordinada.

### Comandos exactos propuestos

Ejecutar solo localmente, nunca editando el checkout productivo:

```bash
git fetch origin
git switch -c codex/prod-mobile-auto-deploy origin/main
git cherry-pick f68aca084f911542e53e9f42435b17bb098b533f
git diff --check origin/main...HEAD
bash -n scripts/operacion/deploy_refresh.sh
git push -u origin codex/prod-mobile-auto-deploy
gh pr create --base main --head codex/prod-mobile-auto-deploy \
  --title "ci(deploy): desplegar SISOC-Mobile en produccion"
```

Requiere review, checks verdes, Environment `production` con reviewer y ventana
aprobada para el primer deploy.

### Backup y rollback

Antes del primer deploy registrar:

```bash
git -C /sisoc/SISOC rev-parse HEAD
git -C /sisoc/SISOC-Mobile rev-parse HEAD
docker inspect --format '{{.Name}} {{.Image}}' \
  sisoc-django-1 sisoc-mobile-frontend-1
```

Rollback del codigo: revertir el commit mediante otro PR. Rollback operativo:
volver al commit/image mobile previo solo con una ventana y comandos propios del
repo mobile; no improvisar un segundo deploy backend.

### Verificar exito / detectar fallo

Exito: workflow aprobado, ambos repos en commits esperados, siete contenedores
activos y `/health/`/`/mobile/` 200. Fallo: mobile unhealthy, commit inesperado,
backend afectado o DB writes no aprobadas; detener promocion y ejecutar rollback
coordinado.

## Temas deliberadamente sin propuesta ejecutable

- TLS: postergado por el responsable.
- Backup DB/media: falta definir herramienta, storage, credenciales, RPO/RTO y
  restore target; inventar comandos seria inseguro.
- Bind 8001/firewall: requiere conocer ACL y balanceo antes de editar Compose.
- Retencion de logs Django/auditoria: requiere politica funcional/legal antes de
  eliminar archivos o registros.
- Checkouts historicos y `tmp/`: no borrar ni mover hasta clasificar contenido.
