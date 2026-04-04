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