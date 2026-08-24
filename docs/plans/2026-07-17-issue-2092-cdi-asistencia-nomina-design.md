# Issue #2092: asistencia CDI sobre nómina

## Diseño aprobado

La asistencia se registra por `(NominaCentroInfancia, fecha)`. Solo las
nóminas activas son elegibles para una carga nueva; una baja con asistencia en
la fecha consultada sigue visible y editable como historial.

No se migran ni eliminan las asistencias de trabajadores existentes. La ruta
operativa canónica es la de nómina y la ruta histórica redirige a ella.

El selector de fecha se implementa como calendario accesible propio con
indicadores mensuales obtenidos de un endpoint protegido por el mismo permiso
y scope territorial. Una fila desmarcada elimina la asistencia existente.

La implementación debe mantener validación de payload, transacción atómica,
unicidad por nómina y fecha, y pruebas de vista para las reglas anteriores.
