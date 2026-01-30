# Flujo: Relevamiento (creación, validación y sincronización con GESTIONAR)

## Objetivo
Registrar relevamientos de comedores, validar que no existan duplicados activos y sincronizar con GESTIONAR.

## Entrada / Salida
- Entrada: creación/edición de `relevamientos.models.Relevamiento` (vía UI o import). Evidencia: relevamientos/models.py:986-1084.
- Salida: payload HTTP a GESTIONAR para crear/borrar relevamientos; opcionalmente URL `docPDF` actualizada en modelo. Evidencia: relevamientos/tasks.py:23-91,116-141.

## Pasos
1. `Relevamiento.save()` valida duplicados activos y setea responsable si corresponde. Evidencia: relevamientos/models.py:1036-1064.
2. Post-save signal clasifica comedor (ClasificacionComedorService). Evidencia: comedores/signals.py:91-93.
3. Tareas asíncronas:
   - Crear: `AsyncSendRelevamientoToGestionar` arma payload (`build_relevamiento_payload`) y hace POST a `GESTIONAR_API_CREAR_RELEVAMIENTO`; guarda `docPDF` si viene en la respuesta. Evidencia: relevamientos/tasks.py:23-91.
   - Borrar: `AsyncRemoveRelevamientoToGestionar` envía Action Delete a `GESTIONAR_API_BORRAR_RELEVAMIENTO`. Evidencia: relevamientos/tasks.py:107-141.
4. Concurrencia controlada con `ThreadPoolExecutor` y `MAX_WORKERS` por env vars. Evidencia: relevamientos/tasks.py:16-21.

## Validaciones y reglas
- No más de un relevamiento con estado “Pendiente” o “Visita pendiente” por comedor; si existe, `save` lanza ValidationError. Evidencia: relevamientos/models.py:1050-1064.
- `unique_together` en (comedor, fecha_visita). Evidencia: relevamientos/models.py:1065-1071.
- Si `responsable_es_referente` y el comedor tiene referente, lo asigna como responsable. Evidencia: relevamientos/models.py:1042-1049.

## Side effects
- Clasificación automática del comedor tras guardar relevamiento. Evidencia: comedores/signals.py:91-93.
- Sincronización asíncrona con GESTIONAR (create/delete). Evidencia: relevamientos/tasks.py:23-91,107-141.
- Logs en tareas (`logger.exception/info`). Evidencia: relevamientos/tasks.py:80-91,133-140.

## Errores comunes y debug
- ValidationError por relevamiento activo duplicado: revisar estados y registros existentes. Evidencia: relevamientos/models.py:1050-1064.
- Fallas HTTP a GESTIONAR: revisar logs de errores y variables `GESTIONAR_API_*`/`GESTIONAR_API_KEY`. Evidencia: relevamientos/tasks.py:70-91,129-140.
- `docPDF` no actualizado: chequear respuesta `Rows[0].docPDF` y logs de tarea. Evidencia: relevamientos/tasks.py:82-91.

## Tests existentes
- No se identificaron tests específicos de relevamientos en el repo actual. Evidencia: DESCONOCIDO (no se hallaron en tests/).
