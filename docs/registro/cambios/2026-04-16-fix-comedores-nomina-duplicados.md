# Fix comedores: deduplicación visible de nómina

**Fecha:** 2026-04-16

## Qué se ajustó

- Se endureció el armado de la nómina de comedores para mostrar una sola fila por ciudadano dentro de una misma admisión.
- La misma deduplicación se aplicó al detalle de nómina directa por comedor para mantener el mismo criterio funcional.
- El alta a nómina ahora vuelve a verificar la existencia del ciudadano dentro de una transacción con lock sobre `Ciudadano`, para reducir carreras que puedan dejar duplicados.
- Se agregó un test de regresión para la vista `/comedores/<pk>/admision/<pk>/nomina/` cubriendo el caso de filas repetidas para la misma persona.

## Decisión clave

La pantalla de nómina debe comportarse como una vista única por ciudadano dentro de la admisión activa. Si existen filas repetidas por datos legacy o por una carrera de alta, la vista prioriza el registro más reciente y no expone duplicados al operador.

## Validación esperada

- La cantidad total y la tabla visible deben contar una sola vez a cada ciudadano dentro de la admisión.
- Si dos altas intentan registrar al mismo ciudadano casi al mismo tiempo, la segunda debe volver a detectar que ya existe antes de crear una nueva fila.
