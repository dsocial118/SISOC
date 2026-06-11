# 2026-06-04 - Ajustes de produccion del primer seguimiento

## Resumen
Tres correcciones reportadas al probar primer seguimiento en produccion:

1. El detalle del primer seguimiento quedaba en "Pendiente sincronizacion" aunque
   el POST a GESTIONAR habia sido exitoso (logueaba "...sincronizado con GESTIONAR
   con exito").
2. El listado de relevamientos mostraba "Sin asignar" como fallback de la fecha,
   leyendose como si el relevamiento no estuviera asignado.
3. El boton `Agregar` vivia en el cuerpo de la card; se pidio moverlo al header
   (alineado con "Relevamientos") y sumar un boton `Agregar` por cada relevamiento
   para crear un seguimiento sobre ese relevamiento puntual.

## Cambios realizados

### 1. Estado de sincronizacion del primer seguimiento
- `relevamientos/tasks.py` (`AsyncSendPrimerSeguimientoToGestionar.run`): tras un
  POST `2xx`, ademas de guardar `gestionar_id` (si viene en la respuesta) se marca
  `sincronizado_gestionar=True`. El registro ya esta del lado de GESTIONAR, asi que
  el badge deja de figurar "Pendiente" sin esperar al `PATCH` de vuelta (que igual
  lo mantiene en `True`). `Relevamiento` conserva su comportamiento (solo lo marca
  el `PATCH` entrante).
- `relevamientos/templates/primer_seguimiento_detail.html` y
  `relevamientos/templates/relevamiento_detail.html`: se ajusto el `title` del badge
  ("se sincronizo con GESTIONAR" / "Todavia no se sincronizo con GESTIONAR") para no
  afirmar "datos recibidos".

### 2. Texto "Sin asignar" en el listado
- `relevamientos/templates/relevamiento_list.html`: el fallback de la fecha
  (`default_if_none`) pasa de `"Sin asignar"` a `"Sin fecha"`, tanto para el
  relevamiento como para el seguimiento.

### 3. Ubicacion de los botones `Agregar`
- `relevamientos/templates/relevamiento_list.html`:
  - El boton `Agregar` (abre `#modalRelevamientoNuevo`) se movio al header de la
    card, alineado con el titulo "Relevamientos".
  - Cada relevamiento (no los seguimientos) que aun no tiene primer seguimiento
    muestra un boton `Agregar` que abre `#modalSeguimientoNuevo` con
    `data-relevamiento-id`.
  - Nuevo modal `#modalSeguimientoNuevo` (tipo primer/segundo seguimiento -segundo
    deshabilitado, fase 2- + territorial) que postea a `relevamiento_create_edit_ajax`
    con un hidden `relevamiento_id`. El select de territorial reutiliza el cache JS
    (`id` con substring `update_territorial_select`).
  - JS que setea el hidden `relevamiento_id` al abrir el modal (`show.bs.modal`).
- `relevamientos/views/web_views.py` (`RelevamientoListView`): cada item padre
  expone `has_seguimiento` para decidir si mostrar el boton por fila.
- `relevamientos/primer_seguimiento_service.py` (`create_asignado`): nuevo parametro
  opcional `relevamiento_id`. Si viene, se ancla a ese relevamiento del comedor
  (`get_object_or_404` scopeado al comedor); si no, se mantiene la resolucion previa
  del ancla activa. El mensaje de duplicado pasa a "...para este relevamiento.".
- `comedores/views/relevamientos.py` (`_handle_create_primer_seguimiento`): reenvia
  `relevamiento_id` desde el POST al servicio.

## Tests
- `tests/test_primer_seguimiento_relevamientos.py`: el envio saliente marca
  `sincronizado_gestionar` (con y sin `gestionar_id` en la respuesta); alta con
  `relevamiento_id` explicito; rechazo si el `relevamiento_id` es de otro comedor.
- `tests/test_relevamientos_web_views_unit.py`: los items del listado incluyen
  `has_seguimiento`.
- `comedores/tests.py`: el endpoint reenvia `relevamiento_id` al servicio.

## Comportamiento observable
- Detalle del primer seguimiento: badge verde "Sincronizado con GESTIONAR" apenas el
  envio saliente responde OK.
- Listado: la fecha ausente se muestra como "Sin fecha".
- Listado: `Agregar` general en el header; `Agregar` por relevamiento sin seguimiento
  para crear el primer seguimiento de ese relevamiento puntual.

## Segunda ronda (mismo dia): por que no llegaba a GESTIONAR + territorial + badge relevamiento

### Diagnostico "no llega a GESTIONAR"
Causa raiz: cuando se crea un primer seguimiento **sin relevamiento inicial**, el
servicio creaba un ancla `Relevamiento` con `_skip_gestionar_sync=True`, asi que ese
relevamiento **nunca se enviaba a GESTIONAR**. El seguimiento se POSTeaba a la tabla
`Seguimientos1erVisita` con `Id_Relevamiento` apuntando a un relevamiento inexistente
en GESTIONAR -> AppSheet responde `200` pero **no registra la fila** (devuelve `Rows`
vacio). El codigo logueaba "sincronizado con exito" ante cualquier `2xx`, enmascarando
el rechazo; el `gestionar_id` vacio ("Sin asignar") es justamente la senal.

### Cambios
- `relevamientos/tasks.py`: `AsyncSendPrimerSeguimientoToGestionar` y
  `AsyncSendRelevamientoToGestionar` ahora marcan `sincronizado_gestionar=True` **solo si
  GESTIONAR devuelve `Rows`**. Si responde `2xx` sin filas, `logger.warning` con el cuerpo
  y NO se marca (estado honesto). Esto revierte la marca incondicional en `2xx` de la
  primera ronda para el seguimiento.
- `AsyncSendRelevamientoToGestionar` ahora **marca el badge del relevamiento** en el POST
  saliente confirmado (pedido explicito: aplicar el cambio de badge tambien a relevamiento).
- `relevamientos/primer_seguimiento_service.py`:
  - El ancla creada para un primer seguimiento sin relevamiento previo **ya NO usa
    `_skip_gestionar_sync`**: se crea como relevamiento asignado (`Visita pendiente`, con el
    territorial del formulario) y se sincroniza a GESTIONAR, para que el seguimiento pueda
    enlazar por `Id_Relevamiento`.
  - **Territorial:** sin relevamiento previo, el territorial del formulario se aplica al
    ancla y al seguimiento; con relevamiento existente (o `relevamiento_id` puntual), el
    `tecnico` se **hereda** de `relevamiento.territorial_uid`.
- `comedores/views/relevamientos.py`: el dispatch del endpoint AJAX reconoce el alta por
  `tipo_relevamiento` (ademas de `territorial`), porque el modal por-fila ya no manda
  territorial.
- `relevamientos/templates/relevamiento_list.html`: el modal `#modalSeguimientoNuevo` ya
  no pide territorial (lo hereda); ayuda actualizada.
- `relevamientos/templates/relevamiento_detail.html`: tooltip del badge del relevamiento.

### Decision a confirmar
El ancla de un primer seguimiento sin relevamiento inicial ahora **crea un relevamiento en
GESTIONAR** (revierte la decision previa de `_skip_gestionar_sync`). Es necesario para que
el seguimiento enlace (un `Seguimientos1erVisita` referencia un `RelevamientoComedores`).
Si se prefiere no crear ese relevamiento en GESTIONAR, hay que rediseniar el contrato con
el dueno de la app AppSheet.

### Tests
- `tests/test_relevamientos_tasks_unit.py`: el sync de relevamiento marca/omite el badge
  segun haya `Rows`.
- `tests/test_primer_seguimiento_relevamientos.py`: herencia de territorial (ancla nueva vs
  relevamiento existente vs `relevamiento_id`), ancla nueva sincroniza a GESTIONAR, y el
  seguimiento NO se marca sincronizado si GESTIONAR no devuelve filas.

## Tercera ronda: causa raiz REAL verificada contra la API de AppSheet (2026-06-04)

Se probo la API real (`.../tables/Seguimientos1erVisita/Action`, app `7ca73a85-...`) con
consultas `Find` (read-only) y un `Add`/`Delete` de diagnostico (creado y borrado, tabla
queda en 0). Hallazgos:

- La tabla `Seguimientos1erVisita` estaba **vacia (0 filas)**: ningun primer seguimiento
  llego nunca, pese a los logs "con exito". La de relevamientos (`RelevamientoComedores`)
  tiene 5171 filas → los relevamientos SI sincronizan.
- **Causa raiz:** el alta mandaba `ID_Seguimiento1` (nuestro PK), que es la **CLAVE
  autogenerada** de la tabla. AppSheet rechaza en silencio el `Add` que la incluye
  (responde `200` con cuerpo vacio, no crea fila). Verificado:
  - `{"Id_Relevamiento":"8584"}` -> 200 y crea la fila; GESTIONAR genera `ID_Seguimiento1`
    (ej. "a7341aaa") y deriva `tecnico`/`ESTADO` del relevamiento.
  - `{"ID_Seguimiento1":"...","Id_Relevamiento":"8584","Id_SISOC":"..."}` -> 200 con cuerpo
    vacio (rechazado).
- La **clave de la tabla es compuesta** (`ID_Seguimiento1` + `Id_Relevamiento`): el `Delete`
  con solo `ID_Seguimiento1` da `400 "Row key field 'Id_Relevamiento' value is missing"`.
- La tabla **no tiene** columna `Id_SISOC` (se ignoraba).

### Fixes
- `build_primer_seguimiento_payload`: el `Add` manda **solo** `{"Id_Relevamiento": "<id>"}`.
- `AsyncSendPrimerSeguimientoToGestionar.run`: persiste el `ID_Seguimiento1` que devuelve
  GESTIONAR en `gestionar_id` (ya lo hacia) y marca sincronizado al confirmar `Rows`.
- `AsyncRemovePrimerSeguimientoToGestionar`: el `Delete` manda la clave compuesta
  (`ID_Seguimiento1` + `Id_Relevamiento`); recibe `relevamiento_id` (lo pasa la signal
  `remove_primer_seguimiento_to_gestionar`).
- `PrimerSeguimientoService.create_asignado`: cuando crea un ancla nueva, envia el
  relevamiento a GESTIONAR de forma **sincronica y ordenada** (relevamiento antes que
  seguimiento) para que el `Id_Relevamiento` ya exista al dar de alta el seguimiento (el
  ancla se crea con `_skip_gestionar_sync=True` y el envio lo hace el service en orden).
