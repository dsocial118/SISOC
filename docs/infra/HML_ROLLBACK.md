# HML - Rollback operativo

Estado: documentado para la limpieza Docker, recurrencia y Stage 1 de MySQL del
2026-07-13.

## Evidencia previa

Backup:

`/home/jportilla/backups/infra/hml/20260713_132045`

Los checksums fueron verificados. El backup registra commits, contenedores,
imagenes, Compose, NGINX, systemd, disco y metadata TLS, sin secretos.

## Alcance real de la limpieza

- Se eliminaron solo imagenes/build cache sin uso de mas de 14 dias.
- No se tocaron contenedores, volumenes, media, logs, MySQL, Git, NGINX ni TLS.
- No hubo restart, deploy o migracion.

## Rollback

Las capas eliminadas no tienen restauracion binaria. Si se necesita una imagen
antigua:

1. identificar commit e imagen en el backup;
2. revisar side effects del entrypoint;
3. aprobar backup DB y ventana;
4. reconstruir desde Git/Dockerfile;
5. validar contenedores, DB, backend, mobile y logs.

No ejecutar un deploy como supuesto rollback: baja/reconstruye el stack y puede
escribir DB. Las imagenes de los contenedores activos no fueron eliminadas.

## Detectar fallo

```bash
bash scripts/infra/healthcheck_hml.sh
docker ps --no-trunc
df -h /
journalctl -t sisoc-hml-disk-cleanup --since today --no-pager
```

El certificado vencido es preexistente y no implica fallo de la poda.

## Revertir la recurrencia

Backup del crontab previo y scripts reemplazados:

`/home/sisoc-deploy/backups/infra/hml/cron-install-20260713_133809`

Restaurar el crontab requiere aprobacion:

```bash
sudo crontab -u sisoc-deploy \
  /home/sisoc-deploy/backups/infra/hml/cron-install-20260713_133809/status/crontab.before.txt
```

No borrar los scripts instalados sin una aprobacion separada. Restaurar un script
anterior solo si existe su copia bajo `installed-before/`.

## MySQL local - Stage 1

Estado aplicado:

- `mysql.service`: inactivo y deshabilitado;
- listener local 3306: ausente;
- datadir y paquetes: intactos;
- backup root-only:
  `/var/backups/sisoc/mysql-local-retirement/hml/20260713_135622`;
- observacion minima: hasta el 2026-07-20.

Reactivar requiere aprobacion, porque vuelve a exponer el listener local. No es
necesario restaurar archivos mientras `/etc/mysql` y `/var/lib/mysql` sigan
intactos:

```bash
sudo systemctl enable --now mysql
systemctl show mysql -p ActiveState -p UnitFileState --no-pager
ss -Hlnpt 'sport = :3306'
```

Despues del rollback, verificar que la aplicacion siga usando la DB remota y no
la instancia reactivada:

```bash
docker exec sisoc-django-1 python manage.py shell -c \
  "from django.db import connection; connection.ensure_connection(); print(connection.settings_dict.get('HOST')); print(connection.connection.get_host_info())"
bash scripts/infra/healthcheck_hml.sh
```

El resultado esperado es host configurado `10.80.5.48`, conexion TCP a ese host
y health funcional OK. No imprimir credenciales ni el contenido de `.env`.

Si faltara configuracion, detenerse y comparar checksums/metadata con el backup;
no copiar el arbol completo a ciegas. No borrar backup, datadir o paquetes como
parte de este rollback.
