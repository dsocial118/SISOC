# PR 1565: render del bloque de responsable

## Qué se corrigió

- Se ajustó el bloque de responsable en `expediente_detail` para exponer una etiqueta estable (`data-field-label`) con el texto `Apellido Responsable *` cuando el responsable es obligatorio.
- Se mantiene la lógica actual que solo marca esos campos como obligatorios cuando corresponde.

## Impacto

- El test de regresión que busca `Apellido Responsable *` en el detalle de expediente vuelve a reflejar el HTML real renderizado sin pelearse con `djlint`.
