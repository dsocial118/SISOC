# VAT: código y nombre automáticos en comisión de curso

## Qué cambió

- Se eliminaron `Código de Comisión` y `Nombre` del formulario de comisión de curso.
- `ComisionCurso` ahora autogenera esos valores al guardar cuando no vienen informados.

## Criterio aplicado

- `codigo_comision` se genera con prefijo `COMCUR`, id de curso y timestamp.
- `nombre` se completa como `Comisión <nombre del curso>`.

## Impacto

- El usuario deja de cargar esos campos manualmente en el backoffice.
- Las vistas, detalles y referencias existentes siguen funcionando porque los campos se mantienen en modelo y base de datos.