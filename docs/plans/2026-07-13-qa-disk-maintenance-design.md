# Mantenimiento conservador de disco en QA

Estado: aprobado por el usuario el 2026-07-13. La ampliacion para incluir build
cache con la misma retencion fue aprobada despues de la primera poda.

## Contexto

El QA canonico es `qa-old` (`mdsldmz-ssies-test`, `10.80.9.15`). Los hosts
AWS quedan fuera de alcance y solo representan un destino posible de migracion.

El filesystem raiz esta al 93%. Docker mantiene 28 imagenes para 2 contenedores
activos y reporta 10.96 GB recuperables. No hay volumenes Docker locales y el
build cache recuperable es de solo 22.58 MB. El crontab efectivo de
`sisoc-deploy` esta vacio; la limpieza versionada nunca fue instalada y ademas
incluye `--volumes`, que no es aceptable para este mantenimiento.

## Decision

1. Respaldar configuracion legible, crontab e inventario Docker fuera del repo.
2. Podar solo imagenes y build cache no usados con mas de 14 dias (`336h`).
3. No podar volumenes, contenedores, dumps, media, logs ni datos MySQL.
4. No reiniciar servicios ni ejecutar deploys o migraciones.
5. Instalar un script mantenible bajo el usuario `sisoc-deploy`.
6. Ejecutarlo semanalmente solo cuando `/` alcance al menos 80%.
7. Excluir secretos, datos y artefactos grandes del contexto de build con
   `.dockerignore`.

## Barreras de seguridad

- Host exacto: `mdsldmz-ssies-test`.
- Entorno exacto: `ENVIRONMENT=qa`, leido sin imprimir el resto de `.env`.
- Modo informativo por defecto; la mutacion requiere `--apply`.
- Ejecucion automatica requiere ademas `--yes`.
- Lock con `flock` para evitar ejecuciones superpuestas.
- Retencion expresada solo como una cantidad positiva de horas.
- Las ordenes permitidas son `docker image prune -af --filter until=336h` y
  `docker builder prune -af --filter until=336h`.
- No existe opcion para agregar `--volumes`.

## Rollback

La poda de imagenes sin uso no modifica los contenedores activos. Las imagenes
eliminadas no se restauran desde el backup de configuracion: si hiciera falta
una version antigua, se reconstruye desde el commit registrado. Por eso se
conservan 14 dias y se exporta el inventario completo antes de limpiar.

El cron se revierte restaurando el crontab exportado. El script instalado puede
deshabilitarse quitando solo su entrada de cron; no es necesario detener Docker.

## Verificacion

- Comparar `df -h /` y `docker system df` antes/despues.
- Confirmar mismos nombres e IDs de imagen de los contenedores activos.
- Confirmar HTTP 200 en `/` y `/health/`.
- Confirmar que el crontab contiene una sola entrada de mantenimiento.
- Confirmar que el working tree remoto no recibio cambios por la operacion.
