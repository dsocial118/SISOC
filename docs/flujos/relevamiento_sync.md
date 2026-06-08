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

1. `PrimerSeguimientoService.create_asignado` resuelve el `Relevamiento` ancla y el territorial del seguimiento:
   - si llega `relevamiento_id` (alta desde el boton de una fila puntual del listado) o ya existe un relevamiento activo (no eliminado y cuyo estado no sea `Finalizado` ni `Finalizado/Excepciones`), usa ese relevamiento y **hereda** su `territorial_uid` como `tecnico` del seguimiento;
   - si no hay relevamiento previo, valida el territorial del formulario (mismo parser del relevamiento inicial) y crea un `Relevamiento` ancla **asignado** (estado `Visita pendiente`, con ese territorial) que **SI** se sincroniza con GESTIONAR. El seguimiento referencia ese relevamiento por `Id_Relevamiento`, asi que GESTIONAR necesita conocerlo para poder enlazar la fila de `Seguimientos1erVisita`.
2. Crea `PrimerSeguimiento` en estado `Asignado`, guarda el tecnico (heredado o del formulario) en `tecnico` y lo vincula por `id_relevamiento`.
3. Envia el alta con `AsyncSendPrimerSeguimientoToGestionar` usando `GESTIONAR_API_CREAR_PRIMER_SEGUIMIENTO`. El payload contiene `{"ID_Seguimiento1": "<pk>", "Id_Relevamiento": "<id>", "Id_SISOC": "<pk>"}`; `ID_Seguimiento1` viaja con el PK de SISOC para que ambos sistemas usen el mismo identificador. SISOC persiste lo que GESTIONAR devuelve en `Rows[0].ID_Seguimiento1` en `PrimerSeguimiento.gestionar_id` (en el flujo normal coincide con el sisoc_id; si GESTIONAR responde con otra cosa, queda registrado).
4. La baja usa `AsyncRemovePrimerSeguimientoToGestionar` y `GESTIONAR_API_BORRAR_PRIMER_SEGUIMIENTO`, enviando el `gestionar_id` guardado. Si el seguimiento no tiene `gestionar_id` (por ejemplo el alta nunca llego a GESTIONAR), la baja se omite con un log informativo.

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

Tanto `Relevamiento` como `PrimerSeguimiento` exponen el booleano `sincronizado_gestionar` (default `False`). El detalle muestra un badge verde "Sincronizado con GESTIONAR" cuando esta en `True`, y un badge gris "Pendiente sincronizacion" mientras siga en `False`. Se marca `True` por dos vias:

1. **POST saliente confirmado:** tanto `AsyncSendRelevamientoToGestionar` como `AsyncSendPrimerSeguimientoToGestionar` marcan `sincronizado_gestionar=True` solo cuando GESTIONAR responde `2xx` **y devuelve filas** (`Rows`). AppSheet responde `200` aun cuando rechaza el alta (p. ej. el `Id_Relevamiento` no existe en GESTIONAR o falta una columna requerida), pero en ese caso devuelve `Rows` vacio: ahi NO se marca sincronizado y se deja un `logger.warning` con el cuerpo para diagnostico. Esto evita el falso "exito" del log cuando la fila no se registro realmente.
2. **PATCH entrante:** cada `PATCH` exitoso desde GESTIONAR tambien lo marca en `True` via `update()` (sin disparar signals), y trae los bloques completos.

## Referente en el PATCH del primer seguimiento

El payload puede traer un objeto `referente` con dos formas:

1. **Asociar uno existente:** `{"sisoc_id": <pk_referente>}`. Si el PK no existe, devuelve `400`.
2. **Get-or-create por documento:** `{"documento": "30555777", "nombre": "...", "apellido": "...", "mail": "...", "celular": "...", "funcion": "..."}`. El `documento` se normaliza (acepta `30.555.777`, `30-555-777`, etc.) y es la clave del lookup. Si ya existe un `Referente` con ese DNI, se actualizan los campos enviados (los `None` no pisan valores previos).

Si no viene `documento` ni `sisoc_id`, cae al patron previo de busqueda por nombre.

## Validaciones y reglas

- No mas de un relevamiento con estado `Pendiente` o `Visita pendiente` por comedor.
- No mas de un `PrimerSeguimiento` para el mismo `Relevamiento`, reforzado por `OneToOneField`.
- El alta exige territorial cuando se crea un relevamiento (inicial o ancla de un primer seguimiento sin relevamiento previo). El primer seguimiento sobre un relevamiento existente NO pide territorial: lo hereda del relevamiento.
- `Segundo seguimiento` queda rechazado hasta implementar la fase 2.
- Los choices no confirmados se guardan como `CharField`; las escalas usan validadores 1..4 o 1..11.
- Las firmas recibidas desde GESTIONAR se guardan como URL/string, no como `FileField`.

## Errores comunes y debug

- ValidationError por relevamiento activo duplicado: revisar estados pendientes del comedor.
- ValidationError por primer seguimiento duplicado: revisar si el ancla ya tiene `primer_seguimiento`.
- El primer seguimiento "llega" a GESTIONAR con `2xx` pero no aparece la fila: revisar el `logger.warning` de `Rows` vacio. Causa tipica: el `Id_Relevamiento` apunta a un relevamiento que GESTIONAR no tiene. Desde 2026-06-04 el ancla creada para un primer seguimiento sin relevamiento previo SI se sincroniza (ya no usa `_skip_gestionar_sync`); si igual no enlaza, validar con el dueno de la app AppSheet que la tabla `Seguimientos1erVisita` no exija columnas adicionales.
- Fallas HTTP a GESTIONAR: revisar `GESTIONAR_API_KEY`, `GESTIONAR_API_CREAR_RELEVAMIENTO`, `GESTIONAR_API_BORRAR_RELEVAMIENTO`, `GESTIONAR_API_CREAR_PRIMER_SEGUIMIENTO` y `GESTIONAR_API_BORRAR_PRIMER_SEGUIMIENTO`.

## Tests

- `tests/test_primer_seguimiento_relevamientos.py`: modelos, servicio, payload y API de primer seguimiento.
- `comedores/tests.py`: endpoint AJAX usado por el modal de relevamientos.
