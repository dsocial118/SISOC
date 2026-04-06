# VAT: ubicación de curso movida a comisión

## Qué cambió

- Se eliminó `ubicacion` como campo persistido de `VAT.Curso`.
- Se agregó `ubicacion` en `VAT.ComisionCurso`.
- La migración copia a cada comisión existente la ubicación que antes heredaba del curso.
- El formulario y los listados ahora editan y muestran la ubicación en la comisión, no en el curso.

## Impacto

- Un curso deja de tener una única ubicación global.
- Cada comisión puede registrar su propia ubicación dentro del centro.
- La validación mantiene el alcance actual: la ubicación elegida debe pertenecer al mismo centro del curso.

## Ajuste de migración

- La migración `VAT.0032_move_curso_ubicacion_to_comisioncurso` quedó tolerante a bases que ya tenían la columna `vat_comisioncurso.ubicacion_id` por corridas previas o estados intermedios.
- En ese escenario, Django actualiza el estado de migraciones sin volver a intentar crear la columna y conserva cualquier ubicación ya cargada en la comisión.