# VAT - filtros en panel de cursos del centro

- Se agregaron filtros cliente en la tabla `Cursos configurados para este centro` para buscar por texto y filtrar por estado.
- Se agregaron filtros cliente en la tabla `Comisiones de Curso` para buscar por texto, filtrar por curso y filtrar por estado.
- Se mantuvo el comportamiento existente de seleccionar un curso para acotar visualmente sus comisiones, ahora conviviendo con los nuevos filtros.
- Se agregó verificación en tests para confirmar que el partial del panel renderiza los controles de filtros nuevos.