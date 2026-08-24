# Corrección de expedientes del issue #2272

## Alcance y prohibiciones

Este runbook ejecuta el comando
`corregir_expedientes_issue_2272` sobre admisiones ya existentes. Actualiza
únicamente `num_expediente` y `legales_num_if`; no modifica `num_if`, estados ni
documentos ya generados.

El manifiesto versionado se deriva de la fuente funcional
`CORRECCIONES EXPEDIENTES - Hoja 2.csv`. Por indicación funcional explícita,
los números de siete u ocho dígitos fueron completados con ceros a la izquierda
hasta nueve dígitos. La fuente contiene 470 admisiones únicas. No existe una
regla especial de exclusión: como las admisiones 1448, 1794, 2314 y 2462 no
figuran en el manifiesto, el comando simplemente las deja intactas.

El CSV prevalece, con autorización operativa, sobre cuatro ocupaciones
históricas detectadas en PRD: el comando libera ambos campos de 1627, 1490,
1218 y 842 para asignar los expedientes a 2072, 2469, 2052 y 802. Cualquier
otra colisión continúa bloqueando el preflight. La aplicación y `--verify`
registran y comprueban esas liberaciones.

No existe ni debe improvisarse una opción `--manifest` en el host. Cualquier
nueva fuente requiere un cambio revisado que actualice el CSV y
`manifest_sha256` antes de desplegarse.

## Precondiciones obligatorias

- Cambio aprobado, desplegado y con el SHA completo registrado en la ventana.
- Responsable funcional e infraestructura disponibles durante la ejecución.
- Ventana con altas y ediciones de admisiones detenidas.
- Backup recuperable de la base objetivo, tomado inmediatamente antes, con su
  identificador o ubicación registrado en el ticket de cambio.
- Preflight exitoso en HML con el mismo manifiesto (mismo checksum normalizado)
  que se desplegará en producción. Los commits pueden diferir porque HML usa
  `homologacion` y PRD usa `main`; debe registrarse el SHA de cada entorno.

Si alguna condición no se cumple, detenerse: no ejecutar `--apply`.

## Preflight en HML

Ejecutar como el operador autorizado en `hml-old`. Reemplazar los valores
solicitados; no ejecutar `--apply` en este bloque.

```bash
set -euo pipefail

APP_ROOT=/sisoc/SISOC
APP_CONTAINER=sisoc-django-1
EXPECTED_HML_SHA='<SHA_COMPLETO_DESPLEGADO_EN_HML>'
EXPECTED_MANIFEST_SHA='<CHECKSUM_VERSIONADO_DE_64_HEX>'

[[ "$(hostname -s)" == "ldmzssies-homolo" ]]
[[ "$EXPECTED_HML_SHA" =~ ^[0-9a-f]{40}$ ]]
[[ "$EXPECTED_MANIFEST_SHA" =~ ^[0-9A-F]{64}$ ]]
test "$(git -C "$APP_ROOT" branch --show-current)" = "homologacion"
git -C "$APP_ROOT" diff --quiet
git -C "$APP_ROOT" diff --cached --quiet
test "$(git -C "$APP_ROOT" rev-parse HEAD)" = "$EXPECTED_HML_SHA"

docker exec "$APP_CONTAINER" python manage.py shell -c \
  "from django.db import connection; connection.ensure_connection(); c=connection.cursor(); c.execute('SELECT @@hostname, DATABASE()'); host, database=c.fetchone(); c.close(); assert str(connection.settings_dict.get('HOST')) == '10.80.5.48'; assert host == 'ldmzsql-homolo'; assert database == 'sisoc_local'; print('hml_db_preflight=ok')"

docker exec "$APP_CONTAINER" python manage.py shell -c \
  "from admisiones.management.commands.corregir_expedientes_issue_2272 import Command; assert Command.manifest_sha256 == '$EXPECTED_MANIFEST_SHA'; print('manifest_checksum=ok')"

docker exec "$APP_CONTAINER" python manage.py \
  corregir_expedientes_issue_2272 --database default
```

El comando debe terminar con `Preflight correcto` y sin errores. Conservar la
salida y el checksum para compararlos con producción.

## Ejecución en producción

Los valores de este bloque corresponden al entorno canónico documentado en
`docs/infra/ENVIRONMENT_DATABASES.md`. Ejecutar como el operador autorizado en
`prd-old`; definir las cuatro variables de control antes de comenzar.

```bash
set -euo pipefail

APP_ROOT=/sisoc/SISOC
APP_CONTAINER=sisoc-django-1
EXPECTED_SHA='<SHA_COMPLETO_APROBADO>'
EXPECTED_MANIFEST_SHA='<CHECKSUM_VALIDADO_EN_HML_DE_64_HEX>'
: "${CHANGE_TICKET:?Definir ticket de cambio aprobado}"
: "${BACKUP_REFERENCE:?Definir backup recuperable confirmado}"
echo 'ticket y backup recuperable confirmados'

[[ "$(hostname -s)" == "mdsldmz-ssies" ]]
[[ "$EXPECTED_SHA" =~ ^[0-9a-f]{40}$ ]]
[[ "$EXPECTED_MANIFEST_SHA" =~ ^[0-9A-F]{64}$ ]]
test "$(git -C "$APP_ROOT" branch --show-current)" = "main"
git -C "$APP_ROOT" diff --quiet
git -C "$APP_ROOT" diff --cached --quiet
test "$(git -C "$APP_ROOT" rev-parse HEAD)" = "$EXPECTED_SHA"

docker exec "$APP_CONTAINER" python manage.py shell -c \
  "from django.db import connection; connection.ensure_connection(); c=connection.cursor(); c.execute('SELECT @@hostname, DATABASE()'); host, database=c.fetchone(); c.close(); assert str(connection.settings_dict.get('HOST')) == '10.80.5.46'; assert host == 'ldmzsql-sisoc'; assert database == 'sisoc_local'; print('prd_db_preflight=ok')"

docker exec "$APP_CONTAINER" python manage.py shell -c \
  "from admisiones.management.commands.corregir_expedientes_issue_2272 import Command; assert Command.manifest_sha256 == '$EXPECTED_MANIFEST_SHA'; print('manifest_checksum=ok')"

docker exec "$APP_CONTAINER" python manage.py \
  corregir_expedientes_issue_2272 --database default
```

El último comando debe terminar con `Preflight correcto` y sin errores. Si no
ocurre, detenerse y adjuntar la salida al ticket; no intentar corregir filas ni
forzar el comando desde SQL.

Con el GO explícito de la ventana y sin reanudar escrituras, aplicar y verificar:

```bash
docker exec "$APP_CONTAINER" python manage.py \
  corregir_expedientes_issue_2272 --apply --database default

docker exec "$APP_CONTAINER" python manage.py \
  corregir_expedientes_issue_2272 --verify --database default
```

La aplicación debe informar el total de admisiones e historiales creados. La
verificación debe terminar con `Verificación #2272 correcta`; comprueba que los
campos de Técnicos y Legales coinciden con el manifiesto aprobado.

## Recuperación

Un error durante `--apply` revierte su propia transacción: no reintentar sin
analizar el preflight. Si `--apply` terminó y la verificación posterior falla,
mantener el freeze de escrituras, preservar la salida del comando y escalar al
responsable. La recuperación se realiza con el backup aprobado o con un nuevo
manifiesto inverso, revisado y desplegado; no ejecutar SQL manual ni reutilizar
el CSV rechazado.
