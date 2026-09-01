# 2026-08-28 - Issue 1947: total de legajos en el detalle del expediente

## Contexto

- El detalle del expediente lista las personas asociadas con su ID, pero no
  informaba cuántas son en total.
- En expedientes con muchos legajos no se podía saber de un vistazo cuántos
  contiene, lo que dificultaba las tareas de control y de validación de
  completitud.

## Cambios aplicados

- `ExpedienteDetailView` expone `legajos_total`. El conteo se agrega al
  `aggregate` que ya calculaba los subtotales por estado (`c_aceptados`,
  `c_rech_tecnico`, etc.), así que **no agrega consultas** a la vista.
- `expediente_detail.html`: badge con el total junto al título "Legajos", con
  `title` explicativo al pasar el mouse.
- Se reutiliza el estilo del badge `ID #N` que ya existe en la misma pantalla,
  junto al título "Detalle del Expediente", en lugar de introducir uno propio.
  De paso mejora el contraste sobre el fondo oscuro de la sección.

## Impacto esperado

- El detalle muestra la cantidad total de personas asociadas al expediente.
- No cambia el modelo de datos, ni hay migraciones, ni se altera ningún flujo.
- El total refleja el universo vivo: los legajos dados de baja (borrado lógico)
  no suman, en línea con lo que muestra la tabla.

## Validación

- `pytest celiaquia/tests` en Docker: 186 aprobados (180 previos + 6 nuevos en
  `test_expediente_detail_total_legajos.py`).
- Se verificó explícitamente que **el contador no se desincroniza de la tabla**.
  La lista mostrada no es el queryset crudo: se arma un árbol responsable/hijo
  que reordena y deduplica por ciudadano. Un test construye un expediente con un
  responsable, dos hijos vinculados por `GrupoFamiliar` y un legajo suelto, y
  comprueba que `legajos_total` coincide con la cantidad y el contenido de
  `legajos_enriquecidos`.
- Casos cubiertos además: expediente sin legajos (muestra 0), legajo eliminado
  lógicamente (no suma), render del badge junto al título y uso del singular
  cuando hay un único legajo.
- `black --check`, `djlint --check` sobre el template modificado y `pylint` sobre
  los archivos Python tocados.

## Riesgos y rollback

- Riesgo mínimo: es un dato de solo lectura derivado de un `aggregate` existente.
- Rollback: revertir el commit. No hay migraciones ni datos que deshacer.
