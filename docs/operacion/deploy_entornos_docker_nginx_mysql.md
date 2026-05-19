# Deploy de entornos con Docker Compose, MySQL y NGINX

Estado: runbook generico para replicar SISOC en QA, homologacion o produccion con dos servidores: uno de aplicacion y uno de base de datos.

Este documento define el procedimiento base. Los valores concretos de cada entorno deben completarse en la matriz del entorno antes de ejecutar comandos.

## 1. Matriz del entorno

Completar antes de empezar:

| Variable            | Descripcion                                                       | Ejemplo QA            |
| ------------------- | ----------------------------------------------------------------- | --------------------- |
| `ENV_NAME`          | Nombre operativo del entorno                                      | `qa`                  |
| `SITE_HOST`         | Alias SSH o hostname del servidor app                             | `qa-site-aws`         |
| `SITE_IP`           | IP del servidor app                                               | `10.1.131.121`        |
| `DB_HOST`           | Alias SSH o hostname del servidor DB                              | `qa-db-aws`           |
| `DB_IP`             | IP del servidor DB                                                | `10.1.130.88`         |
| `APP_USER`          | Usuario Linux propietario del repo                                | `sisoc-deploy`        |
| `APP_ROOT`          | Ruta del repo SISOC en SITE                                       | `/opt/sisoc/SISOC`    |
| `DB_ROOT`           | Ruta operativa MySQL en DB                                        | `/opt/sisoc-mysql`    |
| `GIT_BRANCH`        | Branch a desplegar                                                | `development`         |
| `DB_NAME`           | Base de datos Django                                              | `sisoc_qa`            |
| `DB_APP_USER`       | Usuario MySQL de Django                                           | `djangoapp`           |
| `PUBLIC_ORIGIN`     | URL publica o interna del entorno                                 | `http://10.1.131.121` |
| `PUBLIC_HOSTNAME`   | Hostname publico o interno sin esquema; si no existe, dejar vacio | ``                    |
| `USE_PROD_OVERRIDE` | Si agrega compose extra de produccion                             | `false`               |

Convenciones recomendadas:

| Entorno      | Branch         | `ENVIRONMENT`  | Compose app                                                   |
| ------------ | -------------- | -------------- | ------------------------------------------------------------- |
| QA           | `development`  | `qa`           | `docker-compose.deploy.yml`                                   |
| Homologacion | `homologacion` | `homologacion` | `docker-compose.deploy.yml`                                   |
| Produccion   | `main`         | `prd`          | `docker-compose.deploy.yml` + `docker-compose.produccion.yml` |

No usar para deploy:

- `docker-compose.yml`: reservado para local/dev.
- `docker-compose.site.yml`: no forma parte del camino operativo base.

Para que los comandos sean copiables, definir variables en cada sesion SSH:

```bash
export ENV_NAME=qa
export SITE_IP=10.1.131.121
export DB_IP=10.1.130.88
export APP_USER=sisoc-deploy
export APP_ROOT=/opt/sisoc/SISOC
export DB_ROOT=/opt/sisoc-mysql
export GIT_BRANCH=development
export DB_NAME=sisoc_qa
export DB_APP_USER=djangoapp
export PUBLIC_ORIGIN=http://10.1.131.121
export PUBLIC_HOSTNAME=
```

Los passwords no se exportan como variables de shell salvo para pruebas puntuales. Editar `.env` explicitamente o generar SQL con los scripts de este runbook.

## Camino copy-paste recomendado

Este es el camino operativo principal. Copiar los bloques en orden y cambiar solo las variables del entorno.

### A. DB: variables del entorno

Ejecutar en el servidor DB:

```bash
export ENV_NAME=qa
export SITE_IP=10.1.131.121
export DB_ROOT=/opt/sisoc-mysql
export DB_NAME=sisoc_qa
export DB_APP_USER=djangoapp
export DUMP_PATH=/opt/sisoc-mysql/dump.sql.gz
```

Ingresar secretos sin dejarlos en el historial:

```bash
read -rsp "MYSQL_ROOT_PASSWORD: " MYSQL_ROOT_PASSWORD; echo
read -rsp "DB_APP_PASSWORD: " DB_APP_PASSWORD; echo
```

### B. DB: crear compose, `.env` y SQL de usuario

Ejecutar en el servidor DB:

```bash
set -Eeuo pipefail

sudo install -d -m 700 "$DB_ROOT"
sudo install -d -m 755 "$DB_ROOT/data" "$DB_ROOT/conf" "$DB_ROOT/init" "$DB_ROOT/backups"

sudo tee "$DB_ROOT/compose.yml" >/dev/null <<'YAML'
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
YAML

sudo env \
  MYSQL_ROOT_PASSWORD="$MYSQL_ROOT_PASSWORD" \
  DB_NAME="$DB_NAME" \
  DB_APP_USER="$DB_APP_USER" \
  DB_APP_PASSWORD="$DB_APP_PASSWORD" \
  DB_ROOT="$DB_ROOT" \
  python3 - <<'PY'
from pathlib import Path
import os

db_root = Path(os.environ["DB_ROOT"])
root_password = os.environ["MYSQL_ROOT_PASSWORD"]
db_name = os.environ["DB_NAME"]
db_user = os.environ["DB_APP_USER"]
db_password = os.environ["DB_APP_PASSWORD"]

def sql_quote(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"

(db_root / ".env").write_text(
    f"MYSQL_ROOT_PASSWORD={root_password}\n"
    f"SISOC_DB_NAME={db_name}\n"
    f"SISOC_DB_USER={db_user}\n"
    f"SISOC_DB_PASSWORD={db_password}\n"
)

(db_root / "init" / "01-users.sql").write_text(
    f"CREATE USER IF NOT EXISTS {sql_quote(db_user)}@'%' IDENTIFIED WITH mysql_native_password BY {sql_quote(db_password)};\n"
    f"ALTER USER {sql_quote(db_user)}@'%' IDENTIFIED WITH mysql_native_password BY {sql_quote(db_password)};\n"
    "GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, INDEX, REFERENCES,\n"
    "      CREATE TEMPORARY TABLES, LOCK TABLES, TRIGGER\n"
    f"ON `{db_name}`.* TO {sql_quote(db_user)}@'%';\n"
    "FLUSH PRIVILEGES;\n"
)
PY

sudo chmod 600 "$DB_ROOT/.env"
sudo chown root:999 "$DB_ROOT/init/01-users.sql"
sudo chmod 640 "$DB_ROOT/init/01-users.sql"
```

### C. DB: levantar MySQL y validar root

Ejecutar en el servidor DB:

```bash
set -Eeuo pipefail
cd "$DB_ROOT"

sudo docker compose -f compose.yml up -d
sudo docker compose -f compose.yml ps

if sudo docker exec sisoc-mysql sh -lc 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -N -e "SELECT VERSION();"' >/dev/null 2>&1; then
  echo "root_mysql=ok"
else
  echo "root_mysql=fallo; usar seccion 5 para reset sin borrar datos"
  exit 1
fi
```

### D. DB: restaurar dump con backup preventivo

Ejecutar en el servidor DB despues de copiar el dump a `$DUMP_PATH`:

```bash
set -Eeuo pipefail
cd "$DB_ROOT"

gzip -t "$DUMP_PATH"
stamp=$(date +%Y%m%d_%H%M%S)
sudo mkdir -p "$DB_ROOT/backups"

if sudo docker exec sisoc-mysql sh -lc "mysql -uroot -p\"\$MYSQL_ROOT_PASSWORD\" -N -e \"SHOW DATABASES LIKE '$DB_NAME';\"" | grep -qx "$DB_NAME"; then
  sudo docker exec sisoc-mysql sh -lc \
    "mysqldump -uroot -p\"\$MYSQL_ROOT_PASSWORD\" --single-transaction --routines --triggers $DB_NAME" \
    | gzip -c | sudo tee "$DB_ROOT/backups/${DB_NAME}_pre_restore_${stamp}.sql.gz" >/dev/null
fi

sudo docker exec -i sisoc-mysql sh -lc 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' <<SQL
DROP DATABASE IF EXISTS \`$DB_NAME\`;
CREATE DATABASE \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SQL

gzip -dc "$DUMP_PATH" \
  | sudo docker exec -i sisoc-mysql sh -lc "mysql -uroot -p\"\$MYSQL_ROOT_PASSWORD\" --database=$DB_NAME"

sudo docker exec -i sisoc-mysql sh -lc 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' <"$DB_ROOT/init/01-users.sql"

sudo docker exec sisoc-mysql sh -lc \
  'MYSQL_PWD="$SISOC_DB_PASSWORD" mysql --ssl-mode=DISABLED -h127.0.0.1 -u"$SISOC_DB_USER" -D"$SISOC_DB_NAME" -N -e "SELECT DATABASE(); SELECT COUNT(*) FROM django_migrations;"'
```

### E. DB: firewall minimo

Ejecutar en el servidor DB:

```bash
sudo ufw allow OpenSSH
sudo ufw allow from "$SITE_IP" to any port 3306 proto tcp
sudo ufw status
```

Si ya habia reglas viejas de `3306`, revisarlas y borrar las que no correspondan:

```bash
sudo ufw status numbered
```

### F. SITE: variables del entorno

Ejecutar en el servidor SITE:

```bash
export ENV_NAME=qa
export SITE_IP=10.1.131.121
export DB_IP=10.1.130.88
export APP_USER=sisoc-deploy
export APP_ROOT=/opt/sisoc/SISOC
export GIT_BRANCH=development
export DB_NAME=sisoc_qa
export DB_APP_USER=djangoapp
export PUBLIC_ORIGIN=http://10.1.131.121
export PUBLIC_HOSTNAME=
```

Ingresar el password del usuario MySQL de Django sin dejarlo en el historial:

```bash
read -rsp "DB_APP_PASSWORD: " DB_APP_PASSWORD; echo
```

### G. SITE: branch correcta y `.env`

Ejecutar en el servidor SITE:

```bash
set -Eeuo pipefail

sudo -H -u "$APP_USER" git -C "$APP_ROOT" fetch origin --prune
sudo -H -u "$APP_USER" git -C "$APP_ROOT" checkout "$GIT_BRANCH"
sudo -H -u "$APP_USER" git -C "$APP_ROOT" pull --ff-only origin "$GIT_BRANCH"

sudo env \
  APP_ROOT="$APP_ROOT" \
  ENV_NAME="$ENV_NAME" \
  SITE_IP="$SITE_IP" \
  DB_IP="$DB_IP" \
  DB_NAME="$DB_NAME" \
  DB_APP_USER="$DB_APP_USER" \
  DB_APP_PASSWORD="$DB_APP_PASSWORD" \
  PUBLIC_ORIGIN="$PUBLIC_ORIGIN" \
  PUBLIC_HOSTNAME="$PUBLIC_HOSTNAME" \
  python3 - <<'PY'
from pathlib import Path
import os

app_root = Path(os.environ["APP_ROOT"])
public_origin = os.environ["PUBLIC_ORIGIN"].rstrip("/")
allowed_hosts = [os.environ["SITE_IP"], "127.0.0.1", "localhost"]
public_hostname = os.environ.get("PUBLIC_HOSTNAME", "").strip()
if public_hostname:
    allowed_hosts.append(public_hostname)

updates = {
    "DJANGO_DEBUG": "False",
    "ENVIRONMENT": os.environ["ENV_NAME"],
    "DJANGO_ALLOWED_HOSTS": ",".join(allowed_hosts),
    "DJANGO_CSRF_TRUSTED_ORIGINS": ",".join([public_origin, "http://127.0.0.1", "http://localhost"]),
    "DATABASE_HOST": os.environ["DB_IP"],
    "DATABASE_PORT": "3306",
    "DATABASE_USER": os.environ["DB_APP_USER"],
    "DATABASE_PASSWORD": os.environ["DB_APP_PASSWORD"],
    "DATABASE_NAME": os.environ["DB_NAME"],
    "WAIT_FOR_DB": "true",
    "RUN_MAKEMIGRATIONS_ON_START": "false",
    "DOMINIO": public_origin + "/",
}

env_path = app_root / ".env"
existing = env_path.read_text(errors="replace").splitlines() if env_path.exists() else []
seen = set()
out = []
for raw in existing:
    if raw.strip() and not raw.lstrip().startswith("#") and "=" in raw:
        key = raw.split("=", 1)[0].strip()
        if key in updates:
            out.append(f"{key}={updates[key]}")
            seen.add(key)
            continue
    out.append(raw)

for key, value in updates.items():
    if key not in seen:
        out.append(f"{key}={value}")

env_path.write_text("\n".join(out).rstrip() + "\n")
PY

sudo chown "$APP_USER:$APP_USER" "$APP_ROOT/.env"
sudo chmod 600 "$APP_ROOT/.env"
sudo -H -u "$APP_USER" git -C "$APP_ROOT" status -sb
```

### H. SITE: validar DB desde SITE

Ejecutar en el servidor SITE:

```bash
MYSQL_PWD="$DB_APP_PASSWORD" mysql --ssl=0 \
  -h"$DB_IP" -P3306 -u"$DB_APP_USER" -D"$DB_NAME" \
  -N -e "SELECT DATABASE(); SELECT COUNT(*) FROM django_migrations;"
```

### I. SITE: levantar SISOC

Ejecutar en el servidor SITE:

```bash
set -Eeuo pipefail
cd "$APP_ROOT"

if [ "${USE_PROD_OVERRIDE:-false}" = "true" ]; then
  sudo -H -u "$APP_USER" docker compose \
    -f docker-compose.deploy.yml \
    -f docker-compose.produccion.yml \
    up -d --build
else
  sudo -H -u "$APP_USER" docker compose -f docker-compose.deploy.yml up -d --build
fi

sudo -H -u "$APP_USER" docker compose -f docker-compose.deploy.yml ps
sudo -H -u "$APP_USER" docker compose -f docker-compose.deploy.yml logs --tail 200 django
```

En produccion validar con el mismo set de compose usado para levantar el servicio:

```bash
sudo -H -u "$APP_USER" docker compose \
  -f docker-compose.deploy.yml \
  -f docker-compose.produccion.yml \
  ps
```

Todo servicio definido por `docker-compose.produccion.yml` debe quedar arriba. En `origin/main` esto incluye `bulk_credentials_worker` y `ciudadanos_import_worker` ademas de `django`.

### J. SITE: configurar NGINX

Ejecutar en el servidor SITE:

```bash
set -Eeuo pipefail

server_names="$SITE_IP _"
if [ -n "${PUBLIC_HOSTNAME:-}" ]; then
  server_names="$SITE_IP $PUBLIC_HOSTNAME _"
fi

sudo tee "/etc/nginx/conf.d/sisoc-forwarded-proto.conf" >/dev/null <<'NGINX_MAP'
map $http_x_forwarded_proto $sisoc_forwarded_proto {
    default $http_x_forwarded_proto;
    ""      $scheme;
}
NGINX_MAP

sudo tee "/etc/nginx/sites-available/sisoc-$ENV_NAME" >/dev/null <<NGINX
server {
    listen 80;
    server_name $server_names;

    client_max_body_size 50m;

    access_log /var/log/nginx/sisoc-$ENV_NAME.access.log;
    error_log  /var/log/nginx/sisoc-$ENV_NAME.error.log;

    location /static/ {
        alias $APP_ROOT/static_root/;
        try_files \\$uri =404;
        access_log off;
        expires 7d;
    }

    location /media/ {
        alias $APP_ROOT/media/;
        try_files \\$uri =404;
        expires 1h;
    }

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;

        proxy_set_header Host \\$host;
        proxy_set_header X-Real-IP \\$remote_addr;
        proxy_set_header X-Forwarded-For \\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\$sisoc_forwarded_proto;

        proxy_connect_timeout 60s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
NGINX

sudo ln -sfn "/etc/nginx/sites-available/sisoc-$ENV_NAME" "/etc/nginx/sites-enabled/sisoc-$ENV_NAME"
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

Si PRD se prepara antes de apuntar DNS y emitir TLS, no configurar `listen 443` ni certificados todavia. Mantener el perfil `ENVIRONMENT=prd` y validar el backend HTTP enviando `X-Forwarded-Proto: https`; el HTTP plano directo puede responder `301` por `SECURE_SSL_REDIRECT`.

### K. SITE: firewall minimo

Ejecutar en el servidor SITE:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
# Solo cuando TLS quede implementado en este SITE:
# sudo ufw allow 443/tcp
sudo ufw status
```

### L. Validacion final copy-paste

Ejecutar en SITE:

```bash
set -Eeuo pipefail
cd "$APP_ROOT"

curl -i --max-time 20 http://127.0.0.1:8001/health/
curl -i --max-time 20 http://127.0.0.1/health/
curl -i --max-time 20 "$PUBLIC_ORIGIN/health/"
curl -i --max-time 20 -H "Host: ${PUBLIC_HOSTNAME:-$SITE_IP}" -H "X-Forwarded-Proto: https" http://127.0.0.1/health/

if [ "${USE_PROD_OVERRIDE:-false}" = "true" ]; then
  sudo -H -u "$APP_USER" docker compose \
    -f docker-compose.deploy.yml \
    -f docker-compose.produccion.yml \
    ps
else
  sudo -H -u "$APP_USER" docker compose -f docker-compose.deploy.yml ps
fi

if sudo -H -u "$APP_USER" docker compose -f docker-compose.deploy.yml logs --tail 500 django | grep -iE 'traceback|exception|\[error\]|error 1045|error 2061'; then
  echo "django_log_scan=found"
  exit 1
else
  echo "django_log_scan=none"
fi

sudo nginx -t
sudo tail -n 100 "/var/log/nginx/sisoc-$ENV_NAME.error.log" || true
```

En produccion, repetir el scan para los workers definidos por el override:

```bash
sudo -H -u "$APP_USER" docker compose \
  -f docker-compose.deploy.yml \
  -f docker-compose.produccion.yml \
  logs --tail 500 bulk_credentials_worker ciudadanos_import_worker | grep -iE 'traceback|exception|\[error\]' || true
```

Ejecutar en DB:

```bash
set -Eeuo pipefail
cd "$DB_ROOT"

sudo docker compose -f compose.yml ps
sudo docker exec sisoc-mysql sh -lc \
  'MYSQL_PWD="$SISOC_DB_PASSWORD" mysql --ssl-mode=DISABLED -h127.0.0.1 -u"$SISOC_DB_USER" -D"$SISOC_DB_NAME" -N -e "SELECT DATABASE(); SELECT COUNT(*) FROM django_migrations;"'

if sudo docker logs --tail 300 sisoc-mysql 2>&1 | grep -iE 'error|fatal|denied|failed'; then
  echo "mysql_log_scan=found"
  exit 1
else
  echo "mysql_log_scan=none"
fi
```

## 2. Reglas de seguridad

- No usar `docker compose down -v` en estos despliegues.
- No borrar `/opt/sisoc-mysql/data` ni volumenes MySQL.
- Antes de recrear o pisar una DB, hacer backup preventivo.
- No dejar `root` MySQL remoto abierto; si existe `root`@`%`, bloquearlo.
- No usar `source .env`: las claves pueden contener caracteres especiales. Parsear `.env` con scripts seguros o editar valores explicitamente.
- No imprimir secretos completos en tickets, chats ni reportes.
- Para DBeaver/VPN, crear usuarios especificos; no usar root.
- Firewall minimo:
  - SITE: SSH, `80/tcp` y `443/tcp` si aplica HTTPS.
  - DB: SSH y `3306/tcp` solo desde SITE y redes VPN aprobadas.

## 3. Preflight en ambos servidores

Ejecutar en SITE y DB:

```bash
hostname
whoami
pwd
id
cat /etc/os-release
systemctl is-active docker || true
systemctl is-active nginx || true
systemctl is-active mysql || true
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
docker compose ls
ufw status || true
```

Verificar rutas:

```bash
ls -ld /opt /opt/sisoc /opt/sisoc/SISOC 2>/dev/null || true
ls -ld /opt/sisoc-mysql 2>/dev/null || true
```

En SITE:

```bash
sudo -H -u "$APP_USER" git -C "$APP_ROOT" branch --show-current
sudo -H -u "$APP_USER" git -C "$APP_ROOT" rev-parse --short HEAD
sudo -H -u "$APP_USER" git -C "$APP_ROOT" status -sb
test -f "$APP_ROOT/.env" && ls -l "$APP_ROOT/.env"
```

Si hay contenedores de un compose equivocado, bajarlos sin volumenes:

```bash
cd "$APP_ROOT"
docker compose -f docker-compose.yml down
docker compose -f docker-compose.site.yml down
```

## 4. Preparar MySQL en DB

Crear estructura:

```bash
sudo mkdir -p "$DB_ROOT"/{data,conf,init,backups}
sudo chmod 700 "$DB_ROOT"
```

Crear `$DB_ROOT/compose.yml`:

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

Crear `$DB_ROOT/.env` con permisos `600`:

```dotenv
MYSQL_ROOT_PASSWORD=<ROOT_MYSQL_PASSWORD>
SISOC_DB_NAME=<DB_NAME>
SISOC_DB_USER=<DB_APP_USER>
SISOC_DB_PASSWORD=<DB_APP_PASSWORD>
```

Crear `$DB_ROOT/init/01-users.sql` con permisos `640` y grupo `999` para que el usuario `mysql` del contenedor pueda leerlo al inicializar. Mantener `$DB_ROOT/.env` con permisos `600`:

```sql
CREATE USER IF NOT EXISTS '<DB_APP_USER>'@'%' IDENTIFIED WITH mysql_native_password BY '<DB_APP_PASSWORD>';
ALTER USER '<DB_APP_USER>'@'%' IDENTIFIED WITH mysql_native_password BY '<DB_APP_PASSWORD>';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, INDEX, REFERENCES,
      CREATE TEMPORARY TABLES, LOCK TABLES, TRIGGER
ON `<DB_NAME>`.* TO '<DB_APP_USER>'@'%';
FLUSH PRIVILEGES;
```

Levantar:

```bash
cd "$DB_ROOT"
sudo docker compose -f compose.yml up -d
sudo docker compose -f compose.yml ps
```

## 5. Si root MySQL no autentica

Usar este procedimiento solo si `root` no entra aunque `$DB_ROOT/.env` tenga el valor esperado. No borra datos.

```bash
cd "$DB_ROOT"
sudo docker stop sisoc-mysql
sudo docker run --rm -d --name sisoc-mysql-recover --network none \
  -v "$DB_ROOT/data:/var/lib/mysql" \
  -v "$DB_ROOT/conf:/etc/mysql/conf.d:ro" \
  mysql:8.0 \
  --skip-grant-tables --skip-networking \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci \
  --default-time-zone=-03:00
```

Generar SQL temporal sin `source .env`:

```bash
sudo python3 - <<'PY' >/tmp/reset-root.sql
from pathlib import Path

env_path = Path("/opt/sisoc-mysql/.env")
vals = {}
for raw in env_path.read_text(errors="replace").splitlines():
    if "=" not in raw or raw.strip().startswith("#"):
        continue
    key, value = raw.split("=", 1)
    vals[key.strip()] = value.strip().strip('"').strip("'")

def sql_quote(value):
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"

root_password = vals["MYSQL_ROOT_PASSWORD"]
print("FLUSH PRIVILEGES;")
print("ALTER USER IF EXISTS 'root'@'localhost' IDENTIFIED BY " + sql_quote(root_password) + ";")
print("ALTER USER IF EXISTS 'root'@'127.0.0.1' IDENTIFIED BY " + sql_quote(root_password) + ";")
print("ALTER USER IF EXISTS 'root'@'::1' IDENTIFIED BY " + sql_quote(root_password) + ";")
print("ALTER USER IF EXISTS 'root'@'%' IDENTIFIED BY " + sql_quote(root_password) + " ACCOUNT LOCK;")
print("FLUSH PRIVILEGES;")
PY

sudo docker exec -i sisoc-mysql-recover mysql -uroot </tmp/reset-root.sql
rm -f /tmp/reset-root.sql
sudo docker stop sisoc-mysql-recover
sudo docker compose -f compose.yml up -d
```

Validar:

```bash
sudo docker exec sisoc-mysql sh -lc \
  'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -N -e "SELECT User, Host, plugin, account_locked FROM mysql.user WHERE User IN (\"root\", \"djangoapp\") ORDER BY User, Host;"'
```

## 6. Restaurar dump

Colocar el dump comprimido en:

```text
$DB_ROOT/dump.sql.gz
```

Validar integridad:

```bash
gzip -t "$DB_ROOT/dump.sql.gz"
```

Backup preventivo:

```bash
cd "$DB_ROOT"
stamp=$(date +%Y%m%d_%H%M%S)
sudo mkdir -p backups
if sudo docker exec sisoc-mysql sh -lc "mysql -uroot -p\"\$MYSQL_ROOT_PASSWORD\" -N -e \"SHOW DATABASES LIKE '$DB_NAME';\"" | grep -qx "$DB_NAME"; then
  sudo docker exec sisoc-mysql sh -lc \
    "mysqldump -uroot -p\"\$MYSQL_ROOT_PASSWORD\" --single-transaction --routines --triggers $DB_NAME" \
    | gzip -c | sudo tee "backups/${DB_NAME}_pre_restore_${stamp}.sql.gz" >/dev/null
fi
```

Recrear DB e importar:

```bash
sudo docker exec -i sisoc-mysql sh -lc 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' <<SQL
DROP DATABASE IF EXISTS \`$DB_NAME\`;
CREATE DATABASE \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SQL

gzip -dc "$DB_ROOT/dump.sql.gz" \
  | sudo docker exec -i sisoc-mysql sh -lc "mysql -uroot -p\"\$MYSQL_ROOT_PASSWORD\" --database=$DB_NAME"
```

Aplicar usuario y grants:

```bash
sudo docker exec -i sisoc-mysql sh -lc 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' <"$DB_ROOT/init/01-users.sql"
```

Validar acceso app:

```bash
sudo docker exec sisoc-mysql sh -lc \
  'MYSQL_PWD="$SISOC_DB_PASSWORD" mysql --ssl-mode=DISABLED -h127.0.0.1 -u"$SISOC_DB_USER" -D"$SISOC_DB_NAME" -N -e "SELECT DATABASE(); SELECT COUNT(*) FROM django_migrations;"'
```

## 7. Preparar SITE

Clonar si falta:

```bash
sudo mkdir -p "$(dirname "$APP_ROOT")"
sudo chown "$APP_USER:$APP_USER" "$(dirname "$APP_ROOT")"
sudo -H -u "$APP_USER" git clone git@github-sisoc:dsocial118/SISOC.git "$APP_ROOT"
```

Actualizar branch:

```bash
sudo -H -u "$APP_USER" git -C "$APP_ROOT" fetch origin --prune
sudo -H -u "$APP_USER" git -C "$APP_ROOT" checkout "$GIT_BRANCH"
sudo -H -u "$APP_USER" git -C "$APP_ROOT" pull --ff-only origin "$GIT_BRANCH"
sudo -H -u "$APP_USER" git -C "$APP_ROOT" status -sb
```

Crear `$APP_ROOT/.env` con permisos `600`:

```dotenv
DJANGO_DEBUG=False
ENVIRONMENT=<ENV_NAME>
DJANGO_ALLOWED_HOSTS=<SITE_IP>,127.0.0.1,localhost,<PUBLIC_HOSTNAME>
DJANGO_CSRF_TRUSTED_ORIGINS=<PUBLIC_ORIGIN>,http://127.0.0.1,http://localhost
DATABASE_HOST=<DB_IP>
DATABASE_PORT=3306
DATABASE_USER=<DB_APP_USER>
DATABASE_PASSWORD=<DB_APP_PASSWORD>
DATABASE_NAME=<DB_NAME>
WAIT_FOR_DB=true
RUN_MAKEMIGRATIONS_ON_START=false
DOMINIO=<PUBLIC_ORIGIN>/
```

En PRD no desactivar el hardening HTTPS aunque el servidor se prepare antes del cambio de DNS/TLS. Mantener `ENVIRONMENT=prd`, no agregar overrides `DJANGO_SECURE_*` y validar NGINX con `X-Forwarded-Proto: https`. Si el request llega por HTTP plano directo, `/health/` puede redirigir por `SECURE_SSL_REDIRECT`.

Para un entorno temporal no PRD controlado por HTTP interno, y solo si se acepta explicitamente perder el hardening de HTTPS, se pueden agregar estos overrides al `.env` del servidor. No usarlos para PRD ni para un dominio con TLS real:

```dotenv
DJANGO_SECURE_SSL_REDIRECT=False
DJANGO_SESSION_COOKIE_SECURE=False
DJANGO_CSRF_COOKIE_SECURE=False
DJANGO_SECURE_HSTS_SECONDS=0
```

Permisos:

```bash
sudo chown "$APP_USER:$APP_USER" "$APP_ROOT/.env"
sudo chmod 600 "$APP_ROOT/.env"
```

Validar DB desde SITE:

```bash
MYSQL_PWD='<DB_APP_PASSWORD>' mysql --ssl=0 \
  -h"$DB_IP" -P3306 -u"$DB_APP_USER" -D"$DB_NAME" \
  -N -e "SELECT DATABASE(); SELECT COUNT(*) FROM django_migrations;"
```

## 8. Levantar aplicacion

QA y homologacion:

```bash
cd "$APP_ROOT"
sudo -H -u "$APP_USER" docker compose -f docker-compose.deploy.yml up -d --build
```

Produccion, si corresponde el worker adicional:

```bash
cd "$APP_ROOT"
sudo -H -u "$APP_USER" docker compose \
  -f docker-compose.deploy.yml \
  -f docker-compose.produccion.yml \
  up -d --build
```

En produccion, revisar `ps` y logs con el mismo set de compose:

```bash
sudo -H -u "$APP_USER" docker compose \
  -f docker-compose.deploy.yml \
  -f docker-compose.produccion.yml \
  ps
sudo -H -u "$APP_USER" docker compose \
  -f docker-compose.deploy.yml \
  -f docker-compose.produccion.yml \
  logs --tail 200 django bulk_credentials_worker ciudadanos_import_worker
```

Todo worker definido por `docker-compose.produccion.yml` debe quedar arriba. En `origin/main` esto incluye `bulk_credentials_worker` y `ciudadanos_import_worker`.

Revisar logs hasta Gunicorn:

```bash
sudo -H -u "$APP_USER" docker compose -f docker-compose.deploy.yml logs -f --tail 200 django
```

Salida esperada:

```text
[skip] Omitiendo makemigrations en arranque (flag desactivado).
[run] migrate: python manage.py migrate --noinput
[server] Iniciando Django en modo produccion con Gunicorn...
Listening at: http://0.0.0.0:8000
```

## 9. Configurar NGINX

Crear el map HTTP para preservar `X-Forwarded-Proto` cuando exista un LB/TLS upstream. Esto permite preparar PRD con backend HTTP sin desactivar el hardening de Django:

```nginx
map $http_x_forwarded_proto $sisoc_forwarded_proto {
    default $http_x_forwarded_proto;
    ""      $scheme;
}
```

Por ejemplo:

```bash
sudo tee /etc/nginx/conf.d/sisoc-forwarded-proto.conf >/dev/null <<'NGINX_MAP'
map $http_x_forwarded_proto $sisoc_forwarded_proto {
    default $http_x_forwarded_proto;
    ""      $scheme;
}
NGINX_MAP
```

Crear `/etc/nginx/sites-available/sisoc-$ENV_NAME`. Si no hay hostname publico, quitar `<PUBLIC_HOSTNAME>` de `server_name`:

```nginx

server {
    listen 80;
    server_name <SITE_IP> <PUBLIC_HOSTNAME> _;

    client_max_body_size 50m;

    access_log /var/log/nginx/sisoc-<ENV_NAME>.access.log;
    error_log  /var/log/nginx/sisoc-<ENV_NAME>.error.log;

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
        proxy_set_header X-Forwarded-Proto $sisoc_forwarded_proto;

        proxy_connect_timeout 60s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

Habilitar:

```bash
sudo ln -sfn "/etc/nginx/sites-available/sisoc-$ENV_NAME" "/etc/nginx/sites-enabled/sisoc-$ENV_NAME"
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

Si `nginx -t` advierte `conflicting server name`, buscar duplicados:

```bash
sudo grep -RInE 'server_name|listen 80|sites-enabled' /etc/nginx
```

Debe existir un solo include activo de `/etc/nginx/sites-enabled/*` en `nginx.conf`.

Si PRD se prepara antes de apuntar DNS y emitir TLS, dejar solo HTTP en SITE hasta el corte. No crear `listen 443` ni referenciar certificados inexistentes. La validacion debe usar `X-Forwarded-Proto: https` para simular la futura terminacion TLS sin desactivar el hardening de Django.

## 10. Firewall

SITE:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
# Solo cuando TLS quede implementado en este SITE:
# sudo ufw allow 443/tcp
sudo ufw status
```

DB:

```bash
sudo ufw allow OpenSSH
sudo ufw allow from "$SITE_IP" to any port 3306 proto tcp
sudo ufw status
```

VPN o bastion, si aplica:

```bash
sudo ufw allow from <VPN_CIDR> to any port 3306 proto tcp
```

## 11. Validacion tecnica final

En SITE:

```bash
curl -i "http://127.0.0.1:8001/health/"
curl -i "http://127.0.0.1/health/"
curl -i "$PUBLIC_ORIGIN/health/"
curl -i -H "Host: ${PUBLIC_HOSTNAME:-$SITE_IP}" -H "X-Forwarded-Proto: https" "http://127.0.0.1/health/"
if [ "${USE_PROD_OVERRIDE:-false}" = "true" ]; then
  sudo -H -u "$APP_USER" docker compose -f "$APP_ROOT/docker-compose.deploy.yml" -f "$APP_ROOT/docker-compose.produccion.yml" ps
  sudo -H -u "$APP_USER" docker compose -f "$APP_ROOT/docker-compose.deploy.yml" -f "$APP_ROOT/docker-compose.produccion.yml" logs --tail 500 django bulk_credentials_worker ciudadanos_import_worker | grep -iE 'traceback|exception|\[error\]' || true
else
  sudo -H -u "$APP_USER" docker compose -f "$APP_ROOT/docker-compose.deploy.yml" ps
  sudo -H -u "$APP_USER" docker compose -f "$APP_ROOT/docker-compose.deploy.yml" logs --tail 500 django | grep -iE 'traceback|exception|\[error\]' || true
fi
sudo nginx -t
sudo tail -n 100 "/var/log/nginx/sisoc-$ENV_NAME.error.log"
```

En DB:

```bash
cd "$DB_ROOT"
sudo docker compose -f compose.yml ps
sudo docker exec sisoc-mysql sh -lc \
  'MYSQL_PWD="$SISOC_DB_PASSWORD" mysql --ssl-mode=DISABLED -h127.0.0.1 -u"$SISOC_DB_USER" -D"$SISOC_DB_NAME" -N -e "SELECT DATABASE(); SELECT COUNT(*) FROM django_migrations;"'
sudo docker logs --tail 300 sisoc-mysql | grep -iE 'error|fatal|denied|failed' || true
```

## 12. Smoke funcional recomendado

Despues del health tecnico:

1. Entrar por navegador al dominio/IP del entorno.
2. Validar login con usuario operativo del entorno.
3. Abrir una pantalla con estaticos pesados para confirmar `/static/`.
4. Subir o visualizar un archivo de prueba si el entorno usa `/media/`.
5. Ejecutar un flujo de lectura critico del modulo que se va a probar.
6. Confirmar que no hay tracebacks nuevos en logs Django.
7. Confirmar con el responsable funcional si se habilitan integraciones externas reales.

## 13. Operacion diaria

Reiniciar app:

```bash
cd "$APP_ROOT"
sudo -H -u "$APP_USER" docker compose -f docker-compose.deploy.yml restart django
```

Deploy de nuevo commit:

```bash
cd "$APP_ROOT"
sudo -H -u "$APP_USER" git pull --ff-only origin "$GIT_BRANCH"
sudo -H -u "$APP_USER" docker compose -f docker-compose.deploy.yml up -d --build
```

Logs:

```bash
cd "$APP_ROOT"
sudo -H -u "$APP_USER" docker compose -f docker-compose.deploy.yml logs -f --tail 200 django
sudo tail -f "/var/log/nginx/sisoc-$ENV_NAME.error.log"
```

Backup manual:

```bash
cd "$DB_ROOT"
stamp=$(date +%Y%m%d_%H%M%S)
sudo docker exec sisoc-mysql sh -lc \
  'mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction --routines --triggers "$SISOC_DB_NAME"' \
  | gzip -c | sudo tee "backups/${DB_NAME}_${stamp}.sql.gz" >/dev/null
```

## 14. Criterio de cierre

El entorno queda listo cuando:

- Branch correcta desplegada.
- Compose correcto en uso.
- DB restaurada o creada con backup previo si correspondia.
- Usuario app tiene permisos sobre su DB y no usa root.
- Firewall limita MySQL al SITE y redes aprobadas.
- `/health/` responde directo y por NGINX.
- Logs Django y MySQL no muestran tracebacks ni errores nuevos.
- El smoke funcional minimo fue ejecutado o queda registrado como pendiente explicito.
