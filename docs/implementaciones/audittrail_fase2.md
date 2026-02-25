# Audittrail Fase 2 (metadata persistida y agrupación determinística)

Extiende el MVP de auditoría con metadata persistida por evento para mejorar la
confiabilidad de la trazabilidad y la lectura de acciones masivas.

## Qué agrega Fase 2

- Tabla `audittrail_auditentrymeta` (modelo `AuditEntryMeta`) asociada 1:1 a `auditlog.LogEntry`.
- Snapshot persistido de actor (`username`, nombre/apellido y display) al momento del evento.
- `source` persistido (ej. `http`, `management_command:...`, `system`).
- `batch_key` persistido para agrupación más confiable de acciones masivas.
- Context manager `audittrail.context.audit_context(...)` para scripts/procesos.
- UI de auditoría que prioriza snapshots persistidos y muestra `Origen`.

## Deploy (Fase 2)

### Checklist previo

- [ ] Deploy de código de Fase 1 ya estable.
- [ ] Backup DB.
- [ ] Confirmar que `django-auditlog` está presente en el entorno de app/CI.

### Pasos

1. Ejecutar migraciones:
   - `python manage.py migrate`
2. Validar que existe la tabla:
   - `audittrail_auditentrymeta`
3. Smoke del panel:
   - `/auditoria/`
   - `/auditoria/evento/<id>/` (ver campo `Origen`)
4. Validar una acción nueva (web o comando) y confirmar que se crea metadata Fase 2.

## Rollback (Fase 2)

### Si falla antes de migrar

- Revertir deploy de aplicación.

### Si falla después de migrar

- Revertir deploy de aplicación.
- La tabla `audittrail_auditentrymeta` puede quedar sin uso (rollback no destructivo).
- Evitar rollback de schema salvo necesidad explícita.

## Uso para scripts/procesos (recomendado)

Ejemplo conceptual:

```python
from audittrail.context import audit_context

with audit_context(
    source="management_command:reprocesar_auditoria",
    batch_key="reproceso-2026-02-25",
    extra={"ticket": "OPS-123"},
):
    # operaciones que generan LogEntry
    ...
```

## Riesgos / límites

- Eventos históricos previos a Fase 2 pueden no tener `AuditEntryMeta` (fallback a comportamiento Fase 1).
- Si un proceso no usa `audit_context(...)` y no hay `cid`, la agrupación puede seguir dependiendo de heurística/fallback.
- Sin backfill, la mejora de snapshots aplica principalmente a eventos nuevos.

## Validación recomendada

- Crear/editar/borrar registros desde UI web y confirmar `Origen = Web`.
- Ejecutar un comando con `audit_context(...)` y confirmar `Origen = Comando (...)`.
- Verificar agrupación de lote por `batch_key` con múltiples eventos.
- Verificar actor snapshot si luego cambia nombre/username del usuario.
