# Operación y monitoreo

## Tareas programadas (cron)
- Limpieza de carpetas de logs antiguas mediante `borrar_logs.py` ejecutado diariamente a las 00:00. Evidencia: scripts/crontab:2 y scripts/borrar_logs.py:1-43.
- `docker system prune` semanal (domingos 03:00) para liberar espacio. Evidencia: scripts/crontab:3.
- Agente HetrixTools cada 5 minutos. Evidencia: scripts/crontab:4.
- Purga de auditlog mayor a 180 días vía `manage.py purge_auditlog` diariamente 03:00. Evidencia: scripts/crontab:5 y audittrail/management/commands/purge_auditlog.py:1-38.

## Healthcheck
- Endpoint `GET /health/` devuelve `OK` (200) para monitoreo. Evidencia: healthcheck/urls.py:1-5 y healthcheck/views.py:1-4.
