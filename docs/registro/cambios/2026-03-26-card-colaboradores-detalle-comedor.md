# Card y alta de colaboradores en detalle de comedor

## Qué cambió

- Se agregó una nueva card `Colaboradores del espacio` en el detalle clásico de comedor.
- La card se ubica entre `Convenios` y `Observaciones`.
- La card muestra solo el listado de colaboradores reales registrados para el comedor.
- Se agregó un botón `Agregar` en el header de la card para dar de alta colaboradores del espacio.
- En el listado del detalle de comedor se agregaron acciones `Editar` y `Eliminar`.
- En el detalle de ciudadano se agregó una card final para mostrar sus colaboraciones en comedores cuando existan.

## Alcance

- Se incorporó persistencia nueva para colaboradores del espacio con vínculo a `Ciudadano`.
- Cada colaborador puede tener múltiples actividades y un mismo ciudadano puede estar asociado a múltiples comedores.
- La acción `Eliminar` realiza baja lógica completando `fecha_baja`; no borra físicamente el registro para preservar historial.
- Un mismo ciudadano puede volver a ser dado de alta como colaborador del mismo comedor en diferentes fechas; cada alta queda como registro histórico independiente.
- Se agregó auditoría de movimientos de colaboradores con fecha, usuario, acción y snapshots antes/después para altas, ediciones y bajas.
- El alta sigue el flujo:
  - buscar por DNI en SISOC;
  - si no existe, consultar RENAPER;
  - crear ciudadano en SISOC con datos de RENAPER;
  - registrar la asignación del colaborador al comedor con género, teléfono, fechas y actividades.
- Se incorporó catálogo inicial de actividades:
  - Compras
  - Limpieza
  - Prep/Serv Alimentos
  - Cuidado Niños/Niñas/Adolesc
  - Tareas Administ./Rend.Cuentas
  - Mantenimiento
  - Responsable de la Org.Ejecutante
  - Responsable de la Org.Solicitante
- El resumen agregado de `relevamiento.colaboradores` no forma parte de esta card nueva.

## Validación

- `docker-compose exec django pytest comedores/tests.py`

## Notas de implementación

- Se aprovechó el flujo existente de consulta/creación de ciudadanos desde RENAPER en `ComedorService`.
- Se completó el mapeo de `cuil_cuit` al crear ciudadanos desde RENAPER porque era necesario para el alta de colaboradores.
