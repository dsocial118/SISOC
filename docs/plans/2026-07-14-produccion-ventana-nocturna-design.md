# Produccion: ejecucion nocturna preparada

Estado: paquete preparado; no ejecutado en `prd-old`.

Host canonico: `10.80.5.45` / `mdsldmz-ssies`. Los hosts AWS quedan fuera. TLS
queda excluido por decision explicita.

## Resultado buscado

Al cerrar la ventana:

- `main` esta desplegado en backend y SISOC-Mobile;
- QA y HML contienen todo `main` por el Plan A y sus deploys estan verdes;
- los siete contenedores productivos, NGINX y runner estan sanos;
- Django usa exclusivamente MySQL remoto `10.80.5.46`;
- el MySQL local queda inactivo/deshabilitado, con datadir/paquetes intactos;
- la poda root con `--volumes` y dos cron legacy rotos ya no existen;
- `sisoc-deploy` tiene una limpieza diaria por umbral, retencion 14 dias y sin
  volumenes;
- los logs NGINX bajo `/sisoc` tienen rotacion;
- `.env` mobile queda `root:sisoc-deploy` modo 640;
- `apache2` y `sisoc.service` quedan disabled, sin borrar unidades/paquetes;
- existe backup root-only y rollback exacto de cada cambio host-side.

## Cambios que deben llegar a `main` antes de la ventana

Integrar en este orden y esperar checks verdes:

1. PR #2058: Plan A y remote HTTPS de SISOC-Mobile.
2. PR #2059: hardening atomico de asistencia CDI.
3. PR del paquete nocturno de produccion que contiene este documento.

Cada merge a `main` crea un deploy productivo en espera. No aprobar ninguno
durante la preparacion. El Plan A debe integrar `main` en `development` y
`homologacion`, y los deploys QA/HML deben terminar verdes antes del GO de PRD.

Invariantes Git finales:

```bash
git fetch origin --prune
git merge-base --is-ancestor origin/main origin/development
git merge-base --is-ancestor origin/main origin/homologacion
```

## Alcance de los scripts

| Script | Comportamiento por defecto | Mutacion autorizable |
| --- | --- | --- |
| `prod_night_preflight.sh` | read-only | ninguna |
| `backup_prod_configs.sh` | crea backup root-only | solo backup |
| `prepare_prod_mobile_checkout.sh` | audita checkout/remote | `--apply` alinea owner y HTTPS |
| `install_prod_maintenance.sh` | preflight read-only | `--apply` cambia cron/logrotate/permisos/enablement |
| `cleanup_prod_disk.sh` | informa | `--apply` poda solo si `/ >= 80%` |
| `retire_prod_local_mysql_stage1.sh` | preflight read-only | `--apply` stop+disable local |
| `healthcheck_prod.sh` | read-only | ninguna |
| `verify_prod_release.sh` | read-only | ninguna |
| `rollback_prod_maintenance.sh` | informa | `--apply` restaura backup host-side |
| `rollback_prod_mobile_checkout.sh` | informa | `--apply` restaura owners/ACL y remote |

Ningun script ejecuta `docker volume prune`, `docker system prune`,
`down --volumes`, DROP, purge de paquetes, borrado de media/checkouts/backups o
cambios TLS.

## Preparar el paquete en el servidor sin tocar el checkout activo

Despues de los tres merges, registrar los SHA objetivo:

```bash
sudo -u sisoc-deploy git -C /sisoc/SISOC fetch origin main --prune
TARGET_BACKEND_SHA="$(sudo -u sisoc-deploy git -C /sisoc/SISOC rev-parse origin/main)"
TARGET_MOBILE_SHA="$(git ls-remote https://github.com/dsocial118/SISOC-Mobile.git refs/heads/main | awk '{print $1}')"
printf 'backend=%s\nmobile=%s\n' "$TARGET_BACKEND_SHA" "$TARGET_MOBILE_SHA"
```

Extraer solo scripts versionados desde el commit objetivo, sin switch/pull:

```bash
PACKAGE_ROOT=/root/sisoc-prod-night-package
sudo install -d -o root -g root -m 700 "$PACKAGE_ROOT"
sudo -u sisoc-deploy git -C /sisoc/SISOC archive \
  "$TARGET_BACKEND_SHA" scripts/infra \
  | sudo tar -x -C "$PACKAGE_ROOT"
sudo find "$PACKAGE_ROOT" -type d -exec chmod 700 {} +
sudo find "$PACKAGE_ROOT/scripts/infra" -type f -name '*.sh' -exec chmod 700 {} +
sudo bash -n "$PACKAGE_ROOT"/scripts/infra/*prod*.sh
```

No copiar `.env` al paquete ni imprimirlo.

## Gate 0 - No-go y preflight read-only

Antes de las 22:00 ART confirmar externamente:

- backup DB vigente y restore probado o evidencia aceptada;
- snapshot media `/sisoc/backups/media/20260713_172352` completo;
- sin importaciones, credenciales masivas ni mailings activos;
- operador, validador y aprobador del Environment disponibles;
- ningun deploy en ejecucion;
- HML verde con el mismo `main`.

En PRD:

```bash
sudo bash "$PACKAGE_ROOT/scripts/infra/prod_night_preflight.sh"
```

Abortar si no termina exactamente con `PROD NIGHT PREFLIGHT: OK`. El script
exige host correcto, 100 GiB libres, uso menor a 80%, Git tracked limpio,
branches `main`, Compose valido, siete contenedores, health/DB remota, cero
restart counts y preflights exactos de cron/MySQL.

## Gate 1 - Preparar checkout de SISOC-Mobile

El read-only del 2026-07-14 confirmo que el checkout mobile pertenece al usuario
historico `admin-ssies`, usa el origin SSH esperado y `sisoc-deploy` no puede
operarlo. HML ya usa ownership del runner. Sin corregir esto, el primer deploy
productivo automatico fallaria antes de actualizar mobile.

Preflight sin cambios:

```bash
sudo bash "$PACKAGE_ROOT/scripts/infra/prepare_prod_mobile_checkout.sh"
```

Con GO explicito para el cambio recursivo de owner **solo en
`/sisoc/SISOC-Mobile`**:

```bash
sudo bash "$PACKAGE_ROOT/scripts/infra/prepare_prod_mobile_checkout.sh" \
  --apply --yes
```

El script guarda ACL, owners, grupos y modos de las 866 entradas observadas,
preserva la metadata previa de `.env`, cambia el checkout a
`sisoc-deploy:sisoc-deploy`, normaliza origin a HTTPS publica y valida un fetch
sin mover HEAD. Registrar `MOBILE_BACKUP_DIR` con el `BACKUP_DIR` informado.

Rollback exacto:

```bash
sudo bash "$PACKAGE_ROOT/scripts/infra/rollback_prod_mobile_checkout.sh" \
  --backup-dir "$MOBILE_BACKUP_DIR"
sudo bash "$PACKAGE_ROOT/scripts/infra/rollback_prod_mobile_checkout.sh" \
  --backup-dir "$MOBILE_BACKUP_DIR" --apply --yes
```

## Gate 2 - Mantenimiento host-side

Aplicar con backup y rollback automatico ante un error:

```bash
sudo bash "$PACKAGE_ROOT/scripts/infra/install_prod_maintenance.sh" \
  --apply --yes --rotate-logs-now
```

Registrar el `BACKUP_DIR` informado. El bloque:

1. guarda configuracion, cron, Git/Docker metadata y copia sensible root-only;
2. retira exactamente tres lineas root conocidas: poda con `--volumes` y dos
   paths inexistentes;
3. instala limpieza diaria 03:40 como `sisoc-deploy`, umbral 80% y retencion
   336h; en el baseline actual no poda porque el disco esta muy por debajo;
4. instala y aplica solo `/etc/logrotate.d/sisoc-nginx`;
5. cambia solo owner/grupo/modo de `.env` mobile;
6. deshabilita servicios legacy solo si no estaban activos;
7. valida health como root y como `sisoc-deploy`.

Verificar de nuevo:

```bash
sudo bash "$PACKAGE_ROOT/scripts/infra/healthcheck_prod.sh"
sudo -u sisoc-deploy /home/sisoc-deploy/bin/cleanup_prod_disk.sh
sudo crontab -l | grep -Fc -- '--volumes'
sudo crontab -u sisoc-deploy -l
sudo logrotate -d /etc/logrotate.d/sisoc-nginx
```

Resultado esperado: health OK, cleanup informativo, conteo `--volumes=0` y una
sola entrada de cleanup productivo. Observar 15 minutos.

Rollback host-side:

```bash
sudo bash "$PACKAGE_ROOT/scripts/infra/rollback_prod_maintenance.sh" \
  --backup-dir "$BACKUP_DIR"
sudo bash "$PACKAGE_ROOT/scripts/infra/rollback_prod_maintenance.sh" \
  --backup-dir "$BACKUP_DIR" --apply --yes
```

La primera linea solo muestra el plan. La segunda restaura crons, `.env`,
logrotate, scripts y enablement; no deshace archivos de log ya rotados.

## Gate 3 - Stage 1 del MySQL local

Repetir preflight inmediatamente antes de detener:

```bash
sudo bash "$PACKAGE_ROOT/scripts/infra/retire_prod_local_mysql_stage1.sh"
```

Debe confirmar DB remota correcta y cinco conteos locales en cero. Aplicar:

```bash
sudo bash "$PACKAGE_ROOT/scripts/infra/retire_prod_local_mysql_stage1.sh" \
  --apply --yes
```

Conserva `/var/lib/mysql`, `/etc/mysql` y paquetes por 14 dias. Rollback
inmediato si falla health, DB identity o aparece un consumidor:

```bash
sudo systemctl enable --now mysql
sudo systemctl show mysql -p ActiveState -p UnitFileState --no-pager
sudo ss -Hlnpt 'sport = :3306'
```

Observar 30 minutos y ejecutar:

```bash
sudo bash "$PACKAGE_ROOT/scripts/infra/prod_night_preflight.sh" --skip-mysql
```

## Gate 4 - Elegir un unico deploy de produccion

Listar los runs de `main`:

```bash
gh run list --repo dsocial118/SISOC --workflow deploy.yml --branch main \
  --limit 20 --json databaseId,headSha,status,conclusion,createdAt,url
```

Cancelar todos los runs productivos anteriores al que tenga
`headSha=$TARGET_BACKEND_SHA`:

```bash
gh run cancel RUN_ID_ANTERIOR --repo dsocial118/SISOC
```

No cancelar el run objetivo. Repetir Gate 0/health, confirmar que no aparecieron
nuevos commits y aprobar **solo ese run** en el Environment `production`.

```bash
gh run watch RUN_ID_OBJETIVO --repo dsocial118/SISOC --exit-status
```

El deploy baja/levanta backend y mobile sin volumenes, hace pulls `--ff-only` y
puede ejecutar migraciones del entrypoint. La DB y media ya deben estar
respaldadas antes de aprobar.

## Gate 5 - Verificacion final

```bash
sudo bash "$PACKAGE_ROOT/scripts/infra/verify_prod_release.sh" \
  --backend-sha "$TARGET_BACKEND_SHA" \
  --mobile-sha "$TARGET_MOBILE_SHA"
```

Ademas, con un usuario autorizado y sin crear datos ficticios:

- login;
- detalle CDI, nomina y asistencia;
- confirmar que observaciones es editable;
- static y un media existente;
- workers presentes, sin reprocesamiento inesperado;
- logs NGINX creciendo con owner/modo esperados.

Observar 40 minutos. Cerrar solo con `PROD RELEASE VERIFICATION: OK` y smoke
funcional aceptado.

## Rollback del deploy

Antes de aprobar, registrar commits e imagenes previos desde el backup. Si el
build falla despues del `down`, recuperar primero servicio con las imagenes
anteriores; no podar durante la ventana. El rollback definitivo de codigo se
hace mediante revert PR, nunca con force-push o `git reset --hard`.

No desmigrar automaticamente `0036_asistenciatrabajador`: eliminar la tabla
podria perder asistencias ya creadas. Revertir codigo manteniendo la tabla es el
rollback seguro inicial; cualquier desmigracion requiere aprobacion de datos.

## Evidencia de cierre

Guardar root-only y resumir sin secretos:

- SHA backend/mobile y run objetivo;
- `BACKUP_DIR` de mantenimiento y MySQL;
- hora/resultado de cada gate;
- cron y servicios antes/despues;
- disco, contenedores/restart counts y health;
- DB identity y migracion aplicada;
- cambios omitidos, rollback usado y periodo de observacion.

## Exclusiones y seguimiento

- TLS sigue fuera.
- No se borra datadir/paquetes MySQL antes de 14 dias y nueva aprobacion.
- No se borra media, backups, checkouts historicos, `tmp/`, logs de aplicacion
  ni volumenes Docker.
- El snapshot media sigue siendo local al mismo host: falta copia externa y
  prueba de restore para disaster recovery.
- La retencion de audit trail DB no se automatiza hasta definir politica
  funcional/legal; se elimina solo el cron roto, no datos.
