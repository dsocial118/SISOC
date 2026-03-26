# Fix Celiaquía: autocompletado de sexo en registros erróneos

## Fecha
2026-03-26

## Contexto
En el detalle de expediente de Celiaquía, cuando la importación de Excel fallaba por otra columna (por ejemplo `localidad`), el formulario de `RegistroErroneo` no preseleccionaba `sexo` si el valor original venía abreviado (`M` o `F`).

## Cambios aplicados
- Se ajustó el template de edición de registros erróneos para mapear abreviaturas `M/F` a opciones `Masculino/Femenino` tanto para beneficiario como para responsable.
- Se agregó test de regresión para validar que, ante error en otra columna, el formulario mantiene preseleccionados los campos `sexo` y `sexo_responsable` cuando llegan como `M/F`.

## Impacto
- Mejora de UX en corrección de registros erróneos: se preserva y muestra más información válida durante la subsanación.
- No modifica reglas de validación de negocio ni obligatoriedad de campos.
