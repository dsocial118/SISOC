# INET: Buscador por Ciudadano

## Objetivo

Reemplazar la consulta SQL manual que se corría contra la base para responder
"¿en qué cursos INET se anotó esta persona?" por una pantalla del sistema, con
permisos, alcance territorial y trazabilidad. Ver especificación completa en
[docs/plans/2026-08-13-inet-buscador-por-ciudadano-issue.md](../../plans/2026-08-13-inet-buscador-por-ciudadano-issue.md).

## Cambios

- Nueva entrada en el menú INET, **Buscador por Ciudadano**
  (`vat/buscador-ciudadano/`), permiso `VAT.view_inscripcion` o
  `VAT.view_centro`, igual criterio que el reporte existente.
- Búsqueda por DNI (7-8 dígitos) o CUIT/CUIL (11 dígitos, con o sin
  puntos/guiones); si el número coincide con más de un `tipo_documento` se
  ofrece desambiguar.
- La pantalla muestra la ficha del ciudadano y su trayectoria de inscripciones
  INET: curso, comisión, centro (con CUE vigente), ubicación, período,
  **estado de inscripción** y **resultado final** en columnas separadas
  (`resultado_final` nulo se lee "Sin calificar"), y asistencia ("Sin
  registros" cuando no hay sesiones registradas, nunca `0%`).
- Resuelve las dos rutas de inscripción del modelo (`comision_curso` y
  `comision`), respeta el alcance territorial del usuario
  (`filter_centros_queryset_for_user`) y excluye bajas lógicas.
- Exportación CSV y XLSX de la trayectoria visible, respetando el mismo
  alcance que la pantalla.
- Es de solo lectura: no permite editar inscripciones desde esta vista.

## Refactor asociado

Se extrajo el queryset base que resuelve ambas rutas de inscripción
(`_base_queryset_for_user` de `reportes_inscripciones_asistencia.py`) a
`VAT/services/vat_inscripciones_base.py` como
`base_inscripciones_queryset_for_user`, compartido ahora por el reporte y el
buscador. Ver
[docs/registro/decisiones/2026-08-13-inet-buscador-base-inscripciones-compartida.md](../decisiones/2026-08-13-inet-buscador-base-inscripciones-compartida.md).

## Validación

- `VAT/test_buscador_ciudadano.py` (normalización, ambas rutas, soft-delete,
  CUE múltiple, alcance por referente/SSE, resumen, asistencia sin registros,
  export, permisos).
- `VAT/test_reporte_inscripciones_asistencia.py` sigue en verde tras el
  refactor del queryset compartido.
