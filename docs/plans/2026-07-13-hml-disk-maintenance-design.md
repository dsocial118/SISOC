# Mantenimiento conservador de disco en HML

Estado: ejecucion manual y cron aprobados/validados el 2026-07-13.

## Evidencia

- `/` esta al 93%, con 6.7 GB libres.
- `/sisoc` ocupa 49 GB; 48 GB corresponden a media no regenerable.
- `/var/lib/docker` ocupa 21 GB.
- Docker reporta 76 imagenes para 3 activas y 18.06 GB recuperables.
- Build cache privado: 582.3 MB.
- `/var/log` ocupa 2.5 GB.
- MySQL local ocupa solo 200 MB; retirarlo no resuelve la capacidad.
- No se encontraron dumps grandes accesibles.

## Propuesta

1. Crear backup no secreto de configuracion e inventario Docker fuera del repo.
2. Registrar contenedores e imagenes activas antes de la poda.
3. Podar solo imagenes y build cache no usados con mas de 14 dias.
4. No tocar volumenes, contenedores, media, logs, MySQL ni checkouts.
5. Verificar mismos contenedores/imagenes activas y HTTP 200 en backend/mobile.
6. Medir espacio antes/despues.
7. Solo despues de validar una ejecucion manual, proponer cron semanal al 80%.

## Barreras

- Host exacto `ldmzssies-homolo`.
- `ENVIRONMENT=homologacion` sin imprimir el resto de `.env`.
- Modo informativo por defecto; mutacion solo con `--apply`.
- Lock para evitar ejecuciones simultaneas.
- Retencion minima configurable, default 336 horas.
- Nunca usar `--volumes`.
- Abort si cambian contenedores o imagenes activas.
- Health funcional separado del problema TLS preexistente; se informa el
  certificado invalido sin atribuirlo a la poda.

## Rollback y limites

La poda no tiene restauracion binaria para imagenes sin uso. Las imagenes activas
no se eliminan; una imagen antigua se reconstruye desde el commit registrado. El
backup guarda inventario y estado, no capas Docker.

La propuesta no renueva TLS, no retira MySQL local y no limpia media/logs. Esos
son cambios separados con backups y aprobaciones propias.

## Resultado

- Backup: `/home/jportilla/backups/infra/hml/20260713_132045`, checksums OK,
  directorios 700 y archivos 600.
- `/`: 93% -> 88%; libres 6.7 GB -> 12 GB.
- Docker: 76 -> 15 imagenes; 3 imagenes/contenedores activos intactos.
- Contenedores detenidos: 0; volumenes: 0.
- Backend, health, consulta DB remota y mobile: OK.
- Commits backend/mobile: sin cambios.
- TLS sigue invalido por vencimiento previo; no fue modificado.
- Scripts instalados bajo `/home/sisoc-deploy/bin`, owner/grupo
  `sisoc-deploy`, modo 750.
- Cron semanal instalado una sola vez, domingo 03:20, con backup previo en
  `/home/sisoc-deploy/backups/infra/hml/cron-install-20260713_133809`.
