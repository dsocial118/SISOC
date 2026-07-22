# QA - Rollback operativo

Estado: actualizado el 2026-07-21 tras el retiro Stage 2 del MySQL local.

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

## MySQL local retirado en Stage 2

Stage 2 purgo los paquetes server y elimino `/var/lib/mysql` el 2026-07-21.
Por lo tanto, ya no existe rollback local mediante
`systemctl enable --now mysql`.

El backup de referencia
`/var/backups/sisoc/mysql-local-retirement/20260713_115645` se conserva solo
como evidencia de la configuracion, identidad y metadatos de Stage 1; no
contiene los datos ni habilita recuperar la instancia eliminada.

Ante un incidente, no reinstalar MySQL local ni modificar `.env` como supuesto
rollback. Verificar primero que Django mantenga su conexion con la DB canonica
`10.80.9.18`; cualquier nueva instancia local requiere aprobacion y un plan de
datos independiente.
