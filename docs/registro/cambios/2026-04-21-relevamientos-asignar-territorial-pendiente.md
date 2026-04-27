# Asignacion de territorial en relevamientos pendientes

Fecha: 2026-04-21

## Que cambio

- Se agrego la accion `Asignar` en el detalle de relevamientos con estado `Pendiente`.
- La accion reutiliza el endpoint existente `relevamiento_create_edit_ajax` y el selector de territoriales ya usado en el alta.
- Al asignar un territorial valido, el relevamiento pasa a estado `Visita pendiente`.

## Ajustes tecnicos

- `relevamientos/service.py` exige un payload valido en `territorial_editar` antes de actualizar territorial y estado.
- `relevamientos/service.py` bloquea la asignacion cuando el relevamiento no esta en `Pendiente` y rechaza JSON validos con forma incorrecta.
- `comedores/views/relevamientos.py` valida permiso `relevamientos.change_relevamiento` en la rama de edicion de territorial y responde con `400`/`403` consistentes para AJAX y redirect con mensaje para submit normal.
- `relevamientos/templates/relevamiento_detail.html` incorpora el boton, modal y carga del JS de cache de territoriales solo cuando corresponde.
- Seguimiento 2026-04-22: se restauro el rechazo de `territorial_editar` vacio para no mutar ni persistir el relevamiento cuando el submit de edicion llega sin un territorial valido.

## Validacion cubierta

- El detalle muestra `Asignar` solo para relevamientos `Pendiente`.
- El detalle no muestra la accion para `Visita pendiente` ni relevamientos finalizados.
- El endpoint rechaza payload vacio y usuarios sin permiso de edicion.
- El endpoint rechaza asignaciones sobre relevamientos no pendientes y payloads JSON con forma invalida.
