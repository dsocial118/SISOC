# Flujo: Relevamiento y primer seguimiento

## Objetivo

Registrar el relevamiento inicial de comedores y crear el primer seguimiento asociado al ultimo relevamiento activo del comedor sin romper el contrato vigente con GESTIONAR.

## Entrada / salida

- Entrada de relevamiento inicial: creacion/edicion de `relevamientos.models.Relevamiento` via UI o API.
- Entrada de primer seguimiento: creacion desde el modal de relevamientos con `tipo_relevamiento=primer_seguimiento`, o actualizacion externa por `PATCH /api/relevamiento/primer-seguimiento`.
- Salida de relevamiento inicial: payload HTTP a GESTIONAR para crear/borrar relevamientos; si GESTIONAR devuelve `docPDF`, se actualiza el modelo.
- Salida de primer seguimiento: payload HTTP especifico a GESTIONAR para crear/borrar primeros seguimientos.

## Relevamiento inicial

1. `Relevamiento.save()` valida duplicados activos y asigna el referente como responsable cuando corresponde.
2. El signal `send_relevamiento_to_gestionar` envia el alta con `AsyncSendRelevamientoToGestionar`.
3. La baja usa `AsyncRemoveRelevamientoToGestionar`.
4. La concurrencia se controla con `ThreadPoolExecutor` y `GESTIONAR_RELEVAMIENTOS_WORKERS` / `GESTIONAR_WORKERS`.

## Primer seguimiento

1. `PrimerSeguimientoService` valida el territorial usando el mismo parser del relevamiento inicial.
2. Busca el ultimo `Relevamiento` del comedor que no este eliminado y cuyo estado no sea `Finalizado` ni `Finalizado/Excepciones`.
3. Si no existe ancla activa, crea un `Relevamiento` local con `_skip_gestionar_sync=True`. Ese ancla no envia un relevamiento inicial a GESTIONAR.
4. Crea `PrimerSeguimiento` en estado `Asignado`, guarda el tecnico externo en `tecnico` y lo vincula por `id_relevamiento`.
5. Envia el alta con `AsyncSendPrimerSeguimientoToGestionar` usando `GESTIONAR_API_CREAR_PRIMER_SEGUIMIENTO`.
6. La baja usa `AsyncRemovePrimerSeguimientoToGestionar` y `GESTIONAR_API_BORRAR_PRIMER_SEGUIMIENTO`.

## API externa

`PATCH /api/relevamiento/primer-seguimiento` usa `HasAPIKeyOrToken`.

Requisitos:

- `sisoc_id`: id SISOC del `PrimerSeguimiento`.
- `id_relevamiento`: id SISOC del `Relevamiento` ancla.

Respuestas esperadas:

- `400` si falta alguno de los dos ids.
- `400` si `id_relevamiento` no corresponde al seguimiento informado.
- `404` si no existe el `PrimerSeguimiento`.
- `200` si el payload actualiza bloques relacionados y guarda el seguimiento.

## Validaciones y reglas

- No mas de un relevamiento con estado `Pendiente` o `Visita pendiente` por comedor.
- No mas de un `PrimerSeguimiento` para el mismo `Relevamiento`, reforzado por `OneToOneField`.
- El modal exige territorial para crear relevamiento inicial o primer seguimiento.
- `Segundo seguimiento` queda rechazado hasta implementar la fase 2.
- Los choices no confirmados se guardan como `CharField`; las escalas usan validadores 1..4 o 1..11.
- Las firmas recibidas desde GESTIONAR se guardan como URL/string, no como `FileField`.

## Errores comunes y debug

- ValidationError por relevamiento activo duplicado: revisar estados pendientes del comedor.
- ValidationError por primer seguimiento duplicado: revisar si el ancla ya tiene `primer_seguimiento`.
- Si se creo ancla local y aparece un alta de relevamiento inicial en GESTIONAR, revisar que el signal respete `_skip_gestionar_sync`.
- Fallas HTTP a GESTIONAR: revisar `GESTIONAR_API_KEY`, `GESTIONAR_API_CREAR_RELEVAMIENTO`, `GESTIONAR_API_BORRAR_RELEVAMIENTO`, `GESTIONAR_API_CREAR_PRIMER_SEGUIMIENTO` y `GESTIONAR_API_BORRAR_PRIMER_SEGUIMIENTO`.

## Tests

- `tests/test_primer_seguimiento_relevamientos.py`: modelos, servicio, payload y API de primer seguimiento.
- `comedores/tests.py`: endpoint AJAX usado por el modal de relevamientos.
