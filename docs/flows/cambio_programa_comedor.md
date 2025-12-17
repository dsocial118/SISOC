# Flujo: Cambio de programa de Comedor con auditoría

## Objetivo
Registrar y auditar cambios en el programa asignado a un comedor.

## Entrada / Salida
- Entrada: actualización de `Comedor.programa` (formularios/UI). Evidencia: comedores/models.py:229-233.
- Salida: registro en `AuditComedorPrograma` con programa anterior/nuevo y usuario. Evidencia: comedores/models.py:407-449.

## Pasos
1. En `pre_save` de Comedor, se compara el programa previo con el nuevo. Evidencia: comedores/signals.py:31-41.
2. Si cambió, se obtiene usuario actual vía `get_current_user()` (middleware threadlocals) y se registra creación diferida con `transaction.on_commit`. Evidencia: comedores/signals.py:41-52.
3. Se persiste `AuditComedorPrograma` con `from_programa`, `to_programa`, `changed_by`. Evidencia: comedores/models.py:407-449.
4. Si además hubo otros cambios, se dispara la sincronización a GESTIONAR (flujo de comedor_sync). Evidencia: comedores/signals.py:53-63.

## Validaciones y reglas
- Solo se audita cuando el FK `programa` cambia; se ejecuta dentro de la transacción de guardado. Evidencia: comedores/signals.py:31-52.
- No hay constraints adicionales en el modelo de auditoría (solo FKs opcionales). Evidencia: comedores/models.py:407-449.

## Side effects
- Registro histórico del cambio de programa. Evidencia: comedores/models.py:407-449.
- Potencial sincronización con GESTIONAR si hubo cambios en el comedor. Evidencia: comedores/signals.py:53-63.

## Errores comunes y debug
- Si `get_current_user()` es None, `changed_by` queda vacío (comportamiento esperado). Evidencia: comedores/signals.py:41-50.
- Para revisar historial: consultar `comedor.programa_changes.all()` (related_name). Evidencia: comedores/models.py:407-449.

## Tests existentes
- No se identificaron tests específicos para este flujo. Evidencia: DESCONOCIDO (no se hallaron en tests/).
