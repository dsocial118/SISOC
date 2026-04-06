# VAT: nombre obligatorio en alta de planes curriculares

Fecha: 2026-04-04

## Qué cambió

- Se agregó el campo `nombre` al modelo `PlanVersionCurricular` y al formulario web de alta y edición de planes curriculares.
- El valor ingresado pasa a persistirse directamente en el plan curricular.
- Se mantiene la sincronización automática del Título de Referencia asociado para compatibilidad con flujos existentes que todavía leen esa relación.
- La normativa libre dejó de editarse desde la UI; el formulario solo permite cargar tipo, número y año.
- Si el plan ya tiene normativa libre persistida en base, se muestra como dato informativo y se conserva al guardar.
- El detalle del plan ahora muestra explícitamente ese nombre en la sección de clasificación académica.

## Motivo

- La pantalla `/vat/catalogos/planes-curriculares/nuevo/` permitía crear planes sin un título asociado, aunque la documentación funcional del módulo describe al plan curricular como una versión de un título de referencia.
- El ajuste alinea la UI con ese flujo y evita dejar planes incompletos desde el catálogo.

## Alcance

- Con migración de base de datos para incorporar `PlanVersionCurricular.nombre` y poblarlo desde el primer título asociado cuando exista.
- Sin cambios en permisos.
- Se actualizaron tests de regresión del formulario y del alta web de planes curriculares.

## Compatibilidad

- El título de referencia sigue asociado al plan por `TituloReferencia.plan_estudio`.
- Al guardar desde el formulario, el nombre del plan sincroniza también `TituloReferencia.nombre` para no romper integraciones existentes.