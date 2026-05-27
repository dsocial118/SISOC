# Primer seguimiento: contrato real con GESTIONAR

## Contexto

El PR #1643 dejo la integracion con GESTIONAR usando placeholders. El endpoint real de AppSheet es `https://api.appsheet.com/api/v2/apps/<app-id>/tables/Seguimientos1erVisita/Action` y espera un payload minimo: solo `Id_Relevamiento`. GESTIONAR responde con `ID_Seguimiento1` (string corto, ej. "afbeaa6c") que SISOC debe persistir para sincronizaciones posteriores.

## Cambio

- `relevamientos.tasks.build_primer_seguimiento_payload` envia `{"Id_Relevamiento": "<id>", "Id_SISOC": "<pk>"}` para que GESTIONAR guarde el correlato y pueda usarlo en el PATCH inverso.
- `PrimerSeguimientoApiView` ahora acepta `sisoc_id`/`Id_SISOC`, `gestionar_id`/`ID_Seguimiento1` o `id_relevamiento`/`Id_Relevamiento` (cualquiera alcanza). Si vienen varios, deben referir al mismo registro.
- `AsyncSendPrimerSeguimientoToGestionar.run()` parsea la respuesta y guarda `Rows[0].ID_Seguimiento1` en `PrimerSeguimiento.gestionar_id` via `update()` (sin disparar signals).
- Nuevo campo `PrimerSeguimiento.gestionar_id` (CharField max_length=64, nullable). Migracion `0009_primerseguimiento_gestionar_id`.
- `AsyncRemovePrimerSeguimientoToGestionar` ahora recibe `gestionar_id` y lo usa en el payload de DELETE. Si esta vacio, omite la llamada.
- Signal `remove_primer_seguimiento_to_gestionar` (pre_delete) lee `instance.gestionar_id` y lo pasa a la task.
- Placeholders en `.env.qa` y `.env.prod` actualizados de `/tables/PrimerSeguimiento/Action` (tabla inexistente) a `/tables/Seguimientos1erVisita/Action` (nombre real).

## Decisiones

- El endpoint de **borrado** todavia no fue confirmado por el equipo de GESTIONAR; se asume el patron estandar AppSheet (misma URL con `Action: Delete`). Si se confirma una URL distinta, solo hay que actualizar `GESTIONAR_API_BORRAR_PRIMER_SEGUIMIENTO`.
- El endpoint **PATCH inverso** acepta los tres posibles identificadores (`sisoc_id`, `gestionar_id`, `id_relevamiento`) en lugar de forzar una sola combinacion. Esto le da flexibilidad a GESTIONAR sin tener que decidir el contrato exacto antes de la integracion.

## Pendientes

- Configurar el UUID real de la app AppSheet en `.env.qa`/`.env.prod` (los placeholders quedan con `<qa-app-id>`/`<prd-app-id>`).
- Confirmar que la tabla `Seguimientos1erVisita` tenga columna `Id_SISOC`; si no existe, AppSheet ignora el campo silenciosamente.
- Confirmar URL de baja (asumido mismo endpoint con `Action: Delete`).
