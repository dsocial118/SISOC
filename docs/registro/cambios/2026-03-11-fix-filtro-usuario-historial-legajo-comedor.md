# Fix de filtros en historial de legajo de comedor (audittrail)

## Fecha
2026-03-11

## Contexto
En el historial (auditoría por instancia) del legajo de comedor había inconsistencias de filtrado:
- eventos con usuario visible en UI que no aparecían al filtrar por ese usuario;
- casos de filtros por modelo/ID con formato o espacios que no matcheaban de forma consistente.

## Causa raíz
El filtro `actor` en `audittrail.services.query_service.apply_filters` solo consultaba campos de `LogEntry.actor` (`username`, `email`, `first_name`, `last_name`).

Sin embargo, la UI prioriza snapshots persistidos en `AuditEntryMeta` (`actor_username_snapshot`, `actor_full_name_snapshot`, `actor_display_snapshot`) cuando existen. Eso generaba inconsistencia entre lo mostrado y lo filtrable.

## Cambio implementado
- Se agregó normalización común para filtros de texto.
- Se agregó `apply_actor_filter(...)` en `audittrail/services/query_service/impl.py`.
  - el filtro por actor ahora contempla relación viva (`LogEntry.actor.*`) y snapshots (`audittrail_meta.actor_*_snapshot`);
  - se aplica por términos (AND) para soportar búsquedas compuestas.
- Se agregó `apply_model_filter(...)`:
  - soporta formato exacto `app.model` (ej. `comedores.comedor`);
  - mantiene búsqueda parcial por app/model cuando no se usa ese formato.
- Se agregó `apply_object_pk_filter(...)` para normalizar espacios.
- Se ajustó el filtro de `action` para no aplicar `action=None` cuando el campo no viene en el payload.

## Validación
- Test unitario de regresión agregado en `tests/test_audittrail_views_unit.py`:
  - `test_query_service_actor_filter_includes_snapshot_fields`
  - `test_query_service_model_filter_supports_app_model_format`
  - `test_query_service_object_pk_and_actor_trim_spaces`
  - `test_query_service_does_not_filter_action_when_missing`

## Impacto
- Cambio backward-compatible.
- Mejora la coherencia entre la columna “Usuario” visible en auditoría y el resultado del filtro por usuario.
