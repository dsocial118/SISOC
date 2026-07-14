# QA - Rollback operativo

Estado: validado para el mantenimiento de disco del 2026-07-13.

## Backup de referencia

`/home/sisoc-deploy/backups/infra/qa/20260713_110704`

Contiene configuracion NGINX, unidad del runner, contratos de deploy/Compose,
crontab previo, estado Git, servicios e inventario Docker. Los checksums fueron
verificados. No contiene valores de `.env`.

Snapshot posterior reproducible:

`/home/sisoc-deploy/backups/infra/qa/20260713_111618`

Incluye el crontab final y copias verificadas de los scripts instalados.

## Revertir el cron de mantenimiento

El crontab previo de `sisoc-deploy` estaba vacio. Restaurarlo requiere aprobacion:

```bash
crontab /home/sisoc-deploy/backups/infra/qa/20260713_110704/status/crontab.sisoc-deploy.txt
crontab -l
```

No hace falta detener Docker ni reiniciar cron.

## Revertir el script instalado

La primera opcion es deshabilitar solo su entrada de cron. No borrar el script
sin aprobacion. Las copias instaladas estan en `/home/sisoc-deploy/bin/` y sus
fuentes versionables en `scripts/infra/`.

## Imágenes y build cache podados

Los contenedores activos y sus imagenes no fueron eliminados. Las imagenes/cache
sin uso no se incluyen en el backup de configuracion y no tienen restauracion
directa. Si se necesitara una version antigua:

1. identificar el commit en `docker/images.txt` y `status/git-head.txt`;
2. revisar los side effects del entrypoint;
3. aprobar backup DB y ventana;
4. reconstruir desde Git/Dockerfile;
5. validar contenedores, HTTP, DB y logs.

No ejecutar un deploy como supuesto rollback: el deploy baja el stack y el
entrypoint escribe en la base.

## Detectar fallo

```bash
/home/sisoc-deploy/bin/healthcheck_qa.sh
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'
df -h /
journalctl -t sisoc-qa-disk-cleanup --since today --no-pager
```

Si falla health pero los contenedores siguen activos, preservar evidencia y no
reiniciar: el mantenimiento no toca runtime y el problema puede ser independiente.

## Retiro Stage 1 del MySQL local

Stage 1 no borra `/var/lib/mysql` ni paquetes. Si se necesita restaurar el
servicio local:

Backup de referencia:
`/var/backups/sisoc/mysql-local-retirement/20260713_115645`.

```bash
sudo systemctl enable --now mysql
sudo systemctl is-active mysql
sudo ss -lntp 'sport = :3306'
```

Luego verificar que Django siga conectado a `10.80.9.18`; no cambiar `.env` ni
reiniciar contenedores como parte de este rollback. El script de Stage 1 ejecuta
este rollback automaticamente si falla una validacion posterior al stop.
