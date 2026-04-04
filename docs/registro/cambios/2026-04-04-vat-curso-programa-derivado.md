# VAT: programa derivado en cursos

## Qué cambió

- Se eliminó `programa` como campo persistido de `VAT.Curso`.
- El programa del curso ahora se deriva desde las `voucher_parametrias` asociadas.
- Los formularios de curso ya no editan programa y la API filtra cursos por programa a través de vouchers.

## Impacto

- Un curso sin vouchers queda sin programa derivado.
- Si un curso tuviera vouchers de más de un programa, el derivado devuelve `None`.
- La inscripción rápida de comisiones de curso mantiene la validación previa: exige que el curso resuelva un programa antes de inscribir.

## Ajustes posteriores

- Las vistas web de comisión de curso importan explícitamente `InstitucionUbicacion` para poblar el selector de ubicaciones sin errores en runtime.
- La resolución de programa derivado en `VAT.Curso` reutiliza relaciones prefetcheadas y cachea el resultado en la instancia para evitar consultas duplicadas.
- El filtro `programa_id` de la API de cursos ahora solo devuelve cursos cuyo programa derivado es consistente con un único programa de vouchers.