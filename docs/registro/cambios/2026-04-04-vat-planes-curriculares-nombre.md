# VAT: nombre obligatorio en alta de planes curriculares

Fecha: 2026-04-04

## Qué cambió

- Se agregó el campo Nombre al formulario web de alta y edición de planes curriculares.
- El valor ingresado se usa para crear o actualizar automáticamente el Título de Referencia asociado al plan.
- El detalle del plan ahora muestra explícitamente ese nombre en la sección de clasificación académica.

## Motivo

- La pantalla `/vat/catalogos/planes-curriculares/nuevo/` permitía crear planes sin un título asociado, aunque la documentación funcional del módulo describe al plan curricular como una versión de un título de referencia.
- El ajuste alinea la UI con ese flujo y evita dejar planes incompletos desde el catálogo.

## Alcance

- Sin migraciones de base de datos.
- Sin cambios en permisos.
- Se actualizaron tests de regresión del formulario y del alta web de planes curriculares.

## Supuesto aplicado

- El campo solicitado como Nombre en la pantalla corresponde al nombre del título de referencia vinculado al plan curricular, no a un nuevo atributo persistido en `PlanVersionCurricular`.