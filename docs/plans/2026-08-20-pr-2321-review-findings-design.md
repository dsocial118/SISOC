# PR #2321: corrección de hallazgos de revisión

## Objetivo

Resolver los tres hallazgos P2 de la revisión sin cambiar el contrato funcional
de rendiciones ni el alcance del PR #2321.

## Diseño aprobado

1. Cubrir la invalidación de caché del dashboard con una regresión que precargue
   valores obsoletos, ejecute la actualización y compruebe las métricas
   persistidas.
2. Cubrir el formulario de edición de rendición mediante un GET autenticado y
   autorizado que renderice el template específico y sus campos de datos.
3. Sustituir el modal de preferencias duplicado del listado por el componente
   estándar existente. Mantener la tabla actual y sus columnas configurables;
   no crear una abstracción nueva para las celdas personalizadas.

## Validación

Ejecutar los tests focalizados de dashboard y rendiciones, más `black`,
`djlint` y `git diff --check` sobre los archivos modificados.
