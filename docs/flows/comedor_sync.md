# Flujo: Alta/edición/eliminación de Comedor con sincronización a GESTIONAR

## Objetivo
Mantener datos de comedores en SISOC y sincronizarlos con el sistema externo GESTIONAR en altas, actualizaciones y bajas.

## Entrada / Salida
- Entrada: creación/edición/eliminación de `comedores.models.Comedor` (formularios Django/DRF). Evidencia: comedores/models.py:203-405.
- Salida: payload HTTP enviado a GESTIONAR (`build_comedor_payload`) o solicitud de borrado. Evidencia: comedores/tasks.py:20-66,129-165.

## Pasos
1. Alta/edición/baja de Comedor dispara signals (`post_save`, `pre_save`, `pre_delete`). Evidencia: comedores/signals.py:24-68.
2. `post_save` (creado) → arma payload con `build_comedor_payload` y ejecuta `AsyncSendComedorToGestionar`. Evidencia: comedores/signals.py:24-29; comedores/tasks.py:20-125.
3. `pre_save` (update) compara instancia previa; si hay cambios (excepto `foto_legajo`), arma payload y sincroniza. Evidencia: comedores/signals.py:31-63.
4. `pre_delete` → ejecuta `AsyncRemoveComedorToGestionar` con action Delete. Evidencia: comedores/signals.py:65-68; comedores/tasks.py:129-165.
5. Tareas usan `ThreadPoolExecutor` y `requests.post` contra `GESTIONAR_API_*`. Evidencia: comedores/tasks.py:1-125,129-165.

## Validaciones y reglas
- Campos validados en modelo (dirección regex, lat/long con rangos, estados con choices). Evidencia: comedores/models.py:264-359,292-340.
- Al eliminar, el modelo limpia `ultimo_estado` e historial para evitar FK protegidas. Evidencia: comedores/models.py:382-396.
- Payload incluye URL de imagen con `DOMINIO` si existe `foto_legajo`. Evidencia: comedores/tasks.py:59-63.

## Side effects
- Auditoría de cambios de programa (ver flujo específico de programa). Evidencia: comedores/signals.py:31-52.
- Logs vía `logger.exception/info` en tareas. Evidencia: comedores/tasks.py:113-124,147-163.
- Sincronización asíncrona puede continuar después de la respuesta HTTP.

## Errores comunes y debug
- Errores de request a GESTIONAR: revisar logs (`logs/error.log`) y output de tasks (logger “django”). Evidencia: comedores/tasks.py:113-124,147-163.
- Campos inválidos (lat/long, dirección) bloquean save por validación de modelo. Evidencia: comedores/models.py:292-340.
- Si cambios no disparan sync (solo `foto_legajo`), es esperado (campo excluido). Evidencia: comedores/signals.py:53-59.

## Tests existentes
- No se detectaron tests específicos para sincronización de comedores. Evidencia: DESCONOCIDO (buscar en tests/comedores).***
