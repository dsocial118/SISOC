# VAT: programa derivado en cursos

## Qué cambió

- Se eliminó `programa` como campo persistido de `VAT.Curso`.
- El programa del curso ahora se deriva desde las `voucher_parametrias` asociadas.
- Los formularios de curso ya no editan programa y la API filtra cursos por programa a través de vouchers.

## Impacto

- Un curso sin vouchers queda sin programa derivado.
- Si un curso tuviera vouchers de más de un programa, el derivado devuelve `None`.
- La inscripción rápida de comisiones de curso mantiene la validación previa: exige que el curso resuelva un programa antes de inscribir.