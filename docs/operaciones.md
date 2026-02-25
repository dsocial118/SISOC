# Operación y monitoreo

## Tareas programadas (cron)
- Limpieza de carpetas de logs antiguas mediante `borrar_logs.py` ejecutado diariamente a las 00:00. Evidencia: scripts/crontab:2 y scripts/borrar_logs.py:1-43.
- `docker system prune` semanal (domingos 03:00) para liberar espacio. Evidencia: scripts/crontab:3.
- Agente HetrixTools cada 5 minutos. Evidencia: scripts/crontab:4.
- Purga de auditlog mayor a 180 días vía `manage.py purge_auditlog` diariamente 03:00. Evidencia: scripts/crontab:5 y audittrail/management/commands/purge_auditlog.py:1-38.

## Healthcheck
- Endpoint `GET /health/` devuelve `OK` (200) para monitoreo. Evidencia: healthcheck/urls.py:1-5 y healthcheck/views.py:1-4.

## Auditoría (MVP Fase 1)
- Rutas de uso operativo: `/auditoria/` (listado), `/auditoria/evento/<id>/` (detalle) y vistas por instancia bajo `/auditoria/<app>/<model>/<pk>/`. Evidencia: audittrail/urls.py:1-15.
- El acceso requiere autenticación + permiso `auditlog.view_logentry`. Evidencia: audittrail/views.py:316 y audittrail/views.py:459.
- Para checklist de deploy/rollback, troubleshooting y métricas sugeridas del MVP Fase 1 ver `docs/implementaciones/audittrail_mvp_fase1.md`.

## Auditoría (Fase 2 - metadata persistida)
- Fase 2 agrega migración propia de `audittrail` para `AuditEntryMeta` (snapshot actor, `source`, `batch_key`) y requiere `python manage.py migrate` antes de validar el panel.
- El panel puede mostrar `Origen` (Web / Comando / Sistema) y agrupar por `batch_key` cuando la metadata existe.
- Se agregan filtros por `campo`, `origen`, `batch_key` y exportación `CSV/JSON` (requiere permiso `audittrail.export_auditlog`).
- En MySQL 8.0 se crean índices y FULLTEXT sobre `auditlog_logentry` (si existe `changes_text`) para mejorar búsquedas/consultas.
- Para deploy/rollback y uso de `audittrail.context.audit_context(...)` ver `docs/implementaciones/audittrail_fase2.md`.
