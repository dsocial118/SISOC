# Asignación de territorial en relevamientos pendientes

Fecha: 2026-04-21

## Qué cambió

- Se agregó la acción `Asignar` en el detalle de relevamientos con estado `Pendiente`.
- La acción reutiliza el endpoint existente `relevamiento_create_edit_ajax` y el selector de territoriales ya usado en el alta.
- Al asignar un territorial válido, el relevamiento pasa a estado `Visita pendiente`.

## Ajustes técnicos

- `relevamientos/service.py` ahora exige un payload válido en `territorial_editar` antes de actualizar territorial y estado.
- `comedores/views/relevamientos.py` valida permiso `relevamientos.change_relevamiento` en la rama de edición de territorial y responde con `400`/`403` consistentes para AJAX y redirect con mensaje para submit normal.
- `relevamientos/templates/relevamiento_detail.html` incorpora el botón, modal y carga del JS de cache de territoriales solo cuando corresponde.

## Validación cubierta

- El detalle muestra `Asignar` solo para relevamientos `Pendiente`.
- El detalle no muestra la acción para `Visita pendiente` ni relevamientos finalizados.
- El endpoint rechaza payload vacío y usuarios sin permiso de edición.
