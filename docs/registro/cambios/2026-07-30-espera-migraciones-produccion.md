# Espera acotada de migraciones en producción

## Incidente

El deploy del SHA `ff9da52ade8319b572fc7fc68df60be97235c932` levantó los
contenedores y finalizó `deploy_refresh.sh`, pero consultó `migrate --check`
antes de que el entrypoint terminara sus migraciones. Django devolvió estado
pendiente; la advertencia MySQL `models.W036` fue incidental y no la causa del
fallo.

## Corrección

El job de producción adopta el mismo sondeo acotado de QA y homologación:
intenta `migrate --check` hasta 30 veces, cada dos segundos, y sólo continúa al
healthcheck cuando las migraciones ya están aplicadas. Si se agota el límite,
publica el último error junto con `docker compose ps` y los últimos logs de
`django`, tanto para migraciones como para el healthcheck.

## Datos, compatibilidad y rollback

La corrección no añade ni modifica migraciones, contratos de API, permisos ni
datos. Mantiene la ejecución de las migraciones versionadas por el entrypoint
del contenedor; no introduce una operación manual o silenciosa sobre la base.
Algunas migraciones pendientes incluyen cambios de catálogo y normalización de
datos ya versionados, por lo que no existe rollback automático de datos. Si el
sondeo no converge, el workflow falla antes de declarar el deploy verificado y
se debe revisar el diagnóstico antes de reintentar. Revertir el workflow sólo
revierte su espera; no deshace migraciones ya aplicadas.
