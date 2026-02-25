# Audittrail MVP Fase 1 (release y operación)

Documento breve para devs, ops y soporte sobre el release de Fase 1 del MVP de auditoría.

## Alcance del release (Fase 1)

Cambios funcionales esperados en la experiencia de auditoría:

- `keyword search`: búsqueda rápida por palabra clave para encontrar eventos relevantes (texto de diff, descripciones y/o campos visibles de auditoría).
- `actor legible`: mejor presentación del actor para evitar IDs/valores opacos cuando exista vínculo con usuario.
- `lotes heurísticos`: agrupación visual/lógica de eventos cercanos para lectura de acciones masivas.
- `auth_user`: uso explícito del usuario autenticado (tabla `auth_user`) para resolver/mostrar actor cuando esté disponible.
- `deletes custom`: mensajes de eliminación más legibles en casos donde el diff estándar no conserva suficiente contexto.

## Notas de release (humanas)

### Qué cambia para soporte/ops

- La búsqueda en Auditoría deja de depender solo de filtros exactos (`modelo`, `pk`, `actor`) y suma búsqueda por keyword para triage más rápido.
- Los eventos muestran actor de forma más entendible (nombre/username/email según disponibilidad), reduciendo consultas manuales a base.
- Operaciones masivas pueden verse agrupadas en lotes heurísticos para lectura más rápida del historial.
- Los eventos de eliminación en casos custom muestran textos de contexto más claros (qué se eliminó) en lugar de diffs poco útiles.
- El historial sigue soportando escenarios sin actor (procesos automáticos / comandos / hilos), mostrándolos como sistema/proceso.

### Breaking changes / atención operativa

- No se esperan breaking changes de API pública.
- Sí cambia la interpretación visual del historial: la agrupación por lotes es heurística y no debe usarse como garantía transaccional exacta.
- El actor mostrado puede cambiar respecto de releases previos (más legible), por lo que soporte debe validar por combinación de fecha + objeto + acción cuando compare capturas antiguas.

## Deploy (Fase 1)

### Checklist previo

- [ ] Confirmar tag/commit del release de Fase 1.
- [ ] Backup válido de DB previo al deploy (política estándar del equipo).
- [ ] Verificar acceso a `/auditoria/` en QA con usuario que tenga permiso `auditlog.view_logentry`.
- [ ] Validar que sigue activo `auditlog.middleware.AuditlogMiddleware` y la app `audittrail` en settings (si el deploy toca settings).
- [ ] Confirmar cron de purga (`purge_auditlog --days=180`) y espacio en disco/logs.

### Migraciones y configuración

- Migraciones propias de `audittrail` para Fase 1: **no se esperan** (el módulo no tiene migraciones propias en el estado actual del repo).
- Aun así, ejecutar el flujo estándar del release:
  - `python manage.py migrate` (por consistencia de deploy global del proyecto).
  - `python manage.py check`
- Feature flags / variables de entorno de Fase 1: **no se identifican flags nuevos específicos** en el repo actual. Si el tag final introduce flags, documentarlos en este archivo antes de promover a PRD.

### Smoke checks post deploy (5-10 min)

1. Abrir `GET /auditoria/` con usuario autorizado.
2. Verificar listado con eventos y paginación.
3. Probar filtros existentes (actor/fechas/modelo/pk) y la búsqueda por keyword.
4. Abrir un detalle `GET /auditoria/evento/<id>/` y confirmar visualización de actor y cambios.
5. Validar al menos un evento con `actor=None` (debe mostrarse como sistema/proceso, no romper UI).
6. Ejecutar `python manage.py purge_auditlog --days=180 --dry-run` en entorno no productivo o ventana controlada (si aplica) para confirmar que el comando responde.

## Rollback (Fase 1)

### Cuándo rollbackear

- Aumento sostenido de errores 5xx en `/auditoria/` o `/auditoria/evento/<id>/`.
- Consultas de auditoría con latencia inaceptable (p95/p99) por encima del umbral acordado.
- Resultados inconsistentes en búsqueda por keyword o agrupación que impidan soporte operativo.

### Pasos de rollback

1. Re-deploy del tag estable anterior (rollback de aplicación).
2. Reiniciar servicios web/workers según procedimiento estándar del entorno.
3. Revalidar `/auditoria/` y `/auditoria/evento/<id>/` con smoke básico.
4. Confirmar que cron de purga sigue intacto.

Notas:

- Si Fase 1 no agrega migraciones, **no hay rollback de schema específico** de audittrail.
- Si el release incluye migraciones ajenas al módulo, seguir el playbook general del proyecto (no forzar rollback de DB solo por esta feature).

## Soporte / troubleshooting rápido

### Cómo reproducir (casos típicos)

### 1) Buscar un cambio por keyword

1. Ingresar a `/auditoria/`.
2. Aplicar keyword relacionada al cambio (nombre de campo, valor, entidad o texto esperado del diff).
3. Refinar con fecha/actor/modelo si hay muchos resultados.

### 2) Verificar actor legible

1. Abrir un evento reciente realizado por usuario web.
2. Confirmar que el actor se muestra con identificador humano (username/nombre/email según disponibilidad).
3. Si aparece sistema/proceso, validar si fue comando, proceso automático o actor no disponible.

### 3) Revisar deletes custom

1. Abrir un evento de eliminación en entidad soportada.
2. Verificar que el mensaje conserve contexto útil (qué elemento se eliminó) y no solo valores crudos/vacíos.

### Mensajes/comportamientos esperables

- Sin resultados: `No hay eventos para los filtros seleccionados.`
- Evento sin diffs: `Sin diffs registrados para este evento.`
- Actor ausente: UI puede mostrar `Sistema` (equivale a `actor=None` en backend).
- Sin autenticación: redirección a login (`LoginRequiredMixin`).
- Sin permiso `auditlog.view_logentry`: respuesta 403 / permiso denegado (según manejo estándar de Django).

## Riesgos y supuestos (Fase 1)

- **Retención 180 días**: se asume suficiente para operación corriente. Riesgo: requerimientos de compliance/auditoría legal podrían exigir más. Mitigación: ajustar `--days` en cron + monitorear crecimiento de tabla.
- **Heurística de lotes**: se asume agrupación por proximidad temporal + actor + acción + contexto. Riesgo: falsos positivos/negativos de agrupación en operaciones concurrentes. Mitigación: mantener acceso al detalle evento por evento.
- **`actor=None` en procesos**: se asume normal en comandos, threads, tareas automáticas o integraciones sin request autenticado. Riesgo: soporte lo interprete como pérdida de trazabilidad. Mitigación: documentar origen del proceso y correlacionar con timestamp/objeto.
- **Resolución contra `auth_user`**: si el usuario fue borrado, incompleto o no resolvible, el actor puede degradar a valor genérico/sistema.
- **Búsqueda por keyword**: sin índices específicos sobre payloads/diffs, puede degradar performance con alto volumen de `LogEntry`.

## Métricas operativas recomendadas

Usar estas métricas como referencia mínima (nombres orientativos; adaptar a la herramienta de observabilidad):

- `audittrail_list_requests_total` (labels: `status`, `has_keyword`, `has_actor`, `has_date_range`)
- `audittrail_list_latency_seconds` (p50/p95/p99) para `/auditoria/`
- `audittrail_detail_latency_seconds` (p50/p95/p99) para `/auditoria/evento/<id>/`
- `audittrail_errors_total` (4xx/5xx por endpoint)
- `audittrail_keyword_search_zero_results_ratio`
- `audittrail_actor_none_ratio` (eventos mostrados con actor ausente / total consultado)
- `audittrail_batch_group_size` (tamaño promedio/máximo de lotes heurísticos)
- `purge_auditlog_duration_seconds`
- `purge_auditlog_deleted_total`
- `purge_auditlog_last_success_timestamp`
- `auditlog_rows_older_than_180d` (backlog fuera de política de retención)
- Slow queries de DB sobre `auditlog_logentry` (especialmente búsquedas con keyword y joins a `auth_user`)

## Referencias operativas

- Índice de documentación: `docs/indice.md`
- Operación y monitoreo general: `docs/operaciones.md`
- Comando de purga de auditoría: `docs/comandos_administracion.md`
- Changelog del release: `CHANGELOG.md`
