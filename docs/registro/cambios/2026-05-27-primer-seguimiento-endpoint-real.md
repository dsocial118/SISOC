# Primer seguimiento: contrato real con GESTIONAR

## Contexto

El PR #1643 dejo la integracion con GESTIONAR usando placeholders. El endpoint real de AppSheet es `https://api.appsheet.com/api/v2/apps/<app-id>/tables/Seguimientos1erVisita/Action` y espera un payload minimo: solo `Id_Relevamiento`. GESTIONAR responde con `ID_Seguimiento1` (string corto, ej. "afbeaa6c") que SISOC debe persistir para sincronizaciones posteriores.

## Cambio

- `relevamientos.tasks.build_primer_seguimiento_payload` envia solo `{"Id_Relevamiento": "<id>"}`.
- `AsyncSendPrimerSeguimientoToGestionar.run()` parsea la respuesta y guarda `Rows[0].ID_Seguimiento1` en `PrimerSeguimiento.gestionar_id` via `update()` (sin disparar signals).
- Nuevo campo `PrimerSeguimiento.gestionar_id` (CharField max_length=64, nullable). Migracion `0009_primerseguimiento_gestionar_id`.
- `AsyncRemovePrimerSeguimientoToGestionar` ahora recibe `gestionar_id` y lo usa en el payload de DELETE. Si esta vacio, omite la llamada.
- Signal `remove_primer_seguimiento_to_gestionar` (pre_delete) lee `instance.gestionar_id` y lo pasa a la task.
- Placeholders en `.env.qa` y `.env.prod` actualizados de `/tables/PrimerSeguimiento/Action` (tabla inexistente) a `/tables/Seguimientos1erVisita/Action` (nombre real).

## Decisiones

- El endpoint de **borrado** todavia no fue confirmado por el equipo de GESTIONAR; se asume el patron estandar AppSheet (misma URL con `Action: Delete`). Si se confirma una URL distinta, solo hay que actualizar `GESTIONAR_API_BORRAR_PRIMER_SEGUIMIENTO`.
- El endpoint **PATCH inverso** (GESTIONAR -> SISOC) sigue exigiendo `sisoc_id` + `id_relevamiento`. Pendiente decidir con el equipo de GESTIONAR si va a identificar por `gestionar_id` o `Id_Relevamiento`. Si se decide por `gestionar_id`, hay que extender `PrimerSeguimientoApiView` para resolver por ese campo tambien.

## Pendientes

- Configurar el UUID real de la app AppSheet en `.env.qa`/`.env.prod` (los placeholders quedan con `<qa-app-id>`/`<prd-app-id>`).
- Confirmar URL de baja.
- Confirmar contrato del PATCH inverso.
