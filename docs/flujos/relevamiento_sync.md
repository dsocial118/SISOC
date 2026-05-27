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
5. Envia el alta con `AsyncSendPrimerSeguimientoToGestionar` usando `GESTIONAR_API_CREAR_PRIMER_SEGUIMIENTO`. El payload contiene `{"ID_Seguimiento1": "<pk>", "Id_Relevamiento": "<id>", "Id_SISOC": "<pk>"}`; `ID_Seguimiento1` viaja con el PK de SISOC para que ambos sistemas usen el mismo identificador. SISOC persiste lo que GESTIONAR devuelve en `Rows[0].ID_Seguimiento1` en `PrimerSeguimiento.gestionar_id` (en el flujo normal coincide con el sisoc_id; si GESTIONAR responde con otra cosa, queda registrado).
6. La baja usa `AsyncRemovePrimerSeguimientoToGestionar` y `GESTIONAR_API_BORRAR_PRIMER_SEGUIMIENTO`, enviando el `gestionar_id` guardado. Si el seguimiento no tiene `gestionar_id` (por ejemplo el alta nunca llego a GESTIONAR), la baja se omite con un log informativo.

## API externa

`PATCH /api/relevamiento/primer-seguimiento` usa `HasAPIKeyOrToken`.

GESTIONAR puede identificar al seguimiento por cualquiera de estos tres campos (alcanza con uno):

- `sisoc_id` / `Id_SISOC`: PK del `PrimerSeguimiento` en SISOC.
- `gestionar_id` / `ID_Seguimiento1`: PK que GESTIONAR genero y SISOC persistio.
- `id_relevamiento` / `Id_Relevamiento`: PK del `Relevamiento` ancla (unico por OneToOne).

Si el payload trae mas de uno, deben referir al mismo registro.

Respuestas esperadas:

- `400` si no viene ninguno de los tres identificadores, si alguno es invalido o si entre si refieren a distintos registros.
- `404` si no existe el `PrimerSeguimiento`.
- `200` si el payload actualiza bloques relacionados y guarda el seguimiento.

## Estado de sincronizacion

Tanto `Relevamiento` como `PrimerSeguimiento` exponen el booleano `sincronizado_gestionar` (default `False`). Cada `PATCH` exitoso desde GESTIONAR lo marca en `True` via `update()` (sin disparar signals). El detalle de relevamiento muestra un badge verde "Sincronizado con GESTIONAR" cuando esta en `True`, y un badge gris "Pendiente sincronizacion" en el bloque del primer seguimiento mientras siga en `False`.

## Referente en el PATCH del primer seguimiento

El payload puede traer un objeto `referente` con dos formas:

1. **Asociar uno existente:** `{"sisoc_id": <pk_referente>}`. Si el PK no existe, devuelve `400`.
2. **Get-or-create por documento:** `{"documento": "30555777", "nombre": "...", "apellido": "...", "mail": "...", "celular": "...", "funcion": "..."}`. El `documento` se normaliza (acepta `30.555.777`, `30-555-777`, etc.) y es la clave del lookup. Si ya existe un `Referente` con ese DNI, se actualizan los campos enviados (los `None` no pisan valores previos).

Si no viene `documento` ni `sisoc_id`, cae al patron previo de busqueda por nombre.

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
