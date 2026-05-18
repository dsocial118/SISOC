# Deploy QA en Debian 13 con Docker Compose y NGINX

Estado: runbook operativo para replicar QA en servidores Debian GNU/Linux 13 (trixie).

## Topologia esperada

| Rol | Host actual QA | Ruta principal | Servicio |
| --- | --- | --- | --- |
| SITE-QA | `10.1.131.121` | `/opt/sisoc/SISOC` | Django/SISOC + NGINX |
| DB-QA | `10.1.130.88` | `/opt/sisoc-mysql` | MySQL 8.0 |

QA despliega la branch `development` y usa solo:

```bash
docker compose -f docker-compose.deploy.yml up -d --build
```

No usar `docker-compose.site.yml` ni `docker-compose.yml` para deploy. `docker-compose.yml` queda reservado para local/dev.

## Reglas de seguridad

- No usar `docker compose down -v` sin aprobacion explicita.
- No borrar volumenes ni directorios de datos MySQL.
- Antes de pisar una DB existente, generar backup preventivo.
- No dejar `root` MySQL remoto abierto; si existe `root`@`%`, debe quedar bloqueado.
- No usar `source .env`: los passwords pueden contener caracteres especiales. Editar valores explicitamente o parsear `.env` con un script seguro.
- Firewall:
  - SITE-QA: SSH, `80/tcp` y opcional `443/tcp`.
  - DB-QA: SSH y `3306/tcp` solo desde SITE-QA y redes aprobadas, por ejemplo VPN.

## Relevar estado inicial

En ambos servidores:

```bash
hostname
whoami
pwd
systemctl is-active docker || true
systemctl is-active nginx || true
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
docker compose ls
```

En SITE-QA:

```bash
ls -ld /opt/sisoc /opt/sisoc/SISOC
sudo -H -u sisoc-deploy git -C /opt/sisoc/SISOC branch --show-current
sudo -H -u sisoc-deploy git -C /opt/sisoc/SISOC rev-parse --short HEAD
sudo -H -u sisoc-deploy git -C /opt/sisoc/SISOC status -sb
test -f /opt/sisoc/SISOC/.env && ls -l /opt/sisoc/SISOC/.env
```

En DB-QA:

```bash
ls -ld /opt/sisoc-mysql
sudo find /opt/sisoc-mysql -maxdepth 2 -type f -o -type d
sudo docker ps --filter name=sisoc-mysql
sudo docker logs --tail 80 sisoc-mysql
```

Si hay contenedores levantados por `docker-compose.yml` o `docker-compose.site.yml`, bajarlos sin volumenes:

```bash
cd /opt/sisoc/SISOC
docker compose -f docker-compose.yml down
docker compose -f docker-compose.site.yml down
```

## DB-QA: MySQL 8.0

Crear `/opt/sisoc-mysql/compose.yml`:

```yaml
services:
  mysql:
    image: mysql:8.0
    container_name: sisoc-mysql
    restart: unless-stopped
    env_file: .env
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${SISOC_DB_NAME}
    ports:
      - "3306:3306"
    volumes:
      - ./data:/var/lib/mysql
      - ./conf:/etc/mysql/conf.d:ro
      - ./init:/docker-entrypoint-initdb.d:ro
    command:
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
      - --default-time-zone=-03:00
```

Crear `/opt/sisoc-mysql/.env` con permisos `600`:

```dotenv
MYSQL_ROOT_PASSWORD=<ROOT_MYSQL_QA_PASSWORD>
SISOC_DB_NAME=sisoc_qa
SISOC_DB_USER=djangoapp
SISOC_DB_PASSWORD=<DJANGOAPP_QA_PASSWORD>
```

Crear `/opt/sisoc-mysql/init/01-users.sql` con permisos `600`:

```sql
CREATE USER IF NOT EXISTS 'djangoapp'@'%' IDENTIFIED WITH mysql_native_password BY '<DJANGOAPP_QA_PASSWORD>';
ALTER USER 'djangoapp'@'%' IDENTIFIED WITH mysql_native_password BY '<DJANGOAPP_QA_PASSWORD>';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, INDEX, REFERENCES,
      CREATE TEMPORARY TABLES, LOCK TABLES, TRIGGER
ON `sisoc_qa`.* TO 'djangoapp'@'%';
FLUSH PRIVILEGES;
```

Levantar MySQL:

```bash
cd /opt/sisoc-mysql
docker compose -f compose.yml up -d
docker exec sisoc-mysql mysqladmin ping -uroot -p"$MYSQL_ROOT_PASSWORD" --silent
```

El comando anterior usa la variable dentro del contenedor. No ejecutar `source .env`.

## Si root MySQL no autentica

Esto pasa cuando el volumen ya fue inicializado con otro password. Resetear root sin borrar datos:

```bash
cd /opt/sisoc-mysql
docker stop sisoc-mysql
docker run --rm -d --name sisoc-mysql-recover --network none \
  -v /opt/sisoc-mysql/data:/var/lib/mysql \
  -v /opt/sisoc-mysql/conf:/etc/mysql/conf.d:ro \
  mysql:8.0 \
  --skip-grant-tables --skip-networking \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci \
  --default-time-zone=-03:00
```

Generar SQL temporal parseando `.env` sin `source`:

```bash
sudo python3 - <<'PY' >/tmp/reset-root.sql
from pathlib import Path

vals = {}
for raw in Path("/opt/sisoc-mysql/.env").read_text(errors="replace").splitlines():
    if "=" not in raw or raw.strip().startswith("#"):
        continue
    k, v = raw.split("=", 1)
    vals[k.strip()] = v.strip().strip('"').strip("'")

def q(value):
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"

root = vals["MYSQL_ROOT_PASSWORD"]
print("FLUSH PRIVILEGES;")
print("ALTER USER IF EXISTS 'root'@'localhost' IDENTIFIED BY " + q(root) + ";")
print("ALTER USER IF EXISTS 'root'@'127.0.0.1' IDENTIFIED BY " + q(root) + ";")
print("ALTER USER IF EXISTS 'root'@'::1' IDENTIFIED BY " + q(root) + ";")
print("ALTER USER IF EXISTS 'root'@'%' IDENTIFIED BY " + q(root) + " ACCOUNT LOCK;")
print("FLUSH PRIVILEGES;")
PY
docker exec -i sisoc-mysql-recover mysql -uroot </tmp/reset-root.sql
rm -f /tmp/reset-root.sql
docker stop sisoc-mysql-recover
docker compose -f compose.yml up -d
```

Validar que `root` remoto este bloqueado:

```bash
docker exec sisoc-mysql sh -lc \
  'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -N -e "SELECT User, Host, plugin, account_locked FROM mysql.user WHERE User IN (\"root\", \"djangoapp\") ORDER BY User, Host;"'
```

## Restaurar dump QA

Colocar el dump en:

```text
/opt/sisoc-mysql/dump.sql.gz
```

Validar integridad:

```bash
gzip -t /opt/sisoc-mysql/dump.sql.gz
```

Backup preventivo si `sisoc_qa` existe:

```bash
cd /opt/sisoc-mysql
stamp=$(date +%Y%m%d_%H%M%S)
mkdir -p backups
if docker exec sisoc-mysql sh -lc 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -N -e "SHOW DATABASES LIKE '\''sisoc_qa'\'';"' | grep -qx sisoc_qa; then
  docker exec sisoc-mysql sh -lc \
    'mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction --routines --triggers sisoc_qa' \
    | gzip -c > "backups/sisoc_qa_pre_restore_${stamp}.sql.gz"
fi
```

Recrear DB e importar:

```bash
docker exec -i sisoc-mysql sh -lc 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' <<'SQL'
DROP DATABASE IF EXISTS `sisoc_qa`;
CREATE DATABASE `sisoc_qa` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SQL

gzip -dc /opt/sisoc-mysql/dump.sql.gz \
  | docker exec -i sisoc-mysql sh -lc 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" --database=sisoc_qa'
```

Aplicar usuario y grants:

```bash
docker exec -i sisoc-mysql sh -lc 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' </opt/sisoc-mysql/init/01-users.sql
```

Validar:

```bash
docker exec sisoc-mysql sh -lc \
  'MYSQL_PWD="$SISOC_DB_PASSWORD" mysql --ssl-mode=DISABLED -h127.0.0.1 -u"$SISOC_DB_USER" -D"$SISOC_DB_NAME" -N -e "SELECT DATABASE(); SELECT COUNT(*) FROM django_migrations;"'
```

## SITE-QA: repo y `.env`

El repo debe estar en `/opt/sisoc/SISOC`, owner `sisoc-deploy:sisoc-deploy`, branch `development`:

```bash
sudo -H -u sisoc-deploy git -C /opt/sisoc/SISOC fetch origin --prune
sudo -H -u sisoc-deploy git -C /opt/sisoc/SISOC checkout development
sudo -H -u sisoc-deploy git -C /opt/sisoc/SISOC pull --ff-only origin development
```

Archivo `/opt/sisoc/SISOC/.env` minimo para QA:

```dotenv
DJANGO_DEBUG=False
ENVIRONMENT=qa
DJANGO_ALLOWED_HOSTS=10.1.131.121,127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=http://10.1.131.121,http://127.0.0.1,http://localhost
DATABASE_HOST=10.1.130.88
DATABASE_PORT=3306
DATABASE_USER=djangoapp
DATABASE_PASSWORD=<DJANGOAPP_QA_PASSWORD>
DATABASE_NAME=sisoc_qa
WAIT_FOR_DB=true
RUN_MAKEMIGRATIONS_ON_START=false
DOMINIO=http://10.1.131.121/
```

Permisos:

```bash
sudo chown sisoc-deploy:sisoc-deploy /opt/sisoc/SISOC/.env
sudo chmod 600 /opt/sisoc/SISOC/.env
```

Validar DB desde SITE-QA:

```bash
MYSQL_PWD='<DJANGOAPP_QA_PASSWORD>' mysql --ssl=0 \
  -h10.1.130.88 -P3306 -udjangoapp -Dsisoc_qa \
  -N -e "SELECT DATABASE(); SELECT COUNT(*) FROM django_migrations;"
```

Levantar SISOC:

```bash
cd /opt/sisoc/SISOC
sudo -H -u sisoc-deploy docker compose -f docker-compose.deploy.yml up -d --build
sudo -H -u sisoc-deploy docker compose -f docker-compose.deploy.yml logs -f django
```

El log esperado termina con Gunicorn:

```text
[server] Iniciando Django en modo produccion con Gunicorn...
Listening at: http://0.0.0.0:8000
Booting worker with pid: ...
```

## NGINX en SITE-QA

Crear `/etc/nginx/sites-available/sisoc-qa`:

```nginx
server {
    listen 80;
    server_name 10.1.131.121 _;

    client_max_body_size 50m;

    access_log /var/log/nginx/sisoc-qa.access.log;
    error_log  /var/log/nginx/sisoc-qa.error.log;

    location /static/ {
        alias /opt/sisoc/SISOC/static_root/;
        try_files $uri =404;
        access_log off;
        expires 7d;
    }

    location /media/ {
        alias /opt/sisoc/SISOC/media/;
        try_files $uri =404;
        expires 1h;
    }

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 60s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

Habilitar solo ese site:

```bash
sudo ln -sfn /etc/nginx/sites-available/sisoc-qa /etc/nginx/sites-enabled/sisoc-qa
sudo rm -f /etc/nginx/sites-enabled/sisoc
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

Si `nginx -t` muestra `conflicting server name` y `sites-enabled` tiene un solo site, revisar que `/etc/nginx/nginx.conf` no incluya `sites-enabled/*` dos veces.

## Firewall

SITE-QA:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw status
```

DB-QA:

```bash
sudo ufw allow OpenSSH
sudo ufw allow from 10.1.131.121 to any port 3306 proto tcp
sudo ufw status
```

Agregar VPN solo si corresponde:

```bash
sudo ufw allow from <VPN_CIDR> to any port 3306 proto tcp
```

## Validacion final

En SITE-QA:

```bash
curl -i http://127.0.0.1:8001/health/
curl -i http://127.0.0.1/health/
curl -i http://10.1.131.121/health/
sudo -H -u sisoc-deploy docker compose -f /opt/sisoc/SISOC/docker-compose.deploy.yml ps
sudo -H -u sisoc-deploy docker compose -f /opt/sisoc/SISOC/docker-compose.deploy.yml logs --tail 200 django
sudo tail -n 100 /var/log/nginx/sisoc-qa.error.log
```

En DB-QA:

```bash
cd /opt/sisoc-mysql
docker compose -f compose.yml ps
docker exec sisoc-mysql sh -lc \
  'MYSQL_PWD="$SISOC_DB_PASSWORD" mysql --ssl-mode=DISABLED -h127.0.0.1 -u"$SISOC_DB_USER" -D"$SISOC_DB_NAME" -N -e "SELECT DATABASE(); SELECT COUNT(*) FROM django_migrations;"'
```

## Operacion diaria

Reiniciar app:

```bash
cd /opt/sisoc/SISOC
sudo -H -u sisoc-deploy docker compose -f docker-compose.deploy.yml restart django
```

Rebuild por nuevo deploy:

```bash
cd /opt/sisoc/SISOC
sudo -H -u sisoc-deploy git pull --ff-only origin development
sudo -H -u sisoc-deploy docker compose -f docker-compose.deploy.yml up -d --build
```

Ver logs:

```bash
cd /opt/sisoc/SISOC
sudo -H -u sisoc-deploy docker compose -f docker-compose.deploy.yml logs -f --tail 200 django
sudo tail -f /var/log/nginx/sisoc-qa.error.log
```

Backup manual DB:

```bash
cd /opt/sisoc-mysql
stamp=$(date +%Y%m%d_%H%M%S)
docker exec sisoc-mysql sh -lc \
  'mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction --routines --triggers sisoc_qa' \
  | gzip -c > "backups/sisoc_qa_${stamp}.sql.gz"
```
